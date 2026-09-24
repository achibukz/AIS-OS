# Vault notes

`scripts/vault_notes.py` is the one writer that saves sourced notes into achiMem and
schoolMem for Sciel, Asa and cohesion. Callers name a destination type. They never pass a
path.

## Notes

| Destination | Written to | Also |
|---|---|---|
| `achimem` | `raw/sessions/<date>-<slug>-<id>.md` | One entry appended to `log.md` |
| `schoolmem` | `inbox/<date>-<slug>-<id>.md` | Nothing else. The inbox README keeps wiki promotion for a real session. |

The caller passes the destinations its topic may use with `--allow`. The schoolMem topic
passes `--allow schoolmem` and cannot write achiMem, whatever name its persona uses.

Each fact is one line with a provenance tag. `[stated]` needs a user source and a quote
that appears in the evidence text the handler supplies. A missing or mismatched quote, or
an assistant source, becomes `[inferred]`. `[document]` needs a citation.

One source ID produces one note. A retry returns the first receipt. A Claude session
source reuses the SessionEnd capture that carries the same `session_id`. A filename that
only looks similar is not a match.

When a cohesion item is completed and a note is linked to it, one dated completion note is
added beside the original. No second task is created.

`vault_notes.py recall --scope achimem --query "..."` searches saved notes. achiMem notes
also appear in the existing SessionStart recall, because they live in `raw/sessions` and
open with `## What happened`.

## The five wiki targets

The allowlist is fixed in code. `~/.config/achios/vault_writes.json` can only switch
targets on:

```json
{"wiki_targets": ["achi-os-status", "timeline-row"]}
```

A target also needs its markers on the page, exactly once. Review these before adding them:

| Target | Page | Markers | Write |
|---|---|---|---|
| `achi-os-status` | `wiki/personal/systems/achi-os.md` | `<!-- achios:status:start -->` and `<!-- achios:status:end -->` | Replace the section between them |
| `achi-core-status` | `wiki/personal/systems/achi-core.md` | same pair | same |
| `achibuntu-status` | `wiki/personal/systems/achibuntu.md` | same pair | same |
| `timeline-row` | `wiki/personal/timeline.md` | `<!-- achios:timeline:insert -->` after the table header | Insert one row below the marker, so the newest row comes first |
| `tooling-decision-row` | `wiki/personal/decisions.md` | `<!-- achios:tooling-decisions:append -->` after the last Tooling / workflow row | Append one row above the marker |

Wiki writes need `[stated]` or `[document]` provenance. A `[stated]` wiki fact also needs
a user source. A page that changed since the proposer read it becomes a conflict, and the
proposed text is kept in `raw/conflicts/`. The vault linter runs before and after; any
new error leaves the page saved but uncommitted.

## Persistence

Receipts keep `saved`, `linted`, `committed` and `pushed` separate. Commits go through
`owned_persist`, so add the vaults to `~/.config/achios/persistence.json`. Suggested
paths: `raw/sessions/*.md`, `log.md` and `inbox/*.md`, plus the five wiki pages once they
are enabled.
