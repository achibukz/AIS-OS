# Owned change persistence

`scripts/owned_persist.py` commits and pushes the changes a writer made, and nothing
else. The cohesion task writer uses it for `tasks.md` whenever it writes that file.

## Enable it

Copy `config/persistence.example.json` to `~/.config/achios/persistence.json`. Each
repository entry names its root, the remote and its exact URL, the branch, the author
identity and the paths writers may persist. Without that file nothing is committed and
cohesion behaves as before.

Install `systemd/achios-persist-retry.timer` with `scripts/install_units.sh`. It runs
`owned_persist.py --retry` hourly and pushes any recorded commit that missed its remote.

## What a writer passes

The path, the text it read before writing, and the text it wrote. The commit blob is a
three-way merge of those two texts with `HEAD`, built in a temporary index. It holds
`HEAD` plus the writer's hunks. Other dirty hunks, other files, staged work and the
working tree are left alone. When the writer's hunks overlap someone else's edit the
receipt says `conflict` and nothing is committed.

Other writers call the same operation with a JSON request on stdin:

```json
{"operation_id": "sciel:note:123", "message": "notes: add seminar summary\n",
 "changes": [{"path": "/abs/path/file.md", "before": "old text", "after": "new text"}]}
```

## Receipt states

| State | Meaning |
|---|---|
| `saved` | The file is written. Nothing was committed. `error` says why. |
| `committed` | A local commit exists. `error` says why it is not on the remote yet. |
| `pushed` | The remote branch holds the commit, checked with `ls-remote`. |
| `conflict` | The owned hunks overlap another edit. Nothing was committed. |

Refusals are explicit: `path_not_authorized`, `wrong_branch`, `wrong_remote`,
`hook_failed`, `head_moved_during_commit`, `unrelated_local_commits`,
`divergent_remote` and `push_failed`.

## Guarantees

- One lock per repository serializes operations.
- The repository's pre-commit hook runs against the owned staging only.
- The commit lands with a compare-and-swap on `HEAD`, so a commit made mid-operation is
  never reverted.
- A local commit made by someone else is never published. The operation refuses to push
  until those commits are pushed or removed by their owner.
- A retry with the same operation ID reuses its commit. A lost push acknowledgement is
  resolved by reading the remote ref.
- There is no force push, rebase or reset.
