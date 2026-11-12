# pm05a — the rename

Footprint: cross-cutting (every tool, the gauntlet, the build and the CI's
gate change names).

The package manager was renamed **paxage**, short command **`pxg`**, on
2026-11-09, while the repository was private and nothing had been installed
anywhere. Until then it was larder (`lrd`). The prediction is
`prediction-pm05a.txt` (`ca8d602`), committed first with the census. The branch
began on trunk `e29dac3` and was rebased onto `b3e891e` (PR #12, `disconnect()` in
`tools/check-powercut`) without a conflict.

## The claim

Everything the repository holds that names the program now says paxage:

| Class | New |
|---|---|
| executables | `paxage`, the link `pxg`, the test-only `paxage-failpoint` |
| sources | `src/paxage.lu`, `src/paxage_failpoint.lu`, package `paxage` |
| version line | `paxage 0.1.0 (pxg; format v1, file trust, pack and stage, linux transactions)` |
| diagnostics | `paxage: …` and `paxage-failpoint: …` |
| state and cache | `ROOT/var/lib/paxage/`, `ROOT/var/cache/paxage/` |
| reserved config | `/etc/paxage/` (still never written) |
| config proposals | `PATH.paxage-new` |
| intent header | `paxage-intent<TAB>1` |
| temporaries | `.paxage-t<N>-<i>`, `.paxage-t<N>-u<i>` |
| data files | `snapshot.pxg`, `generations/<N>/db.pxg` |
| variables | `PAXAGE_*` (22 names, each `LARDER_X` → `PAXAGE_X`) |
| test account | gecos "paxage test daemon" |
| guest paths | `/mnt/p/paxage`, `/mnt/m/paxage`, the payload's `paxage/` prefix |

No migration and no alias: no former link, no former variable read, no former
path consulted. Nothing else moves: exit codes, verbs, the hook set, every
format's fields (the intent's header word aside), the trust vectors, the
solver fixtures' bytes and the canonical payload are unchanged.

## Rulings

The following choices were made on 2026-11-09, after the census:

1. The `.lrd` extension becomes `.pxg`.
2. The names the contract did not list (the intent header, the temporaries, the
   test account, the mktemp prefixes, the guest paths) are renamed too.
3. `larder#9` in `tools/lib-fetch.sh` becomes `paxage#9`; the PR number
   survives the repository's rename.
4. The CHANGELOG's unreleased 0.1.0 entries use the new names; one entry records
   the rename, and its first line is the CHANGELOG's only allowlisted line.
5. The census: the former name in any case anywhere, its short command in any
   case as a token, over every tracked file's bytes and path; an explicit list
   of record files and exact allowlisted lines; `tools/check-census` holds the
   only definition of the former words.
6. `names-no-old-environment`: a rig that still sets a former variable goes red
   by name instead of quietly skipping the root and power-cut legs.
7. `LARDER_ROOT` becomes `PAXAGE_ROOT`, mechanically like the rest.

## The rows

`tools/check-census` (step `census`, before the build) prints
`FAIL census-old-names PATH:LINE: TEXT` for every line, and
`FAIL census-old-paths PATH` for every path, that carries a former name outside
its record list. Its records are the lane notes for pm01, pm02, pm03, pm04,
pm04b and pm05a, `notes/name-checks.txt`, `notes/provenance.txt`, the five
predictions that name it and `tools/check-census` itself. The exact lines are
the README's "formerly larder, renamed 2026-11-09" and the CHANGELOG's rename
entry. `census-allowlist` goes red if a record is untracked or an allowed line
is gone.

`tools/check-names` (step `names`, after `cli`) runs every row and fails at the
end if any is red. It drives the built executables and check-transactions' own
fixture repository, and it imports the former words from check-census, so it
carries none:

- `names-binary`, `names-short-link`, `names-failpoint-binary`,
  `names-old-binaries-absent` (no former name in `target/bin`, `.dSYM`
  included);
- `names-version-line` (both names), `names-prefix` (a refusal and the usage,
  through both names), `names-failpoint-prefix`;
- `names-state-path`, `names-cache-path`, `names-database-file`;
- `names-proposal-suffix` (a both-changed upgrade, and `status` lists it),
  `names-etc-reserved`;
- `names-intent-header` (a crash at `intent`), `names-temp-prefix` (a crash at
  the first `apply:<i>:temp`);
- `names-failpoint-env` (`PAXAGE_FAILPOINT=trace` traces, the former variable
  alone traces nothing, a bad spec names the new variable),
  `names-shipped-no-failpoint`;
- `names-root-tree` (no former name in any path or file of the roots the rows
  made, the checkout's own path aside);
- `names-no-old-environment`.

Seen red at the rows' commit, before any rename (`e306e02`, the NixOS Linux host light A,
`evidence/red-linux-e306e02.record`, sha256 `e41a80bc…`):
`red-census` printed 376 `FAIL census-old-names` lines and 21
`FAIL census-old-paths` lines, as predicted, with `census-allowlist` green;
`red-names` printed 17 FAILs, every row but `names-no-old-environment`, which
passed on the take's clean environment. `names-old-binaries-absent` named the
base's own build (`larder`, `larder-failpoint`, `lrd`); the fixture rows failed
with "fixture unavailable", since no `paxage` existed to publish it.

## Deviations from the prediction

- `tools/check-chunk-rss` named its rows `larder-only-*` (the reader alone, not
  the archivers). They are `paxage-only-*` now. The prediction said no existing
  row name would change.
- `names-root-tree` is an eighteenth row the prediction did not list: a content
  and path scan of every root the names rows made.
- On the Mac, `target/bin` also holds `.dSYM` directories;
  `names-old-binaries-absent` covers them by the same rule.
- The rebase onto PR #12 applied cleanly; the prediction expected a conflict
  in `tools/check-powercut`. #12's `disconnect()` is kept, under the new names.
- The first red take, at the rows' commit before the rebase (`a2137d2`), was red
  exactly as the second; it is superseded because that commit is not on the
  branch.
- `CLAUDE.md` gained one line: a new note or prediction that must name the
  former name goes on check-census's record list by path.
- **A prediction miss: the plant's third row did not go red by name.** The
  first plant take (`60040e2` on `0fb7250`, the Mac,
  `evidence/plant-mac-60040e2.record.void-unnamed-row`, sha256
  `dcd9a7e8…`) was red by name for `census-old-names` and
  `names-proposal-suffix`, and the recorder refused it: "missing FAIL line for
  config-both-changed-proposal". The run reached that row, and the row does
  look at the suffix, but its check read the proposal's bytes directly. With
  the proposal missing, `read_bytes()` raised `FileNotFoundError` inside the
  check's own condition, so the row died as an anonymous traceback before it
  could print its FAIL, and the uncaught exception also stopped `--all`, so
  `config-proposal-exists` never ran. This was a pre-existing harness defect:
  any regression that stopped writing a proposal would have gone red without a
  row's name. `7e99453` fixes the runner: a row group whose check raises prints
  `FAIL <group> crashed <exception>` and, under `--all`, the other rows run.
  Checked before the retake on the NixOS Linux host light A at `7e99453`: every transaction row
  passed, and on a scratch, never-pushed commit with the plant's hunk,
  `config-both-changed-proposal` and `config-proposal-exists` each printed FAIL
  by name. The plant was retaken once, on the head that carries the fix.

## Forbidden

- The GitHub repository rename was separate from this work.
- No foreign source of any kind was read; the rename reads only this
  repository.
- Nothing in `/tmp` on any host. Never signed on the NixOS Linux host. The FHS Linux host and the 860
  untouched. No label, merge, tag or close; no attribution trailers. Every
  other lane's files were reused by copy only (pm04's guest inputs, toolchain
  and GNU time).

## Inputs, verified

- Base trunk `b3e891e`. Toolchain unchanged: wolf 0.2.38, lupin 0.1.60, std
  `23baa1a`. The Mac's was staged by `tools/fetch-toolchain` from copies of the
  release archives, each digest checked against `wolf-toolchain.toml`; the
  Linux hosts' are copies of pm04's staged trees, whose stamp names the same pin.
- The guest: the Ubuntu 24.04 release 20261017 image, kernel and initrd, copied
  from pm04's staging and re-checked against their pinned digests (`04e8f246…`,
  `41ba36d8…`, `bf276ffc…`) on each host; `vm-inputs-digests` re-reads them on
  every take.
- The recorder: `tools/gauntlet-record.sh` at `862387f2`, sha256
  `ec9f42c9…`, the same on every host.

## Prediction

`prediction-pm05a.txt` (`ca8d602`): the census by class, the rows and their
red at the base, what must not change, the gate, the plant and the R-list.

## Evidence index

- Red: `evidence/red-linux-e306e02.record` (and the superseded
  `red-mac-a2137d2.record.superseded`, the same red on the Mac before the rebase).
- Green: the Linux record with power cuts and the Mac record at the PR's head,
  named in the PR body.
- Plant: `pm05a-plant-suffix`, one hunk in `src/txn/txn.lu` putting the former
  suffix back, rebuilt on the final head; its record is named in the PR body.
  The first take's record is void (above, "A prediction miss").
- Superseded: `green-mac-0fb7250.record` and the Arch Linux host's
  `green-linux-0fb7250.record`, valid at `0fb7250`, before `7e99453`.

## Done-when

- `census` and `names` green at the head; every other step green as before.
- The whole gauntlet green on a Linux KVM host, `transactions-privileged` and
  `powercut-vm` run (not skipped), and on the Mac.
- The plant red by name.
- The full-matrix CI run green on both hosts with the cross-host payload
  identity.
