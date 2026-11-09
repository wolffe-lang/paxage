# pm04b — recovery and power cuts

Footprint: cross-cutting (the gauntlet, `tools/fetch-toolchain` and the
container step change; the CI runs the gauntlet).

pm04b is the second half of M-PM1, split at pm04's prediction (R-pm04-15 A). It
adds the durability witness that a process-crash matrix cannot be: power cuts on
a journalled filesystem in a KVM guest, real device errors, a really full disk,
and the refusal of an unjournalled filesystem. Its prediction is
`prediction-pm04b.txt` (`d18469b`), committed first with every row red.

## The claim

This is the one place that states M-PM1's claim (R-pm04b-12, pending the
maintainer's ruling; the wording is provisional and changes only here):

> larder's transactions on a synthetic Linux root, from a `file://` repository,
> reach the old or the new generation only, recovered twice identically, after a
> crash at any transition, a crash during rescue, and a power cut before or
> after any durable step, with torn sectors. The power cuts are witnessed on
> ext4 and ext3 with jbd2, `data=ordered`, under QEMU/KVM, with every block
> write the guest issued recorded. The live root (`--root /`) is pm05's and is
> not claimed.

## Forbidden

- Private repository; never named in public text. No upstream issue was needed.
- The clean room. Sources: the NBD protocol specification (`doc/proto.md`,
  sha256 `4b4eda49…`), QEMU's documentation, fsync(2), rename(2), mount(8),
  ext4(5), e2fsck(8), mkfs.ext4(8), the kernel's kernel-parameters document,
  the ALICE and CrashMonkey papers, and pacman's and dpkg's documented
  behaviour. No package manager's, archiver's or filesystem's source, and no NBD
  server's or client's source.
- Never host `/`. Nothing in `/tmp`, with one slip, stated: three public files
  (Ubuntu's SHA256SUMS, its unpacked SUMS and the UEC signing key) were copied
  to satoyama's `/tmp` for about a minute on 11-09 at 10:07Z, and removed at
  once. Never signed on hasu. kasumi and the 860 untouched. On satoyama: the
  GPU, llama-rpc, ollama and the FreeBSD VM untouched; podman only through
  `satoyama-env/bin/podman` (scratch stores under the lane for the cold-store
  rows). No label, merge, tag or close; no attribution trailers.

## Inputs, verified

- **The guest**: Ubuntu 24.04 cloud image, release 20261017 (the image, the
  generic kernel and initrd). SHA256SUMS and unpacked/SHA256SUMS:
  - fetched on hasu (11-08), the Mac and satoyama (11-09), byte-identical;
  - each with a good signature from the UEC Image Automatic Signing Key,
    D2EB44626FDDC30B513D5BB71A5D6C4C7DB87C81, checked with gpgv against a
    lane-local keyring.
  The three files' digests are pinned in `tools/check-powercut`
  (`04e8f246…`, `41ba36d8…`, `bf276ffc…`) and re-read by `vm-inputs-digests`
  on every take.
- **GNU time on satoyama** (chunk-rss and rss resolve it from PATH; satoyama has
  none): Arch's `extra/time` 1.10-1, its sha256 (`fbbd81a7…`) matching the
  local sync database, with a good packager signature against the Arch keyring
  (dearmored under the lane). Unpacked to the lane's `hostbin/time`
  (`ccc57656…`), which the take puts first on PATH. Nothing installed.
- **Toolchain**: unchanged from pm04a (wolf 0.2.38, lupin 0.1.60, std 23baa1a),
  staged on satoyama from the digest-checked archives.
- **The guest binaries**: built in `localhost/px75-ubuntu:2` (Ubuntu 24.04.5,
  glibc 2.39, the guest's own release; the same image id on hasu and satoyama)
  from the take's own commit and toolchain; `vm-binaries-match` compares the
  guest's digests with the build's.

## What was built

- `tools/nbd-recorder`: an NBD server written from the specification (fixed
  newstyle; EXPORT_NAME, INFO, GO, LIST, ABORT; READ, WRITE, FLUSH, DISC;
  simple replies). It logs every request on its two exports in arrival order,
  with each write's bytes. `--eio TEXT:write|flush` answers the first such
  request after a named mark with NBD_EIO (R-pm04b-1, provisional: the EIO rows
  are one function, `eio_runs`, so a different ruling replaces only it).
- `tools/powercut-synth`: crash states from a log (section 1 of the
  prediction), keyed so identical states are checked once.
- `tools/powercut-guest`: the guest's run, eio and check phases.
- `tools/check-powercut`: the host rows (recorder protocol, synthesis, the mark
  action) and the VM driver.
- The `mark` failpoint action (TRANSACTIONS X8).

## Found by the witness

- **Undo's cleanup order.** A power cut inside the removal of an undone
  transaction's tree could leave the backups gone and the intent in place. The
  next rescue then tried to undo again and refused `rescue-missing-backup`
  (`powercut-ext4-rescue-undo-rescue:cleanup:dir-flushes`, red in the dev pass;
  `evidence/dev-red-ext4-discard-enospc.log` on satoyama, sha256 `78e1b6dd…`).
  A process crash cannot reach that state: no hook sits between the two
  removals. Fixed in `2d938f6`: the intent goes first, durably.
- **A real full disk was misnamed.** A failed copy returned an empty digest, so
  ENOSPC read as `live-changed`, `content` or `rescue-missing-backup`
  (`vm-enospc-ext4-upgrade-*`, red in the same pass). The rescues afterwards
  were already correct. Fixed in `b90e89a`: writes, copies and syncs name the
  host's reason (`no-space`, `io`).
- **The container step on a cold podman store** (the BACKLOG item, R-pm04b-9).
  Red first on satoyama with a scratch store under the lane: under the
  step-wide 2 GiB cap, podman's pull itself ran out of address space
  (`evidence/cold-container-red-0bf1c2a.log`, `6a5566bc…`). Warming alone was
  not enough: with the image warm, a later podman call ran out the same way
  (`cold-container-warm-only-red.log`, `4022ef91…`). Fixed in `e3f13e9`: a warm
  step pulls and copies under its own bound, and the cap applies inside the
  container (`ulimit -v`) to the archivers and larder, not to podman. Green on
  a fresh cold store (`cold-container-green.log`, `fe7987fc…`).
- **fetch-toolchain's 20-second retry span** (the BACKLOG item, R-pm04b-8): red
  first with a loopback 504 origin (`be44b32`), then `fetch_release`'s growing
  backoff (`2b1c393`).

## Measured (development passes on satoyama, light slot, before the records)

The full witness on each filesystem takes about 5.5 minutes, so one take holds
both in full (R-pm04b-5: no chunking was needed). Per filesystem:

- **Guest boots.** A run boot with the matrix takes 153 s, each of the 12 EIO
  boots 3 s, and the check boot 80 s.
- **Planned crash states.** After deduplication, ext4 has 788 scenario states
  (install 257, remove 130, rescue-undo 73, upgrade 153, rescue-finish 36,
  concurrent 139) plus 12 EIO states. ext3 has 776 plus 12. Each filesystem
  judges 878 rows.
- **Logs.** A run log holds about 2,550 data writes (42 MB) and 2,040 flushes.
  QEMU's NBD client sent no FUA writes: virtio-blk has no FUA, so the guest
  flushes instead.
- **The matrix in the guest.** pm04a's rows pass 941 rows as root on each
  filesystem, three more than pm04a's 938: the crash rows at the new
  `rescue:cleanup:intent` hook.
- **Results.** ext4 had 928 PASS and ext3 925, with 0 FAIL on each
  (`evidence/dev-green-ext4-full.log` `9e16ebcd…`, `dev-green-ext3-full.log`
  `99c59cf7…`).

## The plant

`pm04-plant-*`: `write_new` skips the fsync of `current.<t>` (one hunk in
`src/txn/txn.lu`). In development the ext4 witness went red by name, as
predicted:

> `FAIL powercut-ext4-upgrade-commit-after … larder: rescue-ambiguous-generation (current-invalid)`

The rename is durable and the zero-length `current` survives the cut
(`noauto_da_alloc`, delalloc). Every post-commit window of the three verbs went
red (96 rows), while every window before the commit stayed green. The
process-crash matrix's `crash-upgrade` rows pass under the plant: a process
crash keeps the page cache. That contrast is the plant's point
(`evidence/dev-plant-ext4-quick.log`, `17514228…`).

## Limits, stated

- The synthesized states model a device that keeps every write a flush covered
  and any subset of the rest, torn at 512-byte sectors. They do not model a
  device that loses a flushed write. That device lies, and no transaction can
  survive it.
- The four seeded subsets per window are a sample, not every subset. The
  before, after, after-all and flush states are exhaustive per window.
- EIO is injected at the recorder, one request per run (R-pm04b-1, provisional).
- CI runs the host rows and SKIPs the VM step (R-pm04b-7); the witness runs in
  local KVM takes.
