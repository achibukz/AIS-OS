# Google Sheets Schedule Planner Skill Specification

**Document Version:** 1.0.0  
**Date:** 2026-08-24  
**Author:** Agi (achiOS Core / Antigravity pair)  
**Target Runner:** Claude Code & achiOS Agentic Toolchain  
**Related Sheet:** [DLSU AY 2026-2027 Term 1 Schedule Planner](https://docs.google.com/spreadsheets/d/1qqaTvcyz40JvyTDyT8MXiOEjPVh57PAL96jb_967BJ4)

---

## 1. Executive Summary & Goal

During our DLSU Term 1 schedule planning session, we established a high-fidelity workflow for:
1. Connecting to Google Sheets via Hermes OAuth credentials (`~/.hermes/google_token.json`).
2. Programmatically constructing executive summary tabs (`📋 Schedule Overview & Status`).
3. Generating aesthetic, conflict-free visual weekly timetable grids (`⭐ Locked Schedule - Aki`, `👥 Hanielle's Schedule`, `👥 Lui's Schedule`) with precise 15-minute slot math, custom cell merging, pastel semantic color palettes, and auto-adjusted column dimensions.
4. Ingesting multimodal schedule inputs (Markdown tables, JSON structures, or student portal screenshots) and mapping them directly to Google Sheets API batch updates.

This document serves as the implementation specification for Claude Code to wrap this capability into an installable skill (`google-sheets-scheduler` / `sheets-planner`).

---

## 2. Authentication & Credential Architecture

### 2.1 Credential Source & Token Refresh
The skill leverages Google Workspace OAuth2 tokens. The canonical credential file on the development environment is `~/.hermes/google_token.json`.

Required OAuth Scopes:
- `https://www.googleapis.com/auth/spreadsheets` (Read/Write access to Sheets)
- `https://www.googleapis.com/auth/drive` (File search and metadata)
- `https://www.googleapis.com/auth/calendar` (Optional: calendar event push)

### 2.2 Python Client Initialization
```python
import json
import sys
from pathlib import Path
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

def get_sheets_service(token_path="~/.hermes/google_token.json"):
    path = Path(token_path).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"OAuth token not found at {path}. Run setup.py to authorize.")
    
    with open(path, "r", encoding="utf-8") as f:
        token_data = json.load(f)
        
    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes")
    )
    
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_data["token"] = creds.token
        with open(path, "w", encoding="utf-8") as f:
            json.dump(token_data, f, indent=2)
            
    return build("sheets", "v4", credentials=creds)
```

---

## 3. Visual Timetable Grid Engine

### 3.1 Time Index & Row Mapping
The schedule grid operates on a 15-minute interval system starting at **7:30 AM** and concluding at **6:00 PM** (42 total 15-minute slots across rows 2 through 43).

Row mapping formula:
$$\text{startRowIndex} = \frac{\text{start\_time\_minutes} - 450}{15} + 1$$
$$\text{endRowIndex} = \frac{\text{end\_time\_minutes} - 450}{15} + 1$$
*(where 450 represents 7:30 AM in minutes from midnight, and indices are 0-indexed for the Sheets API).*

#### Discrete Slot Reference Table
| Time Slot | Sheet Row (1-indexed) | Sheets API 0-index (`startRowIndex`) |
| :--- | :---: | :---: |
| `07:30 AM - 07:45 AM` | Row 2 | 1 |
| `09:15 AM - 10:45 AM` | Rows 9–14 | 8 to 14 (6 rows / 1.5 hrs) |
| `10:00 AM - 12:00 PM` | Rows 12–19 | 11 to 19 (8 rows / 2.0 hrs) |
| `11:00 AM - 12:30 PM` | Rows 16–21 | 15 to 21 (6 rows / 1.5 hrs) |
| `12:45 PM - 02:15 PM` | Rows 23–28 | 22 to 28 (6 rows / 1.5 hrs) |
| `02:30 PM - 04:00 PM` | Rows 30–35 | 29 to 35 (6 rows / 1.5 hrs) |
| `04:15 PM - 05:45 PM` | Rows 37–42 | 36 to 42 (6 rows / 1.5 hrs) |
| `05:45 PM - 06:00 PM` | Row 43 | 42 |
| `ASYNC / RESEARCH` | Row 45 | 44 to 45 (Banner) |

### 3.2 Column Architecture & Widths
- **Col 0 (A):** `TIME` (Width: `145px`)
- **Col 1 (B):** `MONDAY` (Width: `180px`)
- **Col 2 (C):** `TUESDAY (Online)` (Width: `180px`)
- **Col 3 (D):** `WEDNESDAY` (Width: `180px`)
- **Col 4 (E):** `THURSDAY` (Width: `180px`)
- **Col 5 (F):** `FRIDAY (On-Campus)` (Width: `180px`)
- **Col 6 (G):** `SATURDAY` (Width: `180px`)

---

## 4. Semantic Color Palette & Styling System

All colors are defined as normalized RGB floats (0.0 to 1.0) compatible with Google Sheets API `repeatCell` and `userEnteredFormat`.

| Category | Background Color (Hex) | Background RGB | Foreground Text (Hex) | Text RGB |
| :--- | :--- | :--- | :--- | :--- |
| **Grid Header** | Deep Forest Green (`#1E593A`) | `0.118, 0.349, 0.227` | White (`#FFFFFF`) | `1.0, 1.0, 1.0` |
| **Time Col (A)** | Light Gray (`#F4F4F7`) | `0.957, 0.957, 0.969` | Dark Slate (`#3F3F3F`) | `0.247, 0.247, 0.247` |
| **Electives / Track** | Soft Mint (`#CCECCE`) | `0.800, 0.929, 0.827` | Dark Forest (`#19662D`) | `0.098, 0.400, 0.176` |
| **Distributed / Systems**| Soft Lavender (`#D3C4F4`)| `0.827, 0.769, 0.957` | Deep Purple (`#3F2672`) | `0.247, 0.149, 0.447` |
| **Innovation / Mgmt** | Soft Sky Blue (`#B2DDF9`) | `0.698, 0.867, 0.976` | Navy Blue (`#14477A`) | `0.078, 0.278, 0.478` |
| **General Education** | Soft Peach (`#FFD8BF`) | `1.000, 0.847, 0.749` | Warm Rust (`#993F19`) | `0.600, 0.247, 0.098` |
| **Art & Humanities** | Warm Amber (`#FFEABF`) | `1.000, 0.918, 0.749` | Deep Amber (`#8C5300`) | `0.549, 0.325, 0.000` |
| **Language & Research**| Soft Teal (`#C7E6E0`) | `0.780, 0.902, 0.878` | Dark Teal (`#145952`) | `0.078, 0.349, 0.322` |
| **Institutional Studies**| Soft Rose (`#F2D1E5`) | `0.949, 0.820, 0.898` | Plum (`#7A1F61`) | `0.478, 0.122, 0.380` |
| **Thesis Title (Col A)**| Deep Burgundy (`#8C194C`) | `0.549, 0.098, 0.298` | White (`#FFFFFF`) | `1.0, 1.0, 1.0` |
| **Thesis Banner (B:G)**| Soft Pink (`#F4D1E0`) | `0.957, 0.820, 0.878` | Deep Burgundy (`#8C194C`)| `0.549, 0.098, 0.298` |

---

## 5. Master Summary Tab (`📋 Schedule Overview & Status`)

The summary tab acts as the primary cockpit for team enlistment and course tracking:
1. **Title Banner:** Course/Term title, target unit load, enlistment time window, and primary invariants (e.g. Free days for internship/thesis).
2. **Student Section Register:** Breakdown per student showing Course Code, Title, Units, Section, Professor, Schedule, Modality/Room, and Real-time Enrollment Capacity.
3. **Cross-Comparison Matrix:** Side-by-side analysis of daily schedules, weekly free days, group study synergies, and strategic workload trade-offs.

---

## 6. Proposed Skill Implementation (`google-sheets-scheduler`)

### 6.1 Directory Structure
```
skills/productivity/google-sheets-scheduler/
├── SKILL.md
├── scripts/
│   ├── scheduler_engine.py      # Core parser, math, and Sheets API orchestrator
│   ├── sheet_styler.py          # Color schemes, fonts, borders, and column layouts
│   └── test_scheduler.py        # Unit tests with mock spreadsheet payloads
└── references/
    ├── time-grid-mappings.md    # Mapping rules for 15-minute / 30-minute grids
    └── color-palette-tokens.md  # Standard hex & Google RGB token catalog
```

### 6.2 CLI Usage Interface
```bash
# Ingest markdown schedule plan and sync to Google Sheets
python scripts/scheduler_engine.py sync \
  --spreadsheet-id 1qqaTvcyz40JvyTDyT8MXiOEjPVh57PAL96jb_967BJ4 \
  --plan-file docs/dlsu_term1_schedule.md

# Add single person timetable tab
python scripts/scheduler_engine.py add-student \
  --spreadsheet-id 1qqaTvcyz40JvyTDyT8MXiOEjPVh57PAL96jb_967BJ4 \
  --student-name "Lui" \
  --units 14 \
  --courses-json '[{"code":"CCINOV8","section":"S03","time":"Tue/Fri 12:45-2:15","room":"G203"}]'
```

---

## 7. Next Steps for Claude Code

1. Ingest this specification document (`docs/2026-08-24-google-sheets-schedule-planner-skill-spec.md`).
2. Implement `scheduler_engine.py` in the designated skill directory.
3. Verify headless OAuth token refresh handling.
4. Support bidirectional syncing between Markdown registers (`dlsu_term1_schedule.md`) and Google Sheets spreadsheets.
