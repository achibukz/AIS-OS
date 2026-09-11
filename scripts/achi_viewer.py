#!/usr/bin/env python3
"""
achi-viewer - Universal Mobile & Desktop Markdown Web Viewer for achiOS.
Serves /home/achibukz with GitHub-style Markdown rendering, syntax highlighting,
mermaid diagrams, directory browsing, and dark mode over Tailscale.
"""

import os
import re
import sys
import html
import urllib.parse
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

ROOT_DIR = Path("/home/achibukz").resolve()
PORT = 8999
HOST = "0.0.0.0"

# Sensitive files/directories that should never be served
BLOCKED_PATTERNS = [
    ".env", ".key", ".pem", "id_rsa", "id_ed25519",
    ".git/objects", ".git/refs", ".token_storage", "secrets.env",
    # Identity and money documents. The viewer has no auth and binds every interface,
    # so these two folders are reachable by disk only. Telegram still delivers them:
    # MediaDispatcher uploads the file itself and never routes through this server.
    "Documents/Files/personal/legal",
    "Documents/Files/personal/finance",
]


def is_blocked(path) -> bool:
    return any(b in str(path) for b in BLOCKED_PATTERNS)


KNOWN_VAULTS = [
    "Documents/Obsidian/achiMem",
    "Documents/Obsidian/schoolMem",
]


def slugify_heading(text: str) -> str:
    """Slugify a markdown heading into a GitHub/Obsidian compatible anchor ID."""
    t = text.strip().lstrip("#").strip().lower()
    cleaned = []
    for ch in t:
        if ch.isalnum() or ch in ('-', '_'):
            cleaned.append(ch)
        elif ch.isspace():
            cleaned.append('-')
    slug = "".join(cleaned)
    while '--' in slug:
        slug = slug.replace('--', '-')
    return slug.strip('-')


def find_vault(file_path: Path, root_dir: Path = ROOT_DIR, vault_root: Path | None = None) -> Path | None:
    """
    Find the enclosing Obsidian vault for a given file.
    Checks explicit vault_root, known vaults, and directory markers (.obsidian, .git).
    Returns None if file is outside any vault.
    """
    if vault_root is not None:
        return vault_root.resolve()

    resolved_file = file_path.resolve()
    resolved_root = root_dir.resolve()

    # Check known vaults first
    for kv in KNOWN_VAULTS:
        kv_path = (resolved_root / kv).resolve()
        try:
            resolved_file.relative_to(kv_path)
            return kv_path
        except ValueError:
            pass

    # Traverse ancestors from parent upwards
    cur = resolved_file.parent
    while True:
        try:
            resolved_file.relative_to(resolved_root)
            cur.relative_to(resolved_root)
        except ValueError:
            pass

        # If .obsidian exists and this is not ROOT_DIR itself
        if (cur / ".obsidian").is_dir() and cur != resolved_root:
            return cur

        # If .git exists and this is not ROOT_DIR itself
        if (cur / ".git").is_dir() and cur != resolved_root:
            return cur

        if cur == cur.parent or cur == resolved_root:
            break
        cur = cur.parent

    return None


class VaultIndex:
    """Index of notes and assets within a single vault for fast, safe resolution."""

    def __init__(self, vault_root: Path):
        self.vault_root = vault_root.resolve()
        self.by_stem: dict[str, list[Path]] = {}
        self.by_rel_path: dict[str, Path] = {}
        self.by_name: dict[str, list[Path]] = {}
        self._build_index()

    def _build_index(self):
        for root, dirs, files in os.walk(self.vault_root):
            # Skip hidden directories like .git, .obsidian, .claude, etc.
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for f in files:
                if f.startswith("."):
                    continue
                file_path = Path(root) / f
                try:
                    resolved = file_path.resolve()
                except (OSError, RuntimeError):
                    continue

                # Security check: must not escape vault boundary (e.g. symlink to outside)
                try:
                    resolved.relative_to(self.vault_root)
                except ValueError:
                    continue

                # Security check: must not be a blocked resource
                if is_blocked(resolved):
                    continue

                if not resolved.is_file():
                    continue

                rel = file_path.relative_to(self.vault_root)
                rel_str = str(rel).replace("\\", "/")
                rel_lower = rel_str.lower()
                self.by_rel_path[rel_lower] = resolved
                if rel_lower.endswith(".md"):
                    self.by_rel_path[rel_lower[:-3]] = resolved
                elif rel_lower.endswith(".markdown"):
                    self.by_rel_path[rel_lower[:-9]] = resolved

                f_lower = file_path.name.lower()
                if f_lower not in self.by_name:
                    self.by_name[f_lower] = []
                if resolved not in self.by_name[f_lower]:
                    self.by_name[f_lower].append(resolved)

                stem_lower = file_path.stem.lower()
                if stem_lower not in self.by_stem:
                    self.by_stem[stem_lower] = []
                if resolved not in self.by_stem[stem_lower]:
                    self.by_stem[stem_lower].append(resolved)


FENCED_CODE_RE = re.compile(r'(```[\s\S]*?```|~~~[\s\S]*?~~~)')
INLINE_CODE_RE = re.compile(r'(`[^`\n]+`)')
WIKILINK_RE = re.compile(r'\[\[([^\]\|]+)(?:\|([^\]]+))?\]\]')


def mask_code_blocks(text: str) -> tuple[str, list[str]]:
    placeholders: list[str] = []

    def replace_code(m: re.Match) -> str:
        idx = len(placeholders)
        placeholders.append(m.group(0))
        return f"\x00CODE_{idx}\x00"

    masked = FENCED_CODE_RE.sub(replace_code, text)
    masked = INLINE_CODE_RE.sub(replace_code, masked)
    return masked, placeholders


def unmask_code_blocks(text: str, placeholders: list[str]) -> str:
    for idx, original in enumerate(placeholders):
        text = text.replace(f"\x00CODE_{idx}\x00", original)
    return text


def resolve_single_wikilink(
    raw_target: str,
    raw_alias: str | None,
    file_path: Path,
    vault_root: Path | None,
    root_dir: Path = ROOT_DIR,
    vault_index: VaultIndex | None = None,
) -> tuple[bool, str, str]:
    """
    Resolve a single wikilink target within the source vault.
    Returns (is_resolved, href, display_text).
    """
    note_part, has_heading, heading_part = raw_target.partition('#')
    note_part = note_part.strip()
    heading_part = heading_part.strip() if has_heading else ""

    display_text = raw_alias if raw_alias is not None else raw_target

    # Case 1: Same-file heading link: [[#Heading]] or [[#Heading|Label]]
    if not note_part and has_heading:
        anchor_slug = slugify_heading(heading_part)
        return True, f"#{anchor_slug}", display_text

    # Without vault_root or vault_index, cannot resolve vault links
    if not vault_root or not vault_index:
        return False, "", display_text

    decoded_note = urllib.parse.unquote(note_part).strip()
    if not decoded_note:
        return False, "", display_text

    target_file: Path | None = None

    # Path-specified note (contains / or \ or starts with .)
    if "/" in decoded_note or "\\" in decoded_note or decoded_note.startswith("."):
        norm_target = decoded_note.replace("\\", "/")

        if norm_target.startswith("./") or norm_target.startswith("../"):
            cand = (file_path.parent / norm_target).resolve()
            if not cand.is_file():
                cand_md = (file_path.parent / f"{norm_target}.md").resolve()
                if cand_md.is_file():
                    cand = cand_md

            try:
                cand.relative_to(vault_root.resolve())
                if not is_blocked(cand) and cand.is_file():
                    target_file = cand
            except (ValueError, OSError):
                return False, "", display_text
        else:
            # Vault-relative candidate
            cand_vault = (vault_root / norm_target).resolve()
            if not cand_vault.is_file():
                cand_vault_md = (vault_root / f"{norm_target}.md").resolve()
                if cand_vault_md.is_file():
                    cand_vault = cand_vault_md

            # Sibling / relative candidate
            cand_rel = (file_path.parent / norm_target).resolve()
            if not cand_rel.is_file():
                cand_rel_md = (file_path.parent / f"{norm_target}.md").resolve()
                if cand_rel_md.is_file():
                    cand_rel = cand_rel_md

            valid_cands = []
            for c in [cand_vault, cand_rel]:
                try:
                    c.relative_to(vault_root.resolve())
                    if not is_blocked(c) and c.is_file() and c not in valid_cands:
                        valid_cands.append(c)
                except (ValueError, OSError):
                    pass

            if len(valid_cands) == 1:
                target_file = valid_cands[0]
            elif len(valid_cands) > 1:
                return False, "", display_text
            else:
                return False, "", display_text
    else:
        # Bare basename
        clean_note = decoded_note
        if clean_note.lower().endswith(".md"):
            clean_note = clean_note[:-3]
        elif clean_note.lower().endswith(".markdown"):
            clean_note = clean_note[:-9]

        matches = vault_index.by_stem.get(clean_note.lower(), [])
        if not matches:
            matches = vault_index.by_name.get(decoded_note.lower(), [])
        if not matches:
            direct = vault_index.by_rel_path.get(decoded_note.lower())
            if direct:
                matches = [direct]

        if len(matches) == 0:
            return False, "", display_text
        elif len(matches) > 1:
            # Ambiguous: duplicate basenames!
            return False, "", display_text
        else:
            target_file = matches[0]

    if not target_file or not target_file.is_file():
        return False, "", display_text

    # Target is same file with heading anchor
    if target_file.resolve() == file_path.resolve() and has_heading:
        anchor_slug = slugify_heading(heading_part)
        return True, f"#{anchor_slug}", display_text

    # Compute href path
    try:
        rel_from_root = target_file.resolve().relative_to(root_dir.resolve())
        href_path = "/" + urllib.parse.quote(str(rel_from_root).replace("\\", "/"))
    except ValueError:
        try:
            rel_from_vault = target_file.resolve().relative_to(vault_root.resolve())
            href_path = "/" + urllib.parse.quote(str(rel_from_vault).replace("\\", "/"))
        except ValueError:
            return False, "", display_text

    if has_heading:
        anchor_slug = slugify_heading(heading_part)
        href_path = f"{href_path}#{anchor_slug}"

    return True, href_path, display_text


def resolve_wikilinks(content: str, file_path: Path, vault_root: Path | None = None, root_dir: Path = ROOT_DIR) -> str:
    """
    Parse content, resolve all Obsidian wikilinks against the vault, and replace with
    clickable <a> tags or unresolved <span> tags.
    """
    if vault_root is None:
        vault_root = find_vault(file_path, root_dir)

    vault_index = VaultIndex(vault_root) if vault_root else None
    masked_content, placeholders = mask_code_blocks(content)

    def replace_match(match: re.Match) -> str:
        raw_target = match.group(1).strip()
        raw_alias = match.group(2).strip() if match.group(2) is not None else None

        resolved, href, display_text = resolve_single_wikilink(
            raw_target=raw_target,
            raw_alias=raw_alias,
            file_path=file_path,
            vault_root=vault_root,
            root_dir=root_dir,
            vault_index=vault_index,
        )

        if resolved:
            return f'<a class="wiki-link" href="{html.escape(href, quote=True)}">{html.escape(display_text)}</a>'
        else:
            return f'<span class="wiki-link unresolved is-unresolved">[[{html.escape(display_text)}]]</span>'

    result = WIKILINK_RE.sub(replace_match, masked_content)
    return unmask_code_blocks(result, placeholders)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>{title} — achiOS Viewer</title>
  
  <!-- GitHub Markdown CSS -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.6.1/github-markdown-dark.min.css">
  <!-- Highlight.js for Code Highlighting -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
  <!-- Marked.js for fast client-side markdown -->
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <!-- Mermaid.js for diagrams -->
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>

  <style>
    :root {{
      --bg-color: #0d1117;
      --header-bg: #161b22;
      --border-color: #30363d;
      --text-color: #c9d1d9;
      --link-color: #58a6ff;
    }}
    body {{
      background-color: var(--bg-color);
      color: var(--text-color);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 0;
      -webkit-font-smoothing: antialiased;
    }}
    header {{
      position: relative;
      background: var(--header-bg);
      border-bottom: 1px solid var(--border-color);
      padding: 10px 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }}
    .breadcrumbs {{
      font-size: 13px;
      font-weight: 500;
      overflow-x: auto;
      white-space: nowrap;
      display: flex;
      gap: 6px;
      align-items: center;
    }}
    .breadcrumbs a {{
      color: var(--link-color);
      text-decoration: none;
    }}
    .breadcrumbs span {{
      color: #8b949e;
    }}
    .actions {{
      display: flex;
      gap: 8px;
      flex-shrink: 0;
    }}
    .btn {{
      background: #21262d;
      color: #c9d1d9;
      border: 1px solid var(--border-color);
      border-radius: 6px;
      padding: 5px 10px;
      font-size: 12px;
      cursor: pointer;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
    }}
    .btn:hover {{
      background: #30363d;
    }}
    .container {{
      max-width: 900px;
      margin: 0 auto;
      padding: 24px 16px 60px 16px;
    }}
    .markdown-body {{
      box-sizing: border-box;
      min-width: 200px;
      background-color: transparent !important;
      font-size: 15px;
      line-height: 1.6;
    }}
    .markdown-body pre {{
      background-color: #161b22 !important;
      border: 1px solid var(--border-color);
      border-radius: 8px;
    }}

    /* Wikilinks */
    a.wiki-link {{
      color: var(--link-color);
      text-decoration: underline;
      text-decoration-color: rgba(88, 166, 255, 0.4);
      font-weight: 500;
    }}
    a.wiki-link:hover {{
      text-decoration-color: var(--link-color);
    }}
    span.wiki-link.unresolved {{
      color: #8b949e;
      opacity: 0.7;
      border-bottom: 1px dashed #8b949e;
      cursor: not-allowed;
    }}
    
    /* Mermaid Card & Viewport */
    .mermaid-card {{
      position: relative;
      background: #161b22;
      border: 1px solid var(--border-color);
      border-radius: 8px;
      margin: 24px 0;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }}
    .mermaid-toolbar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
      background: #1c2128;
      border-bottom: 1px solid var(--border-color);
      font-size: 12px;
      color: #8b949e;
      user-select: none;
      -webkit-user-select: none;
      z-index: 10;
    }}
    .mermaid-title {{
      font-weight: 600;
      color: #c9d1d9;
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .mermaid-actions {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .zoom-level {{
      font-family: monospace;
      font-size: 11px;
      color: #8b949e;
      min-width: 42px;
      text-align: right;
      margin-right: 4px;
    }}
    .zoom-btn {{
      background: #21262d;
      color: #c9d1d9;
      border: 1px solid var(--border-color);
      border-radius: 6px;
      padding: 4px 10px;
      font-size: 12px;
      font-weight: 500;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      transition: all 0.15s ease;
      user-select: none;
      -webkit-user-select: none;
      touch-action: manipulation;
    }}
    .zoom-btn:hover {{
      background: #30363d;
      color: #ffffff;
      border-color: #8b949e;
    }}
    .zoom-btn:active {{
      transform: scale(0.96);
    }}
    .mermaid-viewport {{
      position: relative;
      width: 100%;
      min-height: 380px;
      max-height: 600px;
      overflow: hidden;
      background: #0d1117;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: grab;
      touch-action: none;
      user-select: none;
      -webkit-user-select: none;
    }}
    .mermaid-viewport:active, .mermaid-viewport.dragging {{
      cursor: grabbing;
    }}
    .mermaid-content {{
      display: flex;
      align-items: center;
      justify-content: center;
      transform-origin: center center;
      will-change: transform;
      pointer-events: auto;
    }}
    .mermaid-content .mermaid {{
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0;
      padding: 24px;
      background: transparent !important;
      border: none !important;
    }}
    .mermaid-content svg {{
      max-width: none !important;
      height: auto !important;
      display: block;
    }}

    /* Seamless In-Place Fullscreen Mode */
    .mermaid-card.fullscreen-mode {{
      position: fixed !important;
      top: 0 !important;
      left: 0 !important;
      right: 0 !important;
      bottom: 0 !important;
      width: 100vw !important;
      height: 100vh !important;
      max-width: none !important;
      max-height: none !important;
      margin: 0 !important;
      border-radius: 0 !important;
      border: none !important;
      z-index: 999999 !important;
      background: #0d1117 !important;
    }}
    .mermaid-card.fullscreen-mode .mermaid-toolbar {{
      padding: 12px 18px;
      background: #161b22;
      border-bottom: 1px solid var(--border-color);
    }}
    .mermaid-card.fullscreen-mode .mermaid-viewport {{
      flex: 1 !important;
      height: 100% !important;
      max-height: none !important;
      min-height: 0 !important;
    }}
    .mermaid-card.fullscreen-mode .fs-btn {{
      background: #b62324 !important;
      color: #fff !important;
      border-color: #b62324 !important;
    }}

    .dir-list {{
      list-style: none;
      padding: 0;
      margin: 0;
      border: 1px solid var(--border-color);
      border-radius: 8px;
      background: var(--header-bg);
      overflow: hidden;
    }}
    .dir-item {{
      border-bottom: 1px solid var(--border-color);
    }}
    .dir-item:last-child {{
      border-bottom: none;
    }}
    .dir-item a {{
      display: flex;
      align-items: center;
      padding: 12px 16px;
      color: var(--text-color);
      text-decoration: none;
      font-size: 14px;
    }}
    .dir-item a:hover {{
      background: #1f242c;
    }}
    .icon {{
      margin-right: 12px;
      font-size: 16px;
    }}
    .badge {{
      margin-left: auto;
      font-size: 11px;
      color: #8b949e;
    }}
  </style>
</head>
<body>
  <header>
    <div class="breadcrumbs">
      {breadcrumbs}
    </div>
    <div class="actions">
      {action_buttons}
    </div>
  </header>

  <main class="container">
    {content}
  </main>

  <script>
    mermaid.initialize({{
      startOnLoad: false,
      theme: 'dark',
      securityLevel: 'loose',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    }});

    const diagramStates = {{}};

    function getCardState(cardId) {{
      if (!diagramStates[cardId]) {{
        diagramStates[cardId] = {{
          scale: 1.0,
          x: 0,
          y: 0,
          pointers: new Map(),
          prevDiff: -1,
          isDragging: false,
          startX: 0,
          startY: 0
        }};
      }}
      return diagramStates[cardId];
    }}

    function updateTransform(cardId, animate) {{
      const state = getCardState(cardId);
      const card = document.getElementById(cardId);
      if (!card) return;
      const content = card.querySelector('.mermaid-content');
      const zoomLvl = card.querySelector('.zoom-level');
      if (content) {{
        content.style.transition = animate ? 'transform 0.18s ease-out' : 'none';
        content.style.transform = `translate3d(${{state.x}}px, ${{state.y}}px, 0) scale(${{state.scale}})`;
      }}
      if (zoomLvl) {{
        zoomLvl.textContent = `${{Math.round(state.scale * 100)}}%`;
      }}
    }}

    function handleZoom(cardId, factor) {{
      const state = getCardState(cardId);
      const newScale = Math.min(8.0, Math.max(0.2, state.scale * factor));
      state.scale = Number(newScale.toFixed(3));
      updateTransform(cardId, true);
    }}

    function handleReset(cardId) {{
      const state = getCardState(cardId);
      state.scale = 1.0;
      state.x = 0;
      state.y = 0;
      updateTransform(cardId, true);
    }}

    function toggleFullscreen(cardId) {{
      const card = document.getElementById(cardId);
      if (!card) return;
      const isFs = card.classList.toggle('fullscreen-mode');
      const fsBtn = card.querySelector('.fs-btn');
      if (fsBtn) {{
        fsBtn.innerHTML = isFs ? '✕ Exit' : '⛶ Fullscreen';
      }}
      updateTransform(cardId, true);
    }}

    window.addEventListener('keydown', (e) => {{
      if (e.key === 'Escape') {{
        document.querySelectorAll('.mermaid-card.fullscreen-mode').forEach(card => {{
          toggleFullscreen(card.id);
        }});
      }}
    }});

    function initDiagramInteractions(card) {{
      const cardId = card.id;
      const viewport = card.querySelector('.mermaid-viewport');
      if (!viewport) return;
      const state = getCardState(cardId);

      // Apply initial 100% scale
      updateTransform(cardId, false);

      viewport.addEventListener('pointerdown', (e) => {{
        if (e.button !== 0 && e.pointerType === 'mouse') return;
        viewport.setPointerCapture(e.pointerId);
        state.pointers.set(e.pointerId, {{ x: e.clientX, y: e.clientY }});

        if (state.pointers.size === 1) {{
          state.isDragging = true;
          state.startX = e.clientX - state.x;
          state.startY = e.clientY - state.y;
          viewport.classList.add('dragging');
        }} else if (state.pointers.size === 2) {{
          state.isDragging = false;
          const pts = Array.from(state.pointers.values());
          state.prevDiff = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y);
        }}
      }});

      viewport.addEventListener('pointermove', (e) => {{
        if (!state.pointers.has(e.pointerId)) return;
        state.pointers.set(e.pointerId, {{ x: e.clientX, y: e.clientY }});

        if (state.pointers.size === 1 && state.isDragging) {{
          state.x = e.clientX - state.startX;
          state.y = e.clientY - state.startY;
          updateTransform(cardId, false);
        }} else if (state.pointers.size === 2) {{
          const pts = Array.from(state.pointers.values());
          const curDiff = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y);
          if (state.prevDiff > 0) {{
            const factor = curDiff / state.prevDiff;
            state.scale = Math.min(8.0, Math.max(0.2, state.scale * factor));
            updateTransform(cardId, false);
          }}
          state.prevDiff = curDiff;
        }}
      }});

      function onPointerEnd(e) {{
        state.pointers.delete(e.pointerId);
        try {{
          viewport.releasePointerCapture(e.pointerId);
        }} catch (err) {{}}

        if (state.pointers.size === 0) {{
          state.isDragging = false;
          state.prevDiff = -1;
          viewport.classList.remove('dragging');
        }} else if (state.pointers.size === 1) {{
          state.isDragging = true;
          const pt = Array.from(state.pointers.values())[0];
          state.startX = pt.x - state.x;
          state.startY = pt.y - state.y;
        }}
      }}

      viewport.addEventListener('pointerup', onPointerEnd);
      viewport.addEventListener('pointercancel', onPointerEnd);

      viewport.addEventListener('wheel', (e) => {{
        e.preventDefault();
        const factor = e.deltaY < 0 ? 1.15 : 0.85;
        handleZoom(cardId, factor);
      }}, {{ passive: false }});

      viewport.addEventListener('dblclick', (e) => {{
        handleReset(cardId);
      }});
    }}

    // Render client-side Markdown if content is present
    const rawContentEl = document.getElementById('raw-markdown-content');
    const resolvedContentEl = document.getElementById('resolved-markdown-content');
    const sourceEl = resolvedContentEl || rawContentEl;
    if (sourceEl) {{
      let text = sourceEl.textContent;

      function slugify(t) {{
        return t.toLowerCase().trim()
          .replace(/[^\\p{{L}}\\p{{N}}\\s\\-_]/gu, '')
          .replace(/\\s+/g, '-')
          .replace(/-+/g, '-')
          .replace(/^-+|-+$/g, '');
      }}

      let diagCount = 0;
      const renderer = {{
        heading(token) {{
          const text = typeof token === 'object' ? token.text : token;
          const depth = typeof token === 'object' ? token.depth : arguments[1];
          const slug = slugify(text);
          return `<h${{depth}} id="${{slug}}">${{text}}</h${{depth}}>\n`;
        }},
        code(token) {{
          const code = typeof token === 'object' ? token.text : token;
          const lang = (typeof token === 'object' ? token.lang : arguments[1]) || '';
          
          if (lang === 'mermaid') {{
            diagCount++;
            const id = 'mermaid-card-' + diagCount;
            return `
              <div class="mermaid-card" id="${{id}}">
                <div class="mermaid-toolbar">
                  <span class="mermaid-title">📊 Flowchart</span>
                  <div class="mermaid-actions">
                    <span class="zoom-level">100%</span>
                    <button class="zoom-btn" onclick="handleZoom('${{id}}', 1.25)" title="Zoom In">➕ In</button>
                    <button class="zoom-btn" onclick="handleZoom('${{id}}', 0.8)" title="Zoom Out">➖ Out</button>
                    <button class="zoom-btn" onclick="handleReset('${{id}}')" title="Reset View">🔄 Reset</button>
                    <button class="zoom-btn fs-btn" onclick="toggleFullscreen('${{id}}')" title="Toggle Fullscreen">⛶ Fullscreen</button>
                  </div>
                </div>
                <div class="mermaid-viewport" id="vp-${{id}}">
                  <div class="mermaid-content">
                    <div class="mermaid">${{code}}</div>
                  </div>
                </div>
              </div>
            `;
          }}
          
          const validLang = (typeof hljs !== 'undefined' && hljs.getLanguage(lang)) ? lang : 'plaintext';
          if (typeof hljs !== 'undefined') {{
            try {{
              const highlighted = hljs.highlight(code, {{ language: validLang }}).value;
              return `<pre><code class="hljs language-${{validLang}}">${{highlighted}}</code></pre>`;
            }} catch (e) {{
              // fallback
            }}
          }}
          return `<pre><code class="language-${{lang}}">${{code}}</code></pre>`;
        }}
      }};

      marked.use({{ renderer, gfm: true, breaks: true }});

      const outputEl = document.getElementById('rendered-content');
      outputEl.innerHTML = marked.parse(text);

      if (window.mermaid) {{
        mermaid.run({{
          nodes: document.querySelectorAll('.mermaid')
        }}).then(() => {{
          document.querySelectorAll('.mermaid-card').forEach(card => {{
            const svg = card.querySelector('.mermaid-viewport svg');
            if (svg) {{
              let nativeWidth = 0;
              if (svg.viewBox && svg.viewBox.baseVal && svg.viewBox.baseVal.width > 0) {{
                nativeWidth = svg.viewBox.baseVal.width;
              }} else {{
                const vb = svg.getAttribute('viewBox');
                if (vb) {{
                  const parts = vb.trim().split(/[\\s,]+/);
                  if (parts.length === 4) nativeWidth = parseFloat(parts[2]);
                }}
              }}
              if (nativeWidth > 0) {{
                svg.style.width = nativeWidth + 'px';
                svg.style.minWidth = nativeWidth + 'px';
                svg.style.maxWidth = 'none';
              }}
            }}
            initDiagramInteractions(card);
          }});
        }}).catch(err => console.warn('Mermaid rendering issue:', err));
      }}
    }}

    function copyMarkdown() {{
      if (rawContentEl) {{
        navigator.clipboard.writeText(rawContentEl.textContent);
        const btn = document.getElementById('copy-btn');
        const orig = btn.innerText;
        btn.innerText = 'Copied!';
        setTimeout(() => btn.innerText = orig, 1500);
      }}
    }}
  </script>
</body>
</html>
"""


class AchiViewerHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        raw_path = urllib.parse.unquote(parsed.path).lstrip("/")
        
        # Security check: Prevent path traversal
        target_path = (ROOT_DIR / raw_path).resolve()
        try:
            target_path.relative_to(ROOT_DIR)
        except ValueError:
            self.send_error(403, "Access Denied")
            return

        # Security check: Block sensitive patterns
        if is_blocked(target_path):
            self.send_error(403, "Access Denied to Protected Resource")
            return

        if not target_path.exists() and raw_path:
            # Smart Short-Path Fallbacks
            fallbacks = [
                ROOT_DIR / "Documents/Obsidian/achiMem" / raw_path,
                ROOT_DIR / "Documents/Obsidian/schoolMem" / raw_path,
                ROOT_DIR / "Code/GitHub/AIS-OS" / raw_path,
                ROOT_DIR / "Documents/Obsidian" / raw_path,
                ROOT_DIR / "Code/GitHub" / raw_path,
            ]
            for fb in fallbacks:
                if fb.exists():
                    target_path = fb.resolve()
                    break

            # If still not found and it's a single slug/filename, search across achiMem, schoolMem, and AIS-OS
            if not target_path.exists() and "/" not in raw_path:
                clean_slug = raw_path.removesuffix(".md").lower()
                
                # Priority 1: Search .md files in wiki/
                matches = list((ROOT_DIR / "Documents/Obsidian/achiMem/wiki").rglob(f"*{clean_slug}*.md"))
                if not matches:
                    matches = list((ROOT_DIR / "Documents/Obsidian/achiMem").rglob(f"*{clean_slug}*.md"))
                if not matches:
                    matches = list((ROOT_DIR / "Code/GitHub/AIS-OS").rglob(f"*{clean_slug}*.md"))
                if not matches:
                    matches = list((ROOT_DIR / "Documents/Obsidian/schoolMem/wiki").rglob(f"*{clean_slug}*.md"))
                if not matches:
                    # Priority 2: Search any matching file
                    matches = list((ROOT_DIR / "Documents/Obsidian/achiMem").rglob(f"*{clean_slug}*"))

                if matches:
                    target_path = matches[0].resolve()

        # Re-check after the fallbacks: they reassign target_path, so the block list
        # above only ever saw the literal request path.
        if is_blocked(target_path):
            self.send_error(403, "Access Denied to Protected Resource")
            return

        if not target_path.exists():
            self.render_not_found(raw_path)
            return

        if target_path.is_dir():
            self.render_directory(target_path)
        elif target_path.suffix.lower() in [".md", ".markdown", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".py", ".sh", ".conf", ".env-example"]:
            self.render_file(target_path)
        else:
            # Serve binary / image / other files directly
            self.serve_raw_file(target_path)

    def get_breadcrumbs(self, target_path: Path):
        rel = target_path.relative_to(ROOT_DIR)
        parts = rel.parts
        crumbs = ['<a href="/">🏠 ~</a>']
        cur = ""
        for p in parts:
            cur += f"/{p}"
            crumbs.append(f'<span>/</span><a href="{cur}">{html.escape(p)}</a>')
        return "".join(crumbs)

    def render_file(self, file_path: Path):
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            self.send_error(500, f"Error reading file: {e}")
            return

        rel_path = file_path.relative_to(ROOT_DIR)
        breadcrumbs = self.get_breadcrumbs(file_path)
        
        actions = f'''
          <button id="copy-btn" class="btn" onclick="copyMarkdown()">📋 Copy</button>
          <a href="{self.path}?raw=true" class="btn" target="_blank">📄 Raw</a>
        '''

        # Check if raw mode requested
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if "raw" in query and query["raw"][0] == "true":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
            return

        vault_root = find_vault(file_path, ROOT_DIR)
        resolved_content = resolve_wikilinks(content, file_path, vault_root=vault_root, root_dir=ROOT_DIR)

        body_html = f'''
          <div id="raw-markdown-content" style="display:none;">{html.escape(content)}</div>
          <div id="resolved-markdown-content" style="display:none;">{html.escape(resolved_content)}</div>
          <div id="rendered-content" class="markdown-body">Loading...</div>
        '''

        full_html = HTML_TEMPLATE.format(
            title=file_path.name,
            breadcrumbs=breadcrumbs,
            action_buttons=actions,
            content=body_html
        )
        data = full_html.encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def render_directory(self, dir_path: Path):
        breadcrumbs = self.get_breadcrumbs(dir_path)
        actions = '<span style="font-size:12px; color:#8b949e;">achiOS Viewer</span>'

        items = []
        try:
            entries = sorted(list(dir_path.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
            for e in entries:
                if e.name.startswith(".") and e.name not in [".obsidian", ".claude"]:
                    continue
                # Skip blocked
                if is_blocked(e):
                    continue
                
                rel = "/" + str(e.relative_to(ROOT_DIR))
                if e.is_dir():
                    icon = "📁"
                    badge = f"{len(list(e.iterdir()))} items" if os.access(e, os.R_OK) else ""
                elif e.suffix.lower() in [".md", ".markdown"]:
                    icon = "📝"
                    badge = f"{e.stat().st_size // 1024} KB"
                elif e.suffix.lower() in [".png", ".jpg", ".jpeg", ".svg"]:
                    icon = "🖼️"
                    badge = "image"
                else:
                    icon = "📄"
                    badge = f"{e.stat().st_size // 1024} KB"

                items.append(f'''
                  <li class="dir-item">
                    <a href="{rel}">
                      <span class="icon">{icon}</span>
                      <span>{html.escape(e.name)}</span>
                      <span class="badge">{badge}</span>
                    </a>
                  </li>
                ''')
        except Exception as err:
            items.append(f'<li class="dir-item"><span style="padding:16px;">Error reading directory: {html.escape(str(err))}</span></li>')

        body_html = f'<ul class="dir-list">{"".join(items)}</ul>'

        full_html = HTML_TEMPLATE.format(
            title=dir_path.name or "Home",
            breadcrumbs=breadcrumbs,
            action_buttons=actions,
            content=body_html
        )
        data = full_html.encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def render_not_found(self, raw_path: str):
        body_html = f'''
          <div class="markdown-body">
            <h2>404 — File Not Found</h2>
            <p>Could not locate <code>{html.escape(raw_path)}</code> on Achibuntu.</p>
            <p><a href="/" style="color:var(--link-color);">Return to Home Directory</a></p>
          </div>
        '''
        full_html = HTML_TEMPLATE.format(
            title="404 Not Found",
            breadcrumbs='<a href="/">🏠 Home</a>',
            action_buttons='',
            content=body_html
        )
        data = full_html.encode("utf-8")
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def serve_raw_file(self, file_path: Path):
        try:
            data = file_path.read_bytes()
            ext = file_path.suffix.lower()
            content_type = "application/octet-stream"
            if ext in [".png"]: content_type = "image/png"
            elif ext in [".jpg", ".jpeg"]: content_type = "image/jpeg"
            elif ext in [".svg"]: content_type = "image/svg+xml"
            elif ext in [".pdf"]: content_type = "application/pdf"
            
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            self.send_error(500, f"Error serving binary file: {e}")


def run_server():
    server_address = (HOST, PORT)
    httpd = ThreadingHTTPServer(server_address, AchiViewerHandler)
    print(f"✅ achi-viewer is live on http://{HOST}:{PORT} (serving {ROOT_DIR})")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping achi-viewer...")
        httpd.server_close()


if __name__ == "__main__":
    run_server()

