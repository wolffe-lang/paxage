# larder

PAX's package manager, also invoked as `lrd`. This repository is **private**.
The current 0.1.0 implementation is read-only: format validation, version order
and dependency planning. It cannot install, remove, upgrade, sync, fetch or sign.
The name has not been registered in any package registry.

## Build and try

Requires the platform C linker, Python 3 (fixture harness), curl, git and tar.
Supported CI hosts: Linux x86-64 and macOS arm64. No other runtime dependencies
beyond the digest-pinned Wolf release/runtime and std tree.

```sh
mkdir -p "$HOME/lanes/pm01/tmp"
export TMPDIR="$HOME/lanes/pm01/tmp"
tools/fetch-toolchain
tools/build
target/bin/larder version
target/bin/lrd check-manifest tests/manifests/valid.manifest
target/bin/larder compare 1~rc-1 1-1
target/bin/larder resolve --snapshot tests/snapshots/basic --want app --json
```

`tools/build` produces one native executable and an `lrd` symbolic link; no
system installation is performed. Both names have identical behavior and every
diagnostic is prefixed `larder:`. On shared development hosts, build a committed
copy behind its host lock and memory/disk gates; see the lane contract.

## Format and boundaries

- [FORMAT](docs/FORMAT.md): three immutable targets, strict Wolf-literal data,
  complete manifest/file records and the future restricted POSIX pax reader.
- [RECIPE](docs/RECIPE.md): declared inputs/environment/argv, no install scripts.
- [VERSION](docs/VERSION.md): epoch:upstream-release, larder's own order, not
  Arch/RPM/Debian compatibility. Digit runs never use a bounded integer.
- [SOLVER](docs/SOLVER.md): immutable bounded snapshots, complete backtracking,
  latest compatible choices, independent checker, holds/ABI/optional/replacement
  policy and budget refusal distinct from exhaustive unsatisfiability.
- [CLI](docs/CLI.md): verbs, request syntax and exit codes.

A checked manifest is syntactically valid, **not authenticated**. TUF, archive
parsing/staging, transactions and networking are later work. Reserved paths
`/var/lib/larder/`, `/var/cache/larder/`, `/etc/larder/` and `.larder-new` are
specification only; this program writes none of them.

## Tests and contributing

```sh
tools/gauntlet
```

The stopping gauntlet prints each `END ... exit=N` and runs fmt, build, unit
properties and CLI fixture e2e. Units exhaustively enumerate 64 subsets for each
of 10,000 seeded small graphs, independently comparing the abstract oracle,
checker and solver; the seed is printed. Hand-derived version vectors have no
foreign implementation oracle. CLI fixtures exercise both executable names,
malformed-input rejection, exact-byte SHA-256, snapshots and all mutation
refusals. The largest fixture has 24 packages; its time is reported, not gated.
No SKIPs are hidden.

**CI has one tier:** every PR (including draft) and every trunk push runs the
same complete gate on Linux x86-64 and macOS arm64. No labels or planner select
lesser coverage. A green run requires both matrix jobs, including CLI e2e; a
unit-only run is insufficient.

PR descriptions carry a `Footprint:` line: `notes` for prose only, `module` for
one program/module without shared tools or specs, `cross-cutting` for format,
pins, CI or shared tooling. This first harness/format pass is cross-cutting.
Use the five lane-note sections, terse chunk commits, no attribution trailers.
A deliberate off-line break belongs on its own `pm01-plant-*` draft PR; never
merge a plant. No package-manager/comparator/resolver implementation source may
be consulted, whatever its licence. Golden vectors derive from the spec alone.

## Licence

GPL-3.0-or-later; the supplemental training-data terms are in
[LICENSE-TRAINING-DATA](LICENSE-TRAINING-DATA). Both licence files are copied
byte-for-byte from lope trunk; their hashes and source revision are recorded in
the lane evidence.
