# pm02 — pack and stage

Materialised by the orchestrator from PR #4's body at the merge (trunk `c16048ca`, 2026-11-03).

Footprint: cross-cutting

## Forbidden

No live-root mutation/promotion, privileged run, install, signing, runtime fetch/HTTP, registry publication, labels, merge, tag or issue action. No foreign package-manager/archiver/compressor/signature implementation source read. Inputs: POSIX.1-2017 pax, FORMAT F1–F6, pm00 and owned Wolf, standard library and project code. GNU tar/bsdtar run only as unprivileged, network-disabled container black boxes; F6 supplies verdicts. SHA-256 is std's, never reimplemented.

The wrapper disallows the `.md` lane note. These five sections are its fallback; the coordinator writes `notes/pm02-pack-and-stage.md` at merge.

## Inputs, verified

Authority: pm02 contract at commit `914c529`; lane rules/additions, RULES §1–§10, pm rulings, pm00 design at pax `5da8daaf`. Base commit `eef47678ec62948fd45ef16e606739ec04d4200c`; baseline source/spec/harness/fixtures read.

Final head: `c16048ca9f8093c8cd581801ca7821256949fc00`. Wolf 0.2.36 (`5adf3d9`) / lupin 0.1.58 (`a5378e3`) unchanged; std explicitly pinned to merged `5b3a59942b2ee69b99682544341ce8a12c984e9e` (bounded SHA-2, unchanged API/digests). Compiler/interpreter archive digests unchanged.

## Prediction

Prediction committed first at `005b2ba`. Packer emits deterministic uncompressed payload plus regenerated manifest; reader rejects unsafe/non-profile bytes; stage authenticates the complete blob before parsing/writing, validates the full inventory, never follows archive-created links and verifies installed content/modes/types/targets. Stage euid 0 always refuses.

Final off-line plant: `pm02-plant-record-c16048c`, head `7009635e48046767bc5718e02cc987c3850bf1a3`, exactly one commit/file/hunk on the final green head. Local verified red contains `FAIL F6-traversal-refused`, unit exit 1, without a test assertion trap or added exec capability. Plant is pushed without a new PR, as directed. Historical draft #3 is superseded; its trap-only/compile-error reds are not the evidence. Disposition of historical #3 stays with the coordinator.

Selected commits:
- `456fd6c`, `22c2e34`, `24a63ba`, `0500f10`: reader, staging, writer, verbs.
- `ced18da`, `fc7629a`, `43c0219`: scoped/reused input buffers and bounded output rows.
- `9a44fe8`, `08970ed`, `e0c547b`: POSIX nonportable names, exact EOF, numeric contrast.
- `49db80b`, `78d3661`: named main-return failures and cold caches per entrypoint.
- `0dcd1cb`, `17b3fdc`: manifest preflight bounds and bounded std pin.

## Evidence index

CLI C4–C7 documents `pack SOURCE TEMPLATE OUTDIR --epoch N`, `verify-payload`, `list-payload [--json]`, `stage ... --length N --sha256 HEX --manifest FILE --into DIR`, exits and failure state. The short command is a link to the same executable. Mutating install/remove/upgrade/sync remain named exit-6 refusals. Numeric owners normalize to zero in package metadata; staged on-disk ownership remains the unprivileged caller's.

| Rule | Tests |
|---|---|
| F6 header layout, checksum/text/type/number/overflow | `src/payload_test.lu`, POSIX-derived independent byte generator in `tools/check-payload`; FIPS empty/abc/multiblock/million-a |
| Required/unused/unknown/duplicate/global extensions | independent vectors including UTF-8/space paths, linkpath, malformed decimal records and forbidden keywords |
| 1 MiB cumulative extensions, 100000 entries, 16 GiB installed, declared length | exact/over-bound headers, 100000 accept/100001 refuse, cumulative local-header cap, truncated block; guards precede large allocation |
| F5 paths/links/duplicates/overlapping types | traversal/absolute/reserved/overlong/control paths, symlink ancestor, escaping/absent hardlink, duplicate/file-dir collision |
| F6.1 strict end and padding | third zero block/extra byte => trailing-data; nonzero file padding refused |
| Canonical output | fixed input modes/umask, reverse physical insertion order, two equal payloads per host; raw cross-host cmp and CI artifact comparison |
| Exact source roundtrip | independent Python source/staged filesystem signatures compare paths, full modes, digests, link targets and hardlink equivalence classes |
| Auth before parsing/writes | wrong digest with malformed manifest/hostile payload; zero entries; inventory/length mismatch, nonempty/root/mount refusals |
| Packer refusals/bounds | FIFO/socket/read-only device/set-ID/sticky/escaping-link/reserved-path rows; node/byte-limit preflight before output creation |
| Confinement | exclusive/no-follow creation, ancestor rechecks, symlinks last, both-host parent listings; Linux read-only fixture parent with only staging writable |
| Mutation | seed 1347244082; four valid shapes; checksum-preserving mutations; 100000 inputs/host with per-input timeout and named refusal or independently checked staged tree |
| Allocation | digest-free production reader-only red/fixed row, max-inventory JSON red/fixed row, capped complete-reader 64MiB/1GiB gate |

### Final records and measurements

The recorder is exact `tools/gauntlet-record.sh` at `68dae09`. Records independently verify head/tree/time and step exits:
- Mac: `evidence/green-mac-c16048c.record`, worst 0, six steps; four loud Linux-only SKIPs (container, maximum-inventory measurement, reader RSS, full RSS). Large RSS never runs on Mac.
- Linux: `evidence/green-linux-c16048c.record`, worst 0, ten steps, all cold CLI/test builds plus fixture/fuzz/container/memory rows.
- Plant: `evidence/red-linux-7009635.record`, worst 1; literal named FAIL inside nonzero unit step, verified one-break ancestry.

100000 mutations: Mac 7125 verified trees / 92875 refusals; Linux 9359 verified trees / 90641 refusals. Both gates pass. Every END line is included in the hand-back, not inferred from wrapper success.

Linux under 2 GiB address-space cap:

| Measurement | 64 MiB KiB | 1 GiB KiB | Growth KiB |
|---|---:|---:|---:|
| Original client-only unscoped reader (no hash), red | 68264 | 1052628 | 984364 |
| Final client-only reader (no hash), green | 2820 | 3028 | 208 |
| Final full F6 reader with new std, green | 3144 | 3244 | 100 |

Unchanged requirement: full-reader growth <8192 KiB. Both full-reader digests equal independent sha256sum results. Original correct-hash Mac RSS was 1424016 / 13038720 KiB; that growing version was not rerun on Mac. Large fixtures are generated/used/deleted within each job.

Raw Mac/Linux canonical payloads compare byte-for-byte; each host's two insertion-order outputs also compare equal. Both SHA-256: `5c3e99659affd3370210b28108617b5f6f66773ead7956bd30634056ed9df9aa`. Raw copies: `evidence/canonical-{mac,linux}-c16048c.payload.tar`.

Contrast, never oracle: GNU pax and BSD zero-mtime archives accepted. BSD negative-time bytes at regular-header offset 1024, mtime offset 136 are `ffffffffffffffffffffff20`, despite a valid local `mtime=-1`; high-bit numeric encoding is forbidden by F6.2, so expected `header-number` refusal. No reader weakening. Source-byte log: `bsd-bytes.log`.

Jobs moved on coordinator instruction at 04:18:41Z from waiting 8–11 to 4–7: old waiters 1213590/2909496 verified WRITE*, terminated individually; sh35 holder untouched. Fresh logs `moved-current-69cbf69` / `moved-proof-832ec92` record the move. Obsolete main compile failures are not final-head evidence.

### Descriptor surface / seven issues for coordinator

Language citations: wolf-lang `7d026c6`, `spec/11-os.md`; std `78b9d3c`, `std/fs/fs.lu` for the inventory.

| Surface | Evidence / missing call and unblocked row |
|---|---|
| openat | Caller-facing dirfd form missing; held-parent stage opens (spec:4182, #707 surface) |
| mkdirat | Missing; existing path form spec:3519, std:1836; relative directory creation |
| symlinkat | Missing; path form spec:3545, std:1870; relative symlink creation |
| linkat dirfds | Missing; path fs_link internally uses linkat, spec:3573–3592, std:1906; confined hardlink source/destination |
| fstatat AT_SYMLINK_NOFOLLOW | Missing; path lstat spec:3371–3440, std:1309; relative ancestor rechecks |
| O_DIRECTORY | No exposed open flag; internal sync_dir use spec:3755–3766 is not a walk primitive |
| fchmod | Missing; path set_mode std:1730; spec:4181–4197 leaves handle form undone; race-free mode application |
| O_NOFOLLOW | Available final component only, flag 16: spec:3876–3890, std:2209/:2253 |
| Full fd metadata | Available device/inode/type/mode: spec:3971–4007, std:2331 |
| Directory fsync | Available via fs_sync(fd), spec:3747/std:2166; Unix directory opens spec:3001; path sync_dir std:2194 |

Each missing row is an issue title/call/unblocked project row; coordinator files seven, including #707 extension. No shell workaround. Remaining race: a third party with access can swap an ancestor between check/use, and final-name chmod can race without fchmod. Pinned cwd, caller-owned empty private stage and euid-0 refusal bound but do not eliminate it. Same-device bind mounts are undetectable. A failed stage leaves its partial tree; no recursive cleanup outside it and no promotion.

### Runtime and rulings

Three-line trap/normal-return witnesses are in `tests/runtime/`; runner builds both cold. On Mac and Linux wolf 0.2.36, preceding stderr is present, assert message absent. No stderr-loss bug reproduced; coordinator filed the real assert-message defect. Only the project's own failure harness changed.

- The incremental-API fallback was inapplicable: incremental std API exists.
- The selected approach was implemented via merged std pin; no interim bound/waiver or local SHA implementation.
- The selected approach was implemented as F6.1 strict EOF. F6.2 names the existing binary-number refusal.
- Verb flags and explicit epoch are engineering choices, documented in CLI.

## Done-when

- [x] Prediction before implementation; chunk commits; private main/isolated one-break plant.
- [x] Packer, strict reader, unprivileged stage and both CLI names; README/CLI/CHANGELOG refreshed.
- [x] Cold CLI/every test entrypoint on both hosts; independent vectors, exact roundtrip, 100000 mutations each.
- [x] Capped raw-reader/inventory red/fixed proofs, full RSS green, black-box contrasts and confinement.
- [x] Raw four-payload byte identity, final-head green records and named local plant red.
- [x] Final push, main PR/run read once and exactly one local-record audit.

Main PR #4. CI run 41580130756 was in progress at the one audit. Audit verified both local records, one-hunk plant, fast-forwardability, head, sections and cited SHAs; final line: `AUDIT FAIL (footprint: cross-cutting)` solely because no cross-cutting CI run had completed yet. No audit rerun or CI polling. The initial immediate run lookup returned no created run; the required audit supplied this run ID.
- [ ] Cross-cutting single-tier CI green before merge; coordinator watches, no lane polling.

No root install, transaction, signer/trust implementation or transport is claimed. No issue filed/closed by lane. Superseded draft plant #3 remains for coordinator disposition.

