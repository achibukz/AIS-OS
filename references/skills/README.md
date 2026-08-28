# Global skills tracked here

Skills in this directory are **global** Claude Code skills whose live home is
`~/.claude/skills/<name>/`. They are kept under `references/` rather than
`.claude/skills/` on purpose: a copy in `.claude/skills/` would auto-load as a
project skill and register a second time under the same name.

`~/.claude/` has no git remote, and `scripts/sync-claude-config.sh` only pushes
Mac to server with `rsync --delete`, so a skill authored on the server is one
sync away from deletion. Committing it here is how it reaches the Mac.

To install one on the Mac:

```
cp -r references/skills/<name> ~/.claude/skills/<name>
```

Then `scripts/sync-claude-config.sh` carries it back down to achibuntu on the
next run, and the Mac becomes the source of truth as it is for every other skill.
