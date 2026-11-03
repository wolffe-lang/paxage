# CLI v0.1

## C1 — Names and working verbs

One binary, `larder`; `lrd` is a symbolic link with identical behavior.
Diagnostics start `larder:` regardless of invocation name. Usage names both.

- `version`: `larder 0.1.0 (lrd; format v1, pack and stage)`.
- `check-manifest FILE`: strict F2/F3 validation, exact-byte std SHA-256 and
  byte length. This does not authenticate a signer or a payload.
- `compare V1 V2`: V2 versions, normalized result -1, 0 or 1.
- `resolve --snapshot DIR --want SPEC [--want SPEC ...] [--json]` reads
  `DIR/snapshot.lrd`, emits a complete independently checked plan, or refuses.
  A spec is `NAME[@ARCH/SLOT][OPVERSION]`, OP one of `= != < <= > >=`;
  absent constraint means any. Defaults come from the snapshot. JSON has
  `status`, `selected`, `removals`, `nodes`, `explanation`. Removals identify
  old and replacing packages; text is deterministic. No root/cache/trust writes.
- `pack`, `verify-payload`, `stage`, `list-payload`: C4–C7 below.
- `--help` / `help`: usage, exit 0; `--version` aliases version.

## C2 — Refusals and exits

`install`, `remove`, `upgrade`, `sync` refuse individually by name:
`larder: VERB refused: mutation arrives in pm04`, exit 6. No argument enables
root mutation. `/var/lib/larder/`, `/var/cache/larder/`, `/etc/larder/` and
`<file>.larder-new` are reserved specification paths, never written here.

Exit 0 success; 1 malformed data, I/O or safety refusal; 2 usage; 3 proven
unsatisfiable snapshot; 4 budget exceeded (search incomplete); 5 independent
checker disagreement; 6 root mutation unavailable. Errors go to stderr and
successful data to stdout. No hidden transport, eval or promotion verb.

## C3 — Boundaries and fixtures

Both names share the same code. Fixtures check exact diagnostics/exits and
JSON/text, parser limits, versions, holds, ABI, conflicts and budgets. The largest
solver fixture has 24 packages; its time is reported, not gated. Payload vectors
are generated independently from POSIX.1-2017 and F6, not an archiver's verdict.
Temporary files are lane-local or checkout-local, never system temporary paths.

The std pin includes bounded incremental SHA-2. Large-file RSS qualification is
Linux-only under a 2 GiB address-space cap; the 1 GiB peak must grow by less than
8 MiB over the 64 MiB peak. Never run that measurement on the Mac.

## C4 — pack

`pack SOURCE TEMPLATE OUTDIR --epoch N`

SOURCE is a directory. TEMPLATE is a complete valid F3 manifest supplying its
identity/dependency/provenance fields; its files/installed estimates are replaced.
OUTDIR must exist. N is an explicit nonnegative epoch in seconds, never the clock.
Output is `OUTDIR/name-version.payload.tar` and `OUTDIR/name-version.manifest`;
existing output names refuse (`pack-output` / `pack-manifest-output`), never replace.

Paths sort by UTF-8 bytes; regular-file contents stream through std SHA-256.
Owners/groups normalize to numeric zero; modes and link targets are preserved.
The first encountered name for an inode supplies within-package hard links.
Headers use ustar name/prefix when representable; needed `path`, `linkpath`,
`size`, `mtime` extensions only, fixed epoch, zero padding, exactly two end blocks.
Source devices/FIFOs/sockets, reserved/unsafe paths, escaping links and permission
bits above 0777 refuse before output creation. Failures after output creation leave
partial files; a successful exit is required before using either output.

## C5 — verify-payload

`verify-payload FILE --length N [--manifest FILE]`

Strict F6 reader, no writes. N is required and must equal the actual regular-file
length. Checks framing, checksums, octal/decimal arithmetic, local extension
syntax/use, all F5 path/link relationships, entry/extension/installed-byte bounds,
zero padding, exact termination, and per-file digests. With --manifest, requires
complete F3 inventory agreement. Success: `payload ok entries=N bytes=N`.
This verb alone does not authenticate the whole blob or a signer.

## C6 — stage

`stage PAYLOAD --length N --sha256 HEX --manifest FILE --into DIR`

HEX is the externally expected lowercase whole-blob SHA-256 (not a signer/trust
check). Check the entire blob and byte length before parsing its headers or the
manifest and before any entry is written. A held payload fd is reused throughout.
Then validate the complete archive/inventory before extracting.

DIR must be empty, caller-owned, a real directory, not `/`, and not group/world
writable. Refuse detectable mount roots (different parent device or identical
parent inode); same-device bind mounts cannot be detected with this surface.
Euid 0 always refuses `privileged-staging-is-pm04-pm05`. This is not an installer.
Numeric archive ownership is logical metadata; on disk, staged entries belong to
the unprivileged caller. Privileged ownership application belongs to pm04/pm05.

The cwd pins the staging root after fd/path identity rechecks. Ancestors are
checked as directories, files created exclusively/no-follow, hard links made
after files, symlinks last. Never follow an archive-created symlink. Verify
installed contents, lengths, types, modes and link targets before success;
restrictive modes are applied after byte verification. No root promotion occurs.
Missing descriptor-relative operations still permit a third party with access
to swap an ancestor between check and use. This is not race-proof extraction
against another same-uid writer. Empty private staging and euid-0 refusal bound
that exposure, not eliminate it. Any failure leaves a partial staging tree; no
recursive cleanup is attempted and nothing outside it is removed.

## C7 — list-payload

`list-payload FILE --length N [--manifest FILE] [--json]`

Same strict reader as C5. Text rows are tab-separated type, decimal mode, length,
path, target. JSON is a path-ordered array of F5 records with keys `path`, `type`,
`mode`, `owner`, `group`, `length`, `sha256`, `target`. No writes. JSON inventory
is not signer authentication, and stage still independently verifies installation.
