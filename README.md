# larder

PAX's package manager, also invoked as `lrd`. This repository is **private**.
The current 0.1.0 implementation validates formats, orders versions, plans
dependencies, packs canonical payloads and stages into a private empty directory.
It cannot install, remove, upgrade, sync, fetch or sign. Large-file qualification
is blocked on the bounded SHA-2 std fix (sc76); the RSS gate remains red. Do not
use this revision for large packages.
The name has not been registered in any package registry.

## Build and try

Requires the platform C linker, Python 3 (fixture harness), curl, git and tar.
Supported CI hosts: Linux x86-64 and macOS arm64. No other runtime dependencies
beyond the digest-pinned Wolf release/runtime and std tree.

```sh
mkdir -p "$HOME/lanes/pm02/tmp"
export TMPDIR="$HOME/lanes/pm02/tmp"
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
  complete manifest/file records and the restricted POSIX pax reader/writer.
- [RECIPE](docs/RECIPE.md): declared inputs/environment/argv, no install scripts.
- [VERSION](docs/VERSION.md): epoch:upstream-release, larder's own order, not
  Arch/RPM/Debian compatibility. Digit runs never use a bounded integer.
- [SOLVER](docs/SOLVER.md): immutable bounded snapshots, complete backtracking,
  latest compatible choices, independent checker, holds/ABI/optional/replacement
  policy and budget refusal distinct from exhaustive unsatisfiability.
- [CLI](docs/CLI.md): verbs, request syntax and exit codes.

A checked manifest is syntactically valid, **not authenticated**. `stage` accepts
an externally expected blob digest/length, validates the complete inventory, and
verifies staged bytes, modes and links. Staging is unprivileged and never promotes
a tree to a live root. Missing descriptor-relative calls leave a same-uid ancestor
swap race; use a private empty caller-owned staging directory. [CLI C4–C7](docs/CLI.md)
details the interface, safety refusals, failure state and current large-file blocker.
TUF, transactions and networking remain later work. Reserved paths
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
refusals. Payload rows add independent POSIX-byte valid/hostile vectors, exact
mode/digest/link roundtrips, insertion-order determinism, FIPS known answers,
100,000 seeded mutations with per-input timeouts, capped Linux digest-free reader
RSS, and 64 MiB/1 GiB full-reader RSS. Linux also runs digest-pinned GNU tar and
bsdtar container contrasts and read-only-parent confinement; these are black boxes,
not verdict oracles. Container tests require podman or Docker. Full SHA-2 RSS is
currently blocked on sc76, not waived. The largest solver fixture has 24 packages;
its time is reported, not gated. No SKIPs are hidden.

**CI has one tier:** every PR (including draft) and every trunk push runs the
same complete gate on Linux x86-64 and macOS arm64. No labels or planner select
lesser coverage. A green run requires both matrix jobs, including CLI e2e; a
unit-only run is insufficient.

PR descriptions carry a `Footprint:` line: `notes` for prose only, `module` for
one program/module without shared tools or specs, `cross-cutting` for format,
pins, CI or shared tooling. The format/CLI/payload pass is cross-cutting.
Use the five lane-note sections, terse chunk commits, no attribution trailers.
A deliberate off-line break belongs on its own lane-prefixed `*-plant-*` draft PR;
never merge a plant. No foreign package-manager, comparator, resolver, archiver,
compressor or signature implementation source may be consulted, whatever its
licence. The org's own wolf/std/larder sources are permitted; golden vectors derive
from specifications alone.

## Licence

GPL-3.0-or-later; the supplemental training-data terms are in
[LICENSE-TRAINING-DATA](LICENSE-TRAINING-DATA). Both licence files are copied
byte-for-byte from lope trunk; their hashes and source revision are recorded in
the lane evidence.
