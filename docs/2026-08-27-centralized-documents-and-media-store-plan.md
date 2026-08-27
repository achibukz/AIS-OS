# Centralized Documents & Media Store Architecture Plan

**Date:** 2026-08-27  
**Status:** Approved & Ready for Claude Code Execution  
**Target:** Achibuntu & AchiBook Air (macOS)  
**Primary Implementer:** Claude Code  

---

## 1. Overview & Motivation

Currently, binary non-markdown assets (photos, prescriptions, official PDFs, certificates, scans, spreadsheets) have been deposited into `raw/` folders inside Obsidian text vaults (`achiMem/raw/` and `schoolMem/raw/`). 

### Core Problems Solved
1. **Git Repository Bloat:** Committing high-resolution images, multi-page PDFs, and binary assets into Git-backed Obsidian vaults bloats `.git` repository size and causes slow fetches/pushes.
2. **Vault Coupling:** Documents related to career, identity, taxes, and health should be accessible globally across projects, daemons, and scripts without depending on Obsidian vault structure.
3. **Synchronization Efficiency:** Isolating binary files into a dedicated Syncthing queue prevents large file syncs from locking or stalling real-time Obsidian markdown sync.

---

## 2. Directory Hierarchy & Taxonomy

The centralized store lives at `~/Documents/Files/` on both Achibuntu and macOS.

```text
~/Documents/Files/
├── personal/
│   ├── health/          # Prescriptions, doctor notes, lab results, vaccination cards
│   ├── finance/         # Official bank statements, tax documents, payment receipts
│   └── legal/           # Birth certificate, government IDs, passport copies, notarized forms
├── academic/
│   ├── csopesy/         # Operating Systems reference PDFs, lecture decks, assignments
│   ├── ths-st1/         # Thesis 1 reference papers, proposal forms, ethical reviews
│   ├── stcloud/         # Cloud Computing lab docs, architecture diagrams
│   └── general/         # DLSU CGMC good moral certificates, enrollment proofs, transcripts
└── career/
    ├── ing/             # Internship offer letter, privacy notices, intern info sheet, notarized agreement
    ├── gcash/           # Hackathon deliverables, submission proofs, certificates
    └── certifications/  # Professional certificates, workshop completions, badges
```

### File Naming Standard
All files follow the **ISO Date Prefix + Kebab-Case** convention:
```
YYYY-MM-DD-descriptor.extension
```
*Examples:*
- `2021-07-07-dr-arthur-roman-prescription.jpg`
- `2026-08-20-ing-internship-offer-letter.pdf`
- `2026-08-25-dlsu-good-moral-certificate.pdf`
- `2026-08-22-psa-birth-certificate.pdf`

---

## 3. Syncthing Configuration & Topology

### Topology
- **Device A:** `achibuntu` (`2J222T5-74IFO56-L4J4F4W-3QESBNW-ZGOYCTE-HPWIBSJ-2YZ3Y4T-VEZH5A5`)
- **Device B:** `AchiBook Air` (`5DV6UYD-6ZSVEKB-UWFLIHM-A2Z3CLL-A5ACENI-AJVCQWO-MK5IKTL-6ECUAA6`)

### Syncthing Folder Specification
- **Folder ID:** `achi-files`
- **Folder Label:** `Documents Files`
- **Achibuntu Path:** `/home/achibukz/Documents/Files`
- **macOS Path:** `/Users/achibukz/Documents/Files`
- **Folder Type:** `sendreceive`
- **File System Watcher:** Enabled (`fsWatcherEnabled: true`, `fsWatcherDelayS: 10`)
- **Rescan Interval:** `3600` seconds
- **Version Control:** Simple File Versioning (clean up after 30 days)

### Git Policy
`~/Documents/Files/` is **strictly Syncthing-managed with no `.git` repository**.

---

## 4. Vault Linking & Referencing Contract

Markdown notes in `achiMem` and `schoolMem` reference files using two complementary mechanisms:

1. **Tailscale Web Viewer Links (for rendering / human clicking):**
   Points directly to the port 8999 server:
   ```markdown
   [Prescription Image](http://100.106.210.38:8999/Documents/Files/personal/health/2021-07-07-dr-arthur-roman-prescription.jpg)
   ```
2. **Absolute / Normalized Filesystem Paths (for AI agents & CLI tools):**
   ```markdown
   - Raw File: `~/Documents/Files/personal/health/2021-07-07-dr-arthur-roman-prescription.jpg`
   ```
3. **No Vault Symlinks:**
   Obsidian vaults will not contain symlinks to avoid cross-platform mobile syncing loops.

---

## 5. Media Dispatcher & Telegram Integration

`achiAgy`'s `MediaDispatcher` (`src/media_dispatcher.py`) supports `Documents/Files/...` paths:
- When an agent outputs `![Caption](/home/achibukz/Documents/Files/personal/health/2021-07-07-dr-arthur-roman-prescription.jpg)`, the daemon:
  1. Identifies the media file on disk.
  2. Dispatches photos via `send_photo` and documents/PDFs via `send_document`.
  3. Rewrites the markdown in the Telegram message to clickable Tailscale viewer links (`http://100.106.210.38:8999/Documents/Files/...`).

---

## 6. Implementation Checklist for Claude Code

- [ ] **Step 1: Scaffold Directory Structure on Achibuntu**
  - Create `~/Documents/Files/{personal/{health,finance,legal},academic/{csopesy,ths-st1,stcloud,general},career/{ing,gcash,certifications}}`.
- [ ] **Step 2: Configure Syncthing**
  - Add `achi-files` folder to `~/.local/state/syncthing/config.xml` on Achibuntu sharing with `AchiBook Air`.
  - Restart syncthing service (`systemctl --user restart syncthing`).
  - Accept and map `achi-files` folder on `AchiBook Air` to `~/Documents/Files`.
- [ ] **Step 3: Migrate Existing Assets**
  - Move `achiMem/raw/prescriptions/2021-07-07-dr-arthur-roman-prescription.jpg` to `~/Documents/Files/personal/health/2021-07-07-dr-arthur-roman-prescription.jpg`.
  - Check `schoolMem/raw/` and migrate any existing documents.
- [ ] **Step 4: Update Vault Notes & Indexes**
  - Update `achiMem/wiki/personal/health/prescriptions.md` with new path and Tailscale URL.
  - Run `scripts/build_index.py` in `achiMem` to rebuild wiki index.
- [ ] **Step 5: Purge `raw/` and Update `.gitignore`**
  - Remove `raw/` from Git index in `achiMem` and `schoolMem`.
  - Add `raw/` to `.gitignore` in both vaults.
  - Commit and push `achiMem` and `schoolMem` to remote origins.
- [ ] **Step 6: Update Documentation & Decision Records**
  - Record completed architecture in `decisions/log.md` and `session-log.md`.
  - Mark task complete in `tasks.md`.
