# CLI v0.1

## C1 — Names and working verbs

One binary, `larder`; `lrd` is a symbolic link to it with identical behavior.
All diagnostics start `larder:` regardless of invocation name. Usage names both.

- `larder version`: `larder 0.1.0 (lrd; read-only format v1)`.
- `larder check-manifest FILE`: strict F2/F3 validation, exact-byte SHA-256 and
  input byte length on stdout. No verification of signatures or payload implied.
- `larder compare V1 V2`: V2 versions, normalized result -1, 0 or 1.
- `larder resolve --snapshot DIR --want SPEC [--want SPEC ...] [--json]`:
  read `DIR/snapshot.lrd`, emit a complete independently checked plan or refuse.
  At least one want; a spec is `NAME[@ARCH/SLOT][OPVERSION]`, where OP is
  `=`, `!=`, `<`, `<=`, `>` or `>=`; absent constraint means any. Defaults come
  from the snapshot. The JSON object has `status`, `selected`, `removals`,
  `nodes` and `explanation`; each removal identifies old and replacing package.
  Text output has deterministic identity order. No root, cache or trust writes.
- `--help` / `help`: usage, exit 0. `--version` is an alias for version.

## C2 — Refusals and exits

`install`, `remove`, `upgrade`, `sync` always refuse individually by name:
`larder: VERB refused: mutation arrives in pm04`, exit 6. No argument can enable
mutation. Reserved paths (not written): `/var/lib/larder/`, `/var/cache/larder/`,
`/etc/larder/`; config proposal `<file>.larder-new`.

Exit 0 success; 1 malformed data, invalid version or I/O refusal; 2 usage errors
(print usage to stderr); 3 proven unsatisfiable snapshot; 4 budget exceeded
(search incomplete); 5 independent checker disagreement; 6 mutation unavailable.
No hidden transport or eval verb. Errors use stderr; successful data use stdout.

## C3 — Boundaries and fixtures

CLI tests compare exact stdout, stderr and exit status for both names, including
all mutating verbs, malformed signed bytes, usage, versions, snapshots, holds,
ABI mismatch, constraints, virtuals, conflicts, removals and budget distinction.
Inputs/outputs live under tests; tests use a lane-local or checkout-local TMPDIR.
The largest fixture's resolution time is recorded, not performance-gated.
