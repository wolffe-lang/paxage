# Changelog

## Unreleased — 0.1.0

- Add a borrowed-handle canonical archive writer with exact phase/length checks,
  error/abort latching, and explicit caller-admitted resource profiles. Package
  defaults and canonical bytes stay unchanged. Add independent framing,
  descriptor-lifetime, pipe/backpressure and sink-failure rows.

- Specify immutable package targets, strict literals, recipes and version v1.
- Add standalone bounded manifest parser and exact-byte std SHA-256.
- Add complete bounded resolver and independent checker for immutable snapshots.
- Add read-only paxage / pxg CLI with pm04 mutation refusals.
- Gate formatting, build, unit properties and CLI fixtures on Linux x86-64 and
  macOS arm64.
- Add canonical restricted pax packing, strict streaming payload inspection and
  unprivileged authenticated-blob staging with inventory/mode/link/digest checks.
- Add independent hostile vectors, roundtrip/determinism, mutation, capped RSS
  and container interop/confinement gates; record the bounded std SHA-2 pin and
  require under 8 MiB RSS growth under a 2 GiB Linux cap. No threshold is waived.
- Keep live-root installs, trust/signing, transactions and fetch unavailable.
- Add durable transactions over a synthetic Linux root (pm04, TRANSACTIONS
  X1–X10). The verbs are init, status, verify, install, remove, upgrade,
  autoremove and rescue. They take a persistent lock inode, refuse an
  unjournalled filesystem, and write only through the descriptor walk. Each
  transaction keeps immutable generations, a framed intent with backups and an
  undo shared with rescue. Account, directory and pending-cache actions come from
  a compiled registry. Configs follow a three-way rule; removal keeps residuals;
  orphans are collected together after a preview. Exits 7, 8 and 9 are new;
  `sync` stays refused.
- Pin wolf 0.2.38 and lupin 0.1.60 (the descriptor walk); std stays at 23baa1a.
- Add a test-only failpoint executable and the transaction rows. They cover a
  crash at every hook, a crash during rescue, injected EIO and ENOSPC, ancestor
  races, lock contention and owner death. The check is that the root reaches the
  old or the new generation, recovered twice identically.
- Add the power-cut witness (pm04b, TRANSACTIONS X11). An NBD recorder logs the
  guest's block writes and flushes, and crash states are synthesized at and
  between every durable step, with torn sectors. On ext4 and ext3 in a KVM
  guest, each state must recover to the old or the new generation, twice
  identically and fsck-clean. The witness also covers real EIO and ENOSPC, two
  writers, the ext2 refusal and the transaction rows run in the guest.
- Undo removes the intent first, durably. A power cut during an undo's cleanup
  could leave the backups gone and the intent in place, and the next rescue then
  refused `rescue-missing-backup`.
- A real full disk or I/O error names its reason (`no-space`, `io`). Before
  this, a failed copy read as `live-changed`, `content` or
  `rescue-missing-backup`.
- `fetch-toolchain` retries a release download with a growing backoff, for up
  to 10 minutes. The container step warms its image, uncapped, before the capped
  run.
- Rename the package manager paxage (`pxg`), formerly larder (`lrd`), on 2026-11-09.
  The executables, the `paxage:` prefix, `ROOT/var/lib/paxage/`, `ROOT/var/cache/paxage/`,
  the reserved `/etc/paxage/`, `.paxage-new`, the intent header, the `.pxg` data files
  and the `PAXAGE_*` variables follow. No former name is accepted as an alias, and
  nothing migrates: nothing was ever installed under the former paths.
