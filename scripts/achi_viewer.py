#!/usr/bin/env python3
"""
achi-viewer - Universal Mobile & Desktop Markdown Web Viewer for achiOS.
Serves /home/achibukz with GitHub-style Markdown rendering, syntax highlighting,
mermaid diagrams, directory browsing, and dark mode over Tailscale.
"""

import os
import sys
import html
import urllib.parse
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

ROOT_DIR = Path("/home/achibukz").resolve()
PORT = 8999
HOST = "0.0.0.0"

# Sensitive files/directories that should never be served
BLOCKED_PATTERNS = [
    ".env", ".key", ".pem", "id_rsa", "id_ed25519",
    ".git/objects", ".git/refs", ".token_storage", "secrets.env"
]

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
    mermaid.initialize({{ startOnLoad: false, theme: 'dark' }});

    // Render client-side Markdown if raw content is present
    const rawContentEl = document.getElementById('raw-markdown-content');
    if (rawContentEl) {{
      let text = rawContentEl.textContent;
      
      // Auto-convert [[wikilinks]] to clickable links
      text = text.replace(/\\[\\[([a-zA-Z0-9_\\-\\.\\s\\/]+)(?:\\|([^\\]]+))?\\]\\]/g, function(match, target, alias) {{
        let linkText = alias || target;
        let cleanTarget = target.trim();
        return `<span class="wiki-link">[[${{linkText}}]]</span>`;
      }});

      marked.setOptions({{
        highlight: function(code, lang) {{
          if (lang === 'mermaid') {{
            return `<div class="mermaid">${{code}}</div>`;
          }}
          const language = highlight.getLanguage(lang) ? lang : 'plaintext';
          return highlight.highlight(code, {{ language }}).value;
        }},
        gfm: true,
        breaks: true
      }});

      const outputEl = document.getElementById('rendered-content');
      outputEl.innerHTML = marked.parse(text);
      mermaid.run();
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
        for blocked in BLOCKED_PATTERNS:
            if blocked in str(target_path):
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

        body_html = f'''
          <div id="raw-markdown-content" style="display:none;">{html.escape(content)}</div>
          <div id="rendered-content" class="markdown-body">Loading...</div>
        '''

        full_html = HTML_TEMPLATE.format(
            title=file_path.name,
            breadcrumbs=breadcrumbs,
            action_buttons=actions,
            content=body_html
        )

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(full_html.encode("utf-8"))

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
                if any(b in str(e) for b in BLOCKED_PATTERNS):
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

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(full_html.encode("utf-8"))

    def render_not_found(self, raw_path: str):
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
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
        self.wfile.write(full_html.encode("utf-8"))

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
        except Exception as e:
            self.send_error(500, f"Error serving binary file: {e}")


def run_server():
    server_address = (HOST, PORT)
    httpd = HTTPServer(server_address, AchiViewerHandler)
    print(f"✅ achi-viewer is live on http://{HOST}:{PORT} (serving {ROOT_DIR})")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping achi-viewer...")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
