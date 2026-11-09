# pm04a — Linux transactions

Footprint: cross-cutting (the toolchain pin, tools and the gauntlet).

pm04 was split at its prediction, as ruled (R-pm04-15 A). pm04a is everything
except the QEMU power cuts: the lock, qualification, the database and
generations, install, upgrade and remove, config and accounts, orphans,
status, verify and rescue, and the failpoint matrix. pm04b is the journalled-guest
power-cut witness, real EIO and ENOSPC, and the ext2 refusal in a VM; M-PM1 is
claimed at pm04b's merge, not here.

## Forbidden

- Private repository; never named in public text. The one upstream issue,
  wolf-lang#1084, is plain prose with no project or host names.
- The clean room. Sources were documentation, specifications and man pages only:
  rename(2), fsync(2), flock(2), openat(2), statfs(2), proc(5) mountinfo, the sysfs
  `/sys/dev/block` ABI, jbd2's procfs files, ext4's documented journalling,
  passwd(5), group(5), shadow(5), and pacman's and dpkg's documented behaviour.
  No package manager's, archiver's or filesystem's source was read. wolf's own
  `spec/11-os.md` (the org's) supplied the descriptor-walk surface.
- Never host `/`: every root is synthetic (`--root`), and `/` refuses by name.
- Nothing in `/tmp`; signals never sent to a host process (the owner-death row
  ends the holder by its own trap); kasumi and the 860 untouched; never signed on
  hasu. No label, merge, tag or close; no attribution trailers.

## Inputs, verified

- Contract: planning `ae10893c`, `sprints/pm/04-linux-transactions`; lane rules 1031
  with every Added item; `sprints/pm/index.md`. The design is pax trunk
  `db516c69` `notes/pm00-the-design.md` (R-pm00-6, -9, -10, the inventory, the
  pm04 row).
- Base larder `d5017a210424`, branch `pm04`.
- Toolchain (R-pm04-1 A): wolf 0.2.38 (`95ae0827`) and lupin 0.1.60 (`17bd5223`).
  Each archive's SHA-256 was read twice, once from the release API and once from a
  downloaded copy:
  - wolf darwin `66a2c313…`, wolf linux `8447a579…`;
  - lupin darwin `f3cae16f…`, lupin linux `e7d4c4f1…`.

  std stays at `23baa1a`; the pin compiled unchanged and the existing units and
  CLI fixtures pass on both hosts. 0.2.38 adds the ten descriptor calls (s277).
  Still absent: renameat, readlinkat, fchownat and fchdir, filed as
  wolf-lang#1084.
- Guest image for pm04b, staged and digest-checked on hasu; not used here: Ubuntu
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
    would need the `exec` capability larder never declares.
  - `rescue-foreign-temp` was not needed: only larder's own temporary names are
    removed.
- **Found.**
  - pm03's `repo keygen` refuses root by design. A root take publishes its fixture
    repository as an unprivileged uid and uses root only for the root verbs.
  - A directory shared by two removed packages was planned twice (red in
    orphan-cycle); fixed.
  - A modified hardlinked file must keep its link in the undo record; fixed.

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
  development root) and hasu natively.
- **Root (owners applied).** In a rootless container on hasu: `px75-ubuntu:2`, the
  tree copied to the same ext4 bind mount, a tmpfs for the unqualified row. On CI
  Linux the same take runs under passwordless `sudo`.
- **Skips.** The Mac prints SKIP for the root take and the tmpfs refusal.

The final-head records (Linux on hasu under its block's two locks, the Mac behind
its lock) and the plant record are cited in the PR. They are not repeated here,
so this note does not have to change after the head it describes.

The plant is `pm04-plant-*`, one commit, one file and one hunk on the final head.
Undo skips restoring a replaced regular file. Predicted red row:
`crash-upgrade-apply:0:renamed`, where rescue refuses `rescue-unknown-state` after
undo and the root is neither old nor new.

### Rulings (all A, 2026-11-09 ~02:0xZ)

R-pm04-1 pin 0.2.38; R-pm04-2 pinned working directory and the upstream issue
(wolf-lang#1084); R-pm04-3 only rescue acts on a pending transaction; R-pm04-4 a
test-only failpoint executable; R-pm04-5 privileged and logical roots; R-pm04-6
ext3/ext4 with an active journal, macOS development roots; R-pm04-7 `/` refused;
R-pm04-8 pm02's stage as root only into the transaction directory; R-pm04-9 a
compiled registry; R-pm04-10 cache actions pending only; R-pm04-11 the
modified-file rules; R-pm04-12 F2 records and a framed intent; R-pm04-13 exits 7, 8
and 9; R-pm04-14 the power-cut model (pm04b); R-pm04-15 the split.

### Limits, stated

- pm03's trust and cache I/O is path-based. Under the root lock, larder brackets
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
