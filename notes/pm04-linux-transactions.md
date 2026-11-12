# pm04a — Linux transactions

Footprint: cross-cutting (the toolchain pin, tools and the gauntlet).

pm04 was split at its prediction, by design. pm04a is everything
except the QEMU power cuts: the lock, qualification, the database and
generations, install, upgrade and remove, config and accounts, orphans,
status, verify and rescue, and the failpoint matrix. pm04b is the journalled-guest
power-cut witness, real EIO and ENOSPC, and the ext2 refusal in a VM; M-PM1 is
claimed at pm04b's merge, not here.

## Forbidden

- The one upstream issue,
  wolf-lang#1084, is plain prose with no project or host names.
- The clean room. Sources were documentation, specifications and man pages only:
  rename(2), fsync(2), flock(2), openat(2), statfs(2), proc(5) mountinfo, the sysfs
  `/sys/dev/block` ABI, jbd2's procfs files, ext4's documented journalling,
  passwd(5), group(5), shadow(5), and pacman's and dpkg's documented behaviour.
  No package manager's, archiver's or filesystem's source was read. wolf's own
  `spec/11-os.md` (the org's) supplied the descriptor-walk surface.
- Never host `/`: every root is synthetic (`--root`), and `/` refuses by name.
- Nothing in `/tmp`; signals never sent to a host process (the lock-holder-death row
  ends the holder by its own trap); the FHS Linux host and the 860 untouched; never signed on
  the NixOS Linux host. No label, merge, tag or close; no attribution trailers.

## Inputs, verified

- Contract: commit `ae10893c`; the design is pax trunk
  `db516c69` `notes/pm00-the-design.md` (the inventory and the pm04 row).
- Base commit `d5017a210424`, branch `pm04`.
- Toolchain: wolf 0.2.38 (`95ae0827`) and lupin 0.1.60 (`17bd5223`).
  Each archive's SHA-256 was read twice, once from the release API and once from a
  downloaded copy:
  - wolf darwin `66a2c313…`, wolf linux `8447a579…`;
  - lupin darwin `f3cae16f…`, lupin linux `e7d4c4f1…`.

  std stays at `23baa1a`; the pin compiled unchanged and the existing units and
  CLI fixtures pass on both hosts. 0.2.38 adds the ten descriptor calls (s277).
  Still absent: renameat, readlinkat, fchownat and fchdir, filed as
  wolf-lang#1084.
- Guest image for pm04b, staged and digest-checked on the NixOS Linux host; not used here: Ubuntu
  24.04 release-20261017, `.img` `04e8f246…`, vmlinuz `41ba36d8…`, initrd
  `bf276ffc…`.

## Prediction

`prediction-pm04.txt` (`6f3f6f7`) came first. The rows went red at the base (`da5f504`,
`e80e956`): 33 row groups FAIL on the Mac, because `init` was an unknown verb,
install exited 6, and the failpoint executable did not exist. Scored against
what was built:

- **As predicted.** The state machine and every named hook. The lock inode. The
  generations and `current` as the only commit authority. Undo shared by the
  in-process rollback and rescue. The three-way config rule. Residuals and purge.
  The orphan cycle. Exits 7, 8 and 9. `--root /` refused. The "old or new,
  recovered twice identically" check. All passed in development runs, the root
  take included.
- **Changed.**
  - Manifests live in each generation (`generations/<N>/manifests/`), not a shared
    `objects/` directory, so an undone generation leaves nothing behind.
  - The stage is not fsynced: nothing is ever redone from it.
  - A `capacity` step (space and inodes for backups, payloads and new files, with
    headroom) refuses before the first durable write.
  - The failpoint crash is a runtime trap (exit 134), not an exit call: `os_exit`
    would need the `exec` capability the program never declares.
  - `rescue-foreign-temp` was not needed: only the program's own temporary names are
    removed.
- **Found.**
  - pm03's `repo keygen` refuses root by design. A root take publishes its fixture
    repository as an unprivileged uid and uses root only for the root verbs.
  - A directory shared by two removed packages was planned twice (red in
    orphan-cycle); fixed.
  - A modified hardlinked file must keep its link in the undo record; fixed.
  - The CLI fixture (`tools/check-e2e`) still expected:
    - the old version line and usage;
    - install, remove and upgrade refused with exit 6.

    The first final take (at `60c756b`) went red at `END cli exit=1` on the NixOS Linux host and on
    the Mac; both records are void. The fixture now expects:
    - the new line;
    - `sync` refused by name;
    - `root-missing` and `live-root-is-pm05` for the three root verbs;
    - usage errors for root verbs without `--root`.
  - pm02's container rows had been recorded only on the FHS Linux host. On the NixOS Linux host
    (NixOS) they failed twice:
    - podman's first `--userns=keep-id` use of the archlinux image builds an
      ID-mapped layer copy. Under the step's 2 GiB address-space cap that copy hit
      `pthread_create` EAGAIN, then the test's 60 s limit. It was warmed once
      outside the gauntlet (135 s).
    - The binary built on the NixOS Linux host's loader lives under `/nix/store`, so it could not
      start in the container. The rows now mount `/nix/store` read-only where it
      exists; no verdict changes.
    - The two RSS steps ran `/usr/bin/time`, which NixOS does not have. They now
      resolve GNU time from PATH and check that it really is GNU time (`-v`).
    - GNU time forks the measured child. Because ru_maxrss survives exec, the
      child's peak starts at time's own RSS, so each reading is max(floor, peak).
    - The floor is recorded as time's own VmHWM, read from `/proc/<pid>/status`
      while it waits on a one-second child. VmHWM is per process image, so it is
      time's peak alone. (A first try used `time -v true`. That measured NixOS's
      multi-call `true`, 4.1 MiB, above the probe; it was replaced.)
    - Each step now requires the 64 MiB reading to be strictly above the floor.
      Both readings are then true peaks, and the floor cancels exactly in the
      1 GiB − 64 MiB difference the gate checks. If that ever fails, the step
      refuses `floor-masks-peak` rather than passing.
    - On the NixOS Linux host (light slot, under the 2 GiB cap): floor 1692 and 1688 KiB. Chunk
      reader 2704 → 2752 KiB (+48); full reader 3180 → 3268 KiB (+88).
  - The CI root take (`sudo` on GitHub's Linux runner) went red at the fixture
    publication. The harness dropped those commands to uid 65534, but the runner
    keeps the checkout under its home directory (0750, owned by the runner), so 65534 could
    not execute the built binary in `target/bin` (EACCES).
    - The NixOS Linux host's container take never saw it. It copies the tree under podman's
      bind-mount path, whose directories are 0755, and that copy is root-owned
      with 0755 binaries.
    - It reproduced red in `localhost/pm04-sudo:1`, a lane image (px75 plus `sudo`,
      a uid-1001 `runner`, a 0750 home, passwordless sudo) running
      `tools/check-transactions-privileged` with `GITHUB_ACTIONS=true` from
      the runner’s checkout path: the same `PermissionError` on the same path.
    - The fixture is now published as the checkout's owner (sudo's caller, then
      65534 only for a root-owned checkout), behind a named preflight
      (`fixture-identity-reach`). Both routes then pass 938 rows: the sudo route as
      uid 1001, the container route as 65534.
  - One dev job on the NixOS Linux host (block A, then slot, then light) ran every step the Mac
    skips. trust-openssl-writer runs only on the FHS Linux host, off limits here, and prints
    its SKIP.

## Evidence index

| Clause | Rows (tools/check-transactions; src/transaction_test.lu) |
|---|---|
| X1 roots and privilege | init-root, init-refuses-existing-state, live-root-refused, install-owner-applied (root take) |
| X2 qualification | fs-unqualified-refused (a tmpfs root on Linux, container and native); ext2 is pm04b's |
| X3 descriptor walk | race-ancestor-{usr,usr-share,usr-share-alpha}-{walk,temp}: path-race, outside sentinel unchanged, rescue refuses while swapped, restores after; race-state-ancestor; X3-walk-paths |
| X4 database | status-generation-zero, install-explicit-database, X4-database-roundtrip, X4-current-roundtrip and the refusals |
| X5 transaction | crash-{install,upgrade,remove}-every-transition-hooked, then crash-VERB-HOOK for every hook a trace passes: cut, mutation-refused (exit 8), rescued twice to the expected digest |
| X6 rescue | crash-rescue-HOOK for every rescue hook, rescue-nothing-to-do, status-recovery-needed, mutation-refused-recovery-needed, rescue-unknown-state (zero writes), rescue-missing-backup, rescue-malformed-intent |
| X7 actions | install-account, install-account-conflict, install-directory-action, install-cache-pending, remove-account-retained |
| X8 failpoints | X8-failpoint-name, -actions, -inject; every crash and injection row; eio-VERB-HOOK and enospc-VERB-HOOK at capacity (zero writes), backup, intent-written, generation, commit-written, a temp step and a renamed step |
| X9 ownership and config | install-file-conflict, install-unowned-collision, install-shared-directory, install-noop, dry-run-no-writes, upgrade-replace-add-drop, upgrade-replaces-modified, config-local-unchanged-replaced, config-upstream-unchanged-kept, config-both-changed-proposal, config-locally-deleted-stays, config-proposal-exists, remove-owned-only, remove-modified-residual, remove-config-residual, remove-purge, remove-required-refused, orphan-cycle-preview, orphan-cycle-collected, verify-clean, verify-drift |
| X4 lock | lock-persistent-inode, lock-contention (exit 7 in under 5 s, rescue also 7, status read-only), lock-owner-exit (the holder traps; the next writer locks at once; no PID file), lock-symlink-refused, lock-missing-refused |

Takes:
- **Logical (owners not applied).** As the caller on every host: the Mac (APFS
  development root) and the NixOS Linux host natively.
- **Root (owners applied).** In a rootless container on the NixOS Linux host: `px75-ubuntu:2`, the
  tree copied to the same ext4 bind mount, a tmpfs for the unqualified row. On CI
  Linux the same take runs under passwordless `sudo`.
- **Skips.** The Mac prints SKIP for the root take and the tmpfs refusal.

The final-head records (Linux on the NixOS Linux host under its block's two locks, the Mac behind
its lock) and the plant record are cited in the PR. They are not repeated here,
so this note does not have to change after the head it describes.

The plant is `pm04-plant-*`, one commit, one file and one hunk on the final head.
Undo skips restoring a replaced regular file. Predicted red row:
`crash-upgrade-apply:0:renamed`, where rescue refuses `rescue-unknown-state` after
undo and the root is neither old nor new.

### Rulings (all A, 2026-11-09 ~02:0xZ)

The selected design pins 0.2.38; uses a pinned working directory (with
wolf-lang#1084 filed upstream); permits only rescue to act on a pending
transaction; uses a test-only failpoint executable; tests privileged and logical
roots; qualifies journalled ext3/ext4 and macOS development roots; refuses `/`;
runs pm02's stage as root only inside the transaction directory; uses a compiled
registry; leaves cache actions pending; applies the modified-file rules; uses F2
records and a framed intent; and assigns exits 7, 8 and 9. The power-cut model
is covered by pm04b, the second part of the split.

### Limits, stated

- pm03's trust and cache I/O is path-based. Under the root lock, the package manager brackets
  it with a check of the state directory's identity by handle and by path. A
  writer who can swap `ROOT/var/lib` is the root's owner.
- Process cuts cannot show a missing barrier; pm04b's power cuts can.
- macOS durability is not claimed.

## Done-when

- [x] Prediction and red rows first; pin bumped; upstream issue filed (wolf-lang#1084).
- [x] Lock, qualification, database and generations, install/upgrade/remove,
  config, accounts and directories, pending caches, orphans, status/verify/rescue.
- [x] Crash at every hook of install, upgrade and remove; crash at every rescue
  hook; injected EIO and ENOSPC; ancestor races; lock contention and owner death.
- [x] Logical takes on both hosts; the root take in a container.
- [x] README, CLI, CHANGELOG, CLAUDE.md and docs/TRANSACTIONS.md current. README
  read: the capability statement, the verb list and the test paragraphs moved and
  were refreshed.
- [ ] Final-head records, the plant record, the PR and the one audit: in the PR.
- [ ] pm04b: power cuts, real EIO/ENOSPC, the ext2 refusal, the missing-barrier plant.
