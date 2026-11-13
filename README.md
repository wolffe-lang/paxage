# paxage

formerly larder, renamed 2026-11-09

PAX's package manager, also invoked as `pxg`. The current 0.1.0 implementation
validates formats, orders versions, plans dependencies, packs canonical payloads,
and publishes test-only signed file repositories. It bootstraps, updates and fetches
from local repositories through a bounded TUF profile. Install, upgrade and removal
use crash-safe transactions on journalled Linux filesystems under test, with a rescue
entry. Selected read-only commands are tested on PAX under QEMU, but PAX package
transactions are not enabled. The live root `/` remains refused until PAX's boot
recovery. Network fetch is not supported. `sync` is refused:
`upgrade` is the refresh-and-upgrade operation. Signing keys must be marked `test-only`;
production signing remains out of scope. The std pin includes bounded SHA-2 and
strict Ed25519 verification. Fuzz, growth rows and large-input measurements run
only on Linux under a 2 GiB cap, never on the Mac.
The name has not been registered in any package registry.

## Build and try

Requires the platform C linker, Python 3 (fixture harness), curl, git and tar.
Supported CI hosts: Linux x86-64 and macOS arm64. No other runtime dependencies
beyond the digest-pinned Wolf release/runtime and std tree.

```sh
mkdir -p target/tmp
export TMPDIR="$PWD/target/tmp"
tools/fetch-toolchain
tools/build
target/bin/paxage version
target/bin/pxg check-manifest tests/manifests/valid.manifest
target/bin/paxage compare 1~rc-1 1-1
target/bin/paxage resolve --snapshot tests/snapshots/basic --want app --json
# A synthetic root from a file:// repository (see TRANSACTIONS):
target/bin/pxg init --root ROOT --repo file:///REPO --pinned-root ROOT.json --arch x86_64 --slot default
target/bin/pxg install --root ROOT NAME
target/bin/pxg status --root ROOT
target/bin/pxg rescue --root ROOT
```

`tools/build` produces one native executable, a `pxg` symbolic link and the
test-only `paxage-failpoint`; no system installation is performed. Both names
have identical behavior and every diagnostic is prefixed `paxage:`. On shared
development hosts, build a committed copy behind the host lock and memory/disk
gates.

On Linux x86-64, `tools/build --static` builds stripped static executables under
`target/static/` using the same pinned Wolf/runtime/std. It needs a C linker with
static libc inputs and `strip`. `python3 -I tools/check-pax-static --build` checks
ELF64 ET_EXEC, absence of PT_INTERP/PT_DYNAMIC, the short link and basic read-only
commands. The static build also produces a read-only `qualify-probe` for the
regression suite. That probe and the failpoint executable are test-only, not
programs to install on a normal system.

The PAX regression distinguishes a stock installer-created ext2 root from a
host-created journalled ext3 root. Read-only CLI comparisons and the 63 raw ABI
rows do not enable root mutations or qualify crash durability. Plain ext2 stays
refused; live-root writes still require the separate maintenance/recovery path.

## Format and boundaries

- [FORMAT](docs/FORMAT.md): three immutable targets, strict Wolf-literal data,
  complete manifest/file records and the restricted POSIX pax reader/writer.
- [RECIPE](docs/RECIPE.md): declared inputs/environment/argv, no install scripts.
- [VERSION](docs/VERSION.md): epoch:upstream-release, paxage's own order, not
  Arch/RPM/Debian compatibility. Digit runs never use a bounded integer.
- [SOLVER](docs/SOLVER.md): immutable bounded snapshots, complete backtracking,
  latest compatible choices, independent checker, holds/ABI/optional/replacement
  policy and budget refusal distinct from exhaustive unsatisfiability.
- [TRUST](docs/TRUST.md): canonical signed spans, four-role metadata, rotation,
  clock/version floors, atomic generations, verified cache and test-only keys.
- [TRANSACTIONS](docs/TRANSACTIONS.md): the lock inode, qualification (ext3/ext4
  with an active journal), the descriptor walk, generations, the intent, undo and
  rescue, actions, ownership and config rules, the old-or-new check, and the
  power-cut witness (X11).
- [CLI](docs/CLI.md): verbs, request syntax and exit codes.

A checked manifest is syntactically valid, **not authenticated**. `stage` accepts
an externally expected blob digest/length, validates the complete inventory, and
verifies staged bytes, modes and links. Staging is unprivileged and never promotes
a tree to a live root. Missing descriptor-relative calls leave a same-uid ancestor
swap race; use a private empty caller-owned staging directory. [CLI C4–C7](docs/CLI.md)
details the interface, safety refusals, failure state and large-file measurement policy.
`fetch --stage` authenticates payload, manifest and buildinfo through signed
metadata and binds the manifest again at staging consumption. The client supports
only literal `file://` URLs and a caller-supplied pinned root. Network transports
remain later work. Transactions (TRANSACTIONS X1–X11) write a root only through
handles held from its root directory, take the root's persistent lock and refuse an
unjournalled filesystem. Tests exercise recovery to the old or the new generation
after process and power cuts. Trusted local state must not be coherently
replaced by an actor able to write it; T20 documents this limit. Malformed state
refuses without repair, directing an explicit re-bootstrap into a new empty directory.
A root's state lives in `ROOT/var/lib/paxage/` and its cache in
`ROOT/var/cache/paxage/`; `.paxage-new` names config proposals. `/etc/paxage/`
remains reserved and unwritten.

## Tests and contributing

```sh
tools/gauntlet
```

The stopping gauntlet prints flat `START` / `END ... exit=N secs=S` steps,
retains subtest PASS/FAIL names, and runs fmt, build, unit
properties and CLI fixture e2e. `census` fails if the former name or its short
command reappears in a tracked file or path outside the records it lists (the lane
notes and predictions); `names` holds the executables, the `paxage:` prefix, the
state, cache and reserved config paths, the `.paxage-new` proposal, the intent
header, the temporaries and `PAXAGE_FAILPOINT`, with no old name as an alias. Units exhaustively enumerate 64 subsets for each
of 10,000 seeded small graphs, independently comparing the abstract oracle,
checker and solver; the seed is printed. Hand-derived version vectors have no
foreign implementation oracle. CLI fixtures exercise both executable names,
malformed-input rejection, exact-byte SHA-256, snapshots and all mutation
refusals. Payload rows add independent POSIX-byte valid/hostile vectors, exact
mode/digest/link roundtrips, insertion-order determinism, FIPS known answers,
100,000 seeded mutations with per-input timeouts on capped Linux, capped Linux digest-free reader
RSS, and 64 MiB/1 GiB full-reader RSS. Linux also runs digest-pinned GNU tar and
bsdtar container contrasts and read-only-parent confinement; these are black boxes,
not verdict oracles. Container tests require podman or Docker. BSD negative-time
binary numeric fields are expected F6.2 refusals, even with a valid pax override.
The unchanged full SHA-2 RSS bound is under 8 MiB growth. The largest solver fixture has 24 packages;
its time is reported, not gated. No SKIPs are hidden.

Trust tests include strict JSON/schema rows, RFC 8032 and all 151 vendored
Wycheproof cases, independent OpenSSL-signed attack trees, interrupted-write cuts,
zero-write corruption refusals, two-publication CLI roundtrips and a separate
100,000-mutation Linux harness. Its per-input state oracle uses independently
witnessed signatures, not the client's verdict alone. OpenSSL CLI runs only in
the pinned offline unprivileged Linux container. Set `PXG_RIG_PROFILE=linux-16core`
to opt into that container on a suitable host; the default `generic` profile
skips it. `PAXAGE_CONTAINER_CPUS` may override the default CPU set `0-3`.
Mac runs use bounded rows and
the payload roundtrip-only path, retaining the canonical-payload identity artifact;
growth/fuzz/timing skips are explicit. Coherent local-storage replay has a labelled
limit witness, not a claimed protection gate.

Transaction rows (`tools/check-transactions`) build a signed fixture repository and
drive every root verb. Each named hook of install, upgrade, remove and rescue is
crashed in turn (a runtime trap), and `rescue` runs twice. The digests must be
identical and equal the untouched root's or the completed run's. Injected EIO and
ENOSPC, ancestor swaps for links, lock contention and lock-owner death, conflicts,
the three config cases, residuals, purge and an orphan cycle are covered too.
They run as the caller (owners logical) on every host. A second take runs as root
(owners applied): in a rootless Linux container, or under `sudo` on CI Linux.
The Mac skips the root take and the tmpfs refusal loudly.

The power-cut witness (`tools/check-powercut`, TRANSACTIONS X11) runs on a Linux
take with KVM and the staged Ubuntu 24.04 guest. An NBD recorder logs every block
write and flush the guest issues. Crash states are built at and between every
durable step, with torn sectors, on ext4 and ext3. Each state must recover to the
old or the new generation, twice identically and fsck-clean. Real EIO and ENOSPC,
two writers, the ext2 refusal and the transaction rows in the guest are covered
too. Its host rows (the recorder's protocol and the crash-state synthesis) run
everywhere. CI and the Mac skip the guest loudly.

Unlabelled PRs run one cheap job. The `ci` or `full-matrix` label runs the
full platform-aware gate on Linux x86-64 and macOS arm64. Trunk pushes run it
only on cross-cutting paths; the nightly and default dispatch run the same
full gate. A full green run requires both matrix jobs, including CLI e2e,
and the cross-host canonical-payload byte comparison; a unit-only run is
insufficient.

PR descriptions carry a `Footprint:` line: `notes` for prose only, `module` for
one program/module without shared tools or specs, `cross-cutting` for format,
pins, CI or shared tooling. The format/CLI/payload pass is cross-cutting.
Use the five lane-note sections, terse chunk commits, no attribution trailers.
A deliberate off-line break belongs on its own lane-prefixed `*-plant-*` branch,
pushed without a PR. Record its named failing row locally; never merge a plant.
No foreign package-manager, comparator, resolver, archiver,
compressor or signature implementation source may be consulted, whatever its
licence. The org's own wolf/std/paxage sources are permitted; golden vectors derive
from specifications alone.

## Licence

GPL-3.0-or-later; the supplemental training-data terms are in
[LICENSE-TRAINING-DATA](LICENSE-TRAINING-DATA). Both licence files are copied
byte-for-byte from lope trunk; their hashes and source revision are recorded in
the lane evidence.
