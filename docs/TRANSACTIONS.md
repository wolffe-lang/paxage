# Transactions v1 (Linux, file:// repository)

pm04's implementation of pax `notes/pm00-the-design.md` R-pm00-6, -9 and -10.
Sources: rename(2), fsync(2), flock(2), openat(2), statfs(2), proc(5) and sysfs
documentation, ext4's documented journalling, passwd(5), group(5), shadow(5), and
pacman's and dpkg's documented behaviour. No other package manager's,
archiver's or filesystem's source was read.

## X1 — Roots and privilege

Every root verb takes `--root DIR`, a synthetic root. `/` refuses
`live-root-is-pm05`: the live root waits for PAX's boot recovery. A root is
initialized once (`init`) as *privileged* (euid 0: manifest owners are applied by
handle) or *logical* (any other caller, on a root that caller owns; owners are
recorded but never applied, pm02's rule). The mode is fixed at init; using a root
in the other mode refuses `ownership-mode-mismatch`.

## X2 — Qualification

Mutation runs only on a qualified filesystem. On Linux that is ext3 or ext4
(`statfs` type 0xEF53) with an active jbd2 journal for the root's own device: the
device's kernel name comes from `/sys/dev/block/MAJOR:MINOR` (or
`/proc/self/mountinfo`), and `/proc/fs/jbd2/NAME-*` must exist. Plain ext2 (the
same magic, no journal), tmpfs, overlay and every other type refuse
`unqualified-filesystem`, by name, at init and before every transaction. macOS
roots are development roots: accepted, with no durability claim. This exception
is macOS-only. `os_name` describes the running kernel, so a static Linux binary
reports `pax` on PAX; it must not acquire the development exception. PAX ext-family
roots currently refuse `unqualified-filesystem` until a native positive journal
proof is qualified. Other unsupported operating systems fail closed as well.

## X3 — The descriptor walk

Every name in the root is reached one component at a time from the held root
handle, each directory opened with `O_DIRECTORY|O_NOFOLLOW`. A link or
non-directory at any level refuses `path-race PATH`. Files are created by
`openat(O_CREAT|O_EXCL|O_NOFOLLOW)` in the held parent; modes and owners are set
on the open handle (`fchmod`, `fchown`) before the file has its name. wolf 0.2.38
has no `renameat`, `readlinkat` or `fchownat` (wolf-lang#1084). Those three
operations run with the working directory pinned: one-component `chdir` steps from
the root, each step's `.` checked by device and inode against the held handle,
then a one-component name. paxage is single-threaded, so pinning the
process-wide working directory is sound.

## X4 — The database

`ROOT/var/lib/paxage/` (0700, one filesystem with the root):

- `lock`: the persistent lock inode, made once by init, never unlinked or
  recreated, no PID inside. Each writer opens it with `O_NOFOLLOW` and takes an
  exclusive non-blocking `flock`. Contention exits 7 `locked`. The lock dies with
  its owner however the owner ends. A missing lock refuses `lock-missing`; a link
  or non-file refuses `lock-inode`.
- `current`: the commit decision, F2 `current { schema, features, generation,
  database, transaction }`. `database` is the SHA-256 of that generation's
  `db.pxg`.
- `generations/<N>/db.pxg`: an immutable F2 `database` record, holding:
  - arch, slot, repository and ownership mode;
  - the installed packages, each with its reason (explicit or dependency) and the
    SHA-256 of its manifest;
  - config baselines;
  - residuals and owned `.paxage-new` proposals;
  - declared accounts, action-created directories and pending actions.

  `generations/<N>/manifests/<sha256>` holds each installed manifest's exact
  bytes. The ownership index is derived from those manifests and never stored.
- `transactions/t<N>/`: the one in-flight transaction to generation N. It holds
  `intent`, `backup/<i>` and `stage/<package>/`.
- `trust/`: pm03's trust generations. They are monotonic and outside package
  rollback.

`ROOT/var/cache/paxage/` is pm03's hash-bound cache. Generation numbers and
transaction ids are deterministic, so two identical runs write identical bytes.

## X5 — The transaction

Planning is read-only. Any refusal leaves zero writes. The durable steps follow,
in order, each followed by its named hook (X8):

1. **stage**: `t<N>/` is made. Each new or changed package is fetched through
   pm03's verified cache and staged by pm02's `stage` into `t<N>/stage/<name>`,
   with euid 0 allowed only there.
2. **backup:<i>**: an exact copy of every regular file the plan replaces or
   deletes, checked against the planned digest and fsynced. The backup directory
   is then fsynced.
3. **intent-written**, **intent**: `t<N>/intent.tmp` is written and fsynced, then
   renamed to `intent`, and both directories are fsynced. The intent is one
   tab-separated line per operation (index, action, path, the old and new
   identities, backup flag), ending with `end <sha256 of every preceding byte>`.
4. **apply:<i>:walk**, **:temp**, **:renamed**, **apply:<i>**: one hook set per
   operation, in order. Operations run:
   - mkdir shallowest-first, then directory metadata changes;
   - file and symlink puts: a same-directory temporary `.paxage-t<N>-<i>`,
     content checked against the planned SHA-256, owner then mode by handle,
     fsync, rename over the name (X3), fsync of the parent;
   - hard links, as a temporary link renamed into place;
   - deletes, then rmdirs deepest-first.

   Before each operation the live name must still be the planned old identity
   (`live-changed`).
5. **validate**: every operation's path is its new identity, with hard links
   sharing their source's inode, and every declared account is consistent across
   passwd and group.
6. **generation**: `generations/<N>/` with its manifests and `db.pxg`, all
   fsynced.
7. **commit-written**, **commit-renamed**, **commit**: `current.t<N>` is written
   and fsynced, renamed over `current`, and the directory is fsynced. `current`
   naming t<N> is the commit decision; no other record contradicts it.
8. **cleanup:backup**, **:stage**, **:intent**, **:dir**, **done**: `t<N>/` is
   removed through handles, deepest first, with each directory fsynced.

On an error before the commit, the verb undoes in-process (X6's undo) and exits 1
with `rolled back`. If the undo refuses, it says `rollback refused` and leaves
the transaction for `rescue`. An error after the commit leaves cleanup to
`rescue`.

## X6 — Recovery and the rescue entry

While `transactions/` holds anything, `install`, `remove`, `upgrade`,
`autoremove` and `verify` exit 8 `recovery-needed`. `status` reports it
read-only. Only `rescue` acts (R-pm04-3):

- Nothing pending: `rescue: nothing to do`, zero writes, exit 0.
- `current` names t<N>: finish (X5 step 8), `rescue: finished t<N>`.
- t<N> without `intent`: nothing live was touched. `rescue: discarded t<N>`
  removes it, with any uncommitted generation and commit temporary.
- t<N> with a valid intent: undo. Undo first checks every backup's digest
  (`rescue-missing-backup`) and classifies every operation's live identity as old
  or new. Anything else refuses `rescue-unknown-state PATH`, with zero writes.
  Then, in reverse order:
  - it removes every temporary of the operation;
  - restores each new identity to its old one (from its backup, a recorded link
    target, recorded directory metadata, or by removal);
  - relinks hard links to their restored sources;
  - verifies every path is old again;
  - removes the intent first, with t<N> fsynced (`rescue:cleanup:intent`), so a
    power cut from here on leaves a t<N> without an intent, which rescue
    discards;
  - removes the uncommitted generation, `current.t<N>` and t<N>.

  It prints `rescue: undone t<N>`.

Rescue's own steps have hooks (`rescue:undo:<i>`, `rescue:relink:<i>`,
`rescue:generation`, `rescue:cleanup:*`) and tolerate a crash at any of them. A
malformed intent refuses `rescue-malformed-intent`. A `current` or generation
that does not verify refuses `rescue-ambiguous-generation`. A swapped ancestor
refuses `rescue-unknown-state`. Every refusal exits 9 and is repeatable once the
operator restores the named path.

## X7 — Actions

A package names registry entries (`src/registry`, R-pm04-9), never ids or paths:

- `account`: a passwd line `name:x:uid:gid:gecos:home:shell` and a group line
  `name:x:gid:`. A shadow line `name:!:::::::` is added only where `etc/shadow`
  exists. These are whole-file replacements with backups inside the plan.
  - A name present with other ids refuses `account-conflict`.
  - An id used by another name refuses `account-id-conflict`.
  - An identical existing account is adopted.
  - Accounts are never deleted. They stay recorded after their package leaves.
- `directory`: an owned directory with the registry's mode and owner. Missing
  ancestors are made 0755 by root and owned with it. On removal it goes only when
  empty.
- `cache`: recorded as pending in the next generation and never executed
  (R-pm04-10).

## X8 — Failpoints

The shipped `paxage` passes an inert hook set. The test-only `paxage-failpoint`
(built beside it, never installed) reads `PAXAGE_FAILPOINT` (R-pm04-4):

- `trace` prints `FAILPOINT <name> [detail]` for every hook passed.
- `NAME:crash` ends the process by a runtime trap at NAME (exit 134, no
  unwinding).
- `NAME:eio` and `NAME:enospc` fail the step at NAME with `io` or `no-space`.
- `NAME:pause` prints `PAUSED NAME` and waits on `PAXAGE_FAILPOINT_FIFO`. The
  word `crash` there traps.
- `mark` writes one 512-byte record, `MARK <name> [detail]`, at offset 0 of
  `PAXAGE_FAILPOINT_MARK` at every hook. It fsyncs the record and prints it on
  stderr. On a block device served by the power-cut recorder (X11), each record
  is logged in order with the data writes.

## X9 — Ownership, configuration and removal

- **Conflicts.** A non-directory path owned by another package that stays
  refuses `file-conflict PATH owner=NAME`. An existing unowned non-directory
  refuses `unowned-collision PATH`. A co-owned directory with other metadata
  refuses `directory-conflict PATH`. There is no overwrite option.
- **Configs.** Each `configs` path keeps a baseline B (the packaged digest).
  Upgrade compares the live digest L with B and the new packaged digest N:
  - L absent: the file stays absent;
  - L == B: N is installed;
  - N == B, or L == N: L is kept;
  - otherwise L is kept and `PATH.paxage-new` = N is written as an owned
    proposal. An unowned file of that name refuses `proposal-exists`.
- **Removal.** Remove deletes owned paths whose live identity is the recorded one.
  A modified file, config or not, stays as a recorded residual. A directory goes
  when empty and no remaining package owns it. `--purge` deletes the named
  packages' residual configs, printing `purge PATH`. Removing a package another
  one requires refuses `required-by`.
- **Upgrade.** Upgrade replaces a modified non-config owned file; its preimage is
  backed up until the commit (R-pm04-11).
- **Reasons and orphans.** Named packages are explicit; their closure is
  dependency. `autoremove` previews the packages unreachable from explicit ones
  over required edges (provides included). `--yes` removes them, cycles
  included, in one generation.
- **Whole-snapshot upgrade.** `upgrade` resolves every explicit package against
  the trusted targets (R-pm00-5).

## X10 — The check

`tools/check-transactions` digests a root: every entry's path, type, mode, owner
(logical roots omit it), length, content SHA-256 or link target, and hardlink
class. Times are excluded, and so are `var/lib/paxage/trust/` and the cache.

For every hook a trace passes in install, upgrade and remove, the run is cut
there and `rescue` runs twice. It passes when:

- both rescues exit 0 and give identical digests;
- the second prints `nothing to do`;
- the digest equals the untouched root's before `commit-renamed` and the
  completed run's from it on.

The same check covers:

- every rescue hook, with the crash inside rescue;
- injected EIO and ENOSPC;
- ancestor swaps at each walk and temp step;
- concurrent writers and lock-owner death.

A failed write or sync names the host's reason when an operator can act on it:
`write PATH: no-space`, `sync PATH: io`, `backup-write <i>: no-space`, and
`restore-write PATH: no-space` from an undo. The injected rows name the same
words.

## X11 — The power-cut witness

`tools/check-powercut --vm` runs on Linux with KVM and the staged Ubuntu 24.04
guest. It cuts the power at every durable step and checks what the disk holds.

- **The recorder.** `tools/nbd-recorder` is written from the NBD protocol
  specification. The guest's data disk is its export, and the mark device is a
  second export. Every request on both is logged in arrival order: each write's
  offset, length and bytes, each flush, and the FUA flag.
- **Crash states.** For a cut at a log position, `tools/powercut-synth` keeps:
  - every write a flush before the cut covers, and every FUA write;
  - a chosen subset of the rest, each write whole or torn after a whole number
    of 512-byte sectors.

  The marks split each scenario into one window per step. Each window yields
  these states:
  - `before`: the durable state at the previous mark;
  - `after`: the durable state at this step's mark;
  - `after-all`: everything the step wrote;
  - `flushes`: the state at each flush inside the window;
  - `subsets`: four seeded subsets of one epoch's unflushed writes.
- **Scenarios.** Each runs on ext4 and on ext3, both mounted
  `data=ordered,noauto_da_alloc`:
  - install, upgrade and remove;
  - a rescue that undoes a crashed remove;
  - a rescue that finishes a committed upgrade;
  - two writers, cut while the owner holds the lock.
- **The check.** The guest rebuilds every state on a loop device, which replays
  the journal. It then runs `rescue` twice, remounts, and runs `e2fsck -fn`. A
  state passes when:
  - both rescues exit 0 and the second says `nothing to do`;
  - the three digests agree;
  - `verify` passes;
  - no transaction or temporary remains;
  - fsck is clean;
  - the digest is the old one in every window through `commit-written`, the new
    one from `commit`'s own state on, and either in between.
- **EIO.** The recorder fails the first write, then in a separate run the first
  flush, after the mark that precedes `backup:0`, `intent-written`,
  `apply:0:temp`, `generation` or `commit-written` in an upgrade, and
  `rescue:undo:0` in a rescue. The verb must exit nonzero, naming the error. The
  disk, preened as a boot would, must recover to the old tree twice.
- **ENOSPC.** A 32 MiB disk is filled while the upgrade pauses at `backup:0`,
  `apply:0:temp` or `generation`. The upgrade must exit 1 naming `no-space`. With
  the filler gone, rescue twice must give the old tree. The capacity check
  refuses a nearly full disk before any write.
- **Qualification.** ext2, and ext4 without a journal, refuse
  `unqualified-filesystem`.
- **The matrix.** `tools/check-transactions --all` runs as root in the guest on
  each filesystem.
