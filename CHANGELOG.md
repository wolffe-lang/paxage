# Changelog

## 0.1.1 — 2026-11-21

- Rename two refusal codes to plain names: `live-root-is-pm05` is now `live-root-unsupported`, and `privileged-staging-is-pm04-pm05` is now `privileged-staging-refused`. Only the error text on stderr changes; exit statuses are unchanged. A script that matches the old text must match the new one.
- Document `privileged-trust-refused`, which every command that takes a trust directory returns at euid 0.
- Keep internal work ids out of tracked source, tools and docs: the public-text check now rejects them, and the docs and comments name layers instead.
- Add an experimental HTTPS transport for `bootstrap`, `update` and `fetch`, beside `file://`. It is tested only against local loopback repositories; no public repository is published, and signing is still test-only. Refuse a system clock earlier than the build.
- Raise the bounds to 768 targets and 256 installed packages, and hand the solver only the install closure, at most 64 packages. Past 64, install and upgrade refuse `snapshot-limit` and change nothing. The solver's search no longer allocates per node.
- Keep unknown target kinds under the signature and ignore them; reap a digest's failed part files before a new attempt.

## 0.1.0 — 2026-11-20

- Experimental 0.1.0 preview: file:// transport only and test-only signing; no network fetch, production signing, live-root writes or PAX root transactions.
- Provide manifest/version checks, bounded dependency planning, canonical payload packing and authenticated local-file staging. Linux synthetic-root transaction tests do not qualify production deployment.
- Require the full cross-platform gate at the exact tag before staging checksummed macOS arm64 and Linux x86-64 archives as a draft.
- Pin wolf 0.2.40, lupin 0.1.62 and the std tree that wolf 0.2.40 bundles. The release build initializes its own build root before it loads the compiler pins, and the release checks catch stale rename exceptions in the public-text census. No behaviour of the tool changes.
- Add the borrowed-handle canonical archive writer, with explicit caller-admitted resource profiles. Package defaults and canonical bytes are unchanged.

## Development history

- Add a borrowed-handle canonical archive writer with exact phase/length checks,
  error/abort latching, and explicit caller-admitted resource profiles. Package
  defaults and canonical bytes stay unchanged. Add independent framing,
  descriptor-lifetime, pipe/backpressure and sink-failure rows.

- Specify immutable package targets, strict literals, recipes and version v1.
- Add standalone bounded manifest parser and exact-byte std SHA-256.
- Add complete bounded resolver and independent checker for immutable snapshots.
- Add read-only paxage / pxg CLI with refusals for the mutating verbs.
- Gate formatting, build, unit properties and CLI fixtures on Linux x86-64 and
  macOS arm64.
- Add canonical restricted pax packing, strict streaming payload inspection and
  unprivileged authenticated-blob staging with inventory/mode/link/digest checks.
- Add independent hostile vectors, roundtrip/determinism, mutation, capped RSS
  and container interop/confinement gates; record the bounded std SHA-2 pin and
  require under 8 MiB RSS growth under a 2 GiB Linux cap. No threshold is waived.
- Keep live-root installs, trust/signing, transactions and fetch unavailable.
- Add durable transactions over a synthetic Linux root (TRANSACTIONS
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
- Add the power-cut witness (TRANSACTIONS X11). An NBD recorder logs the
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
- Pin wolf 0.2.40 and lupin 0.1.62, with std at the tree wolf 0.2.40 bundles
  (be1d10fa). That std carries the public-PKI TLS client (P-384 and RSA-PSS
  verification, path building). A row builds a probe against those modules and
  was red at the old pins. No behaviour changes.
