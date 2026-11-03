# Package format v1

## F1 — Immutable targets

A package consists of `name-version.manifest`, `name-version.payload.tar`, and
`name-version.buildinfo`. External authenticated index records bind each target's
exact SHA-256 and byte length; no self-referential archive hash is embedded.
Logical names acquire TUF consistent-snapshot prefixes in pm03. pm01 parses data
only: no trust claim, archive reader, root mutation, signing or fetch operation.

## F2 — Literal data and rejection names

This is a strict subset of Wolf grammar/1 named struct literals, list literals,
plain string literals, decimal integers and booleans, parsed without a compiler.
A document is one named struct literal. Names and field keys are ASCII identifiers
`[a-z_][a-z0-9_]*`. Structs use `tag { key: value, ... }`; lists use `[value, ...]`.
Commas are required between members; a single trailing comma is permitted.
Whitespace is ASCII space, tab, CR and LF. No BOM, comments, expressions, calls,
interpolation, floats, null, negative integers, alternate integer bases or raw
strings. Escapes permitted: `\\`, `\"`, `\n`, `\r`, `\t`; literal braces must be
`{{` or `}}` as in Wolf. Other escapes and control bytes are refused. UTF-8 must
be shortest-form scalar encoding, excluding surrogates and values above U+10FFFF.

Rejections: `bad-utf8`, `byte-limit` (1,048,576), `depth-limit` (32 containers),
`node-limit` (16,384 values), `member-limit` (4,096 per container), `string-limit`
(65,536 decoded bytes), `integer-overflow` (maximum 9,223,372,036,854,775,807),
`duplicate-key`, `unknown-field`, `missing-field`, `field-type`, `bad-schema`,
`expression`, `interpolation`, `comment`, `bad-escape`, `control-byte`, `syntax`,
`trailing-data`. Unknown fields, not merely unknown mandatory ones, reject;
there is no optional extension namespace in v1. `features` must be empty,
otherwise `unsupported-feature`. Hash the original input bytes, never a reprint.
The file reader stops at byte-limit+1 before parsing or allocation of more input.

## F3 — Manifest

A `manifest` has every field below, no others:

- `schema: 1`, `features: []`;
- `name`, `version`, `arch`, `slot`, `license`: nonempty strings;
- `sources`: nonempty list of `source { name, sha256, length }` (strings, lowercase
  64-hex SHA-256, nonnegative integer length); source names are logical references,
  never URLs to execute or host paths;
- `buildinfo`: lowercase 64-hex SHA-256 of the detached buildinfo;
- `installed_bytes`, `installed_inodes`: nonnegative integer estimates;
- `requires`, `optional`, `conflicts`, `replaces`: lists of F4 `dep` records;
- `provides`: list of `provide { name, version }` (exact versioned capabilities);
- `files`: list of F5 file records; `configs`: list of paths of regular files;
- `actions`: list of `action { kind, name, version }`, where kind is
  `account`, `directory` or `cache`; names are registry references and version is
  a positive integer. These are declarations, never executed by pm01.

Names, architectures and ABI slots match `[a-z0-9][a-z0-9_+.-]*`, maximum 128
bytes, excluding `.` and `..`. Licence is a nonempty descriptive string, at most
4096 bytes. Version follows V1–V2. Invalid identity: `bad-identity`; invalid digest:
`bad-digest`. Comparator-equal versions in the same snapshot slot reject even
when spelling differs. Maximum snapshot packages: 24 (`snapshot-limit`).

## F4 — Dependency edges

`dep { name, op, version, arch, slot }`: strings. Operators are `any`, `=`, `!=`,
`<`, `<=`, `>`, `>=`; `any` requires version `""`, otherwise V2 version required.
The target's concrete architecture and ABI slot must match exactly. A versioned
provide satisfies an edge using its advertised version, not package version.
Conflicts match direct names or capabilities symmetrically; replaces names a
concrete installed package, never virtual overwrite authority. Optional edges
are advisory until explicitly requested. Duplicate provides by name reject.

## F5 — Installed file records

`file { path, type, mode, owner, group, length, sha256, target }`:
all fields required; mode/owner/group/length are nonnegative integers. Type is
`file`, `dir`, `symlink` or `hardlink`. Mode <= 0777 (decimal 511); numeric owners
<= 2^32-1. Paths are relative UTF-8, <=4096 bytes, no empty/`.`/`..` components,
NUL, absolute prefix, backslash, controls, or trailing slash. No duplicate paths,
non-directory ancestor, or payload below `home`, `var`, `run`, `proc`, `sys`,
`dev`, `boot` or `efi`. A regular file requires a lowercase SHA-256 and empty
target; other types require empty sha256 and zero length. Directory target empty.
Symlinks use a nonempty relative target whose lexical resolution from its parent
never escapes the package root. Hard links name a regular file in this manifest,
without chains, absolute names or traversal, and must match its mode/owner/group.
Config paths identify regular files
under `etc/` only. Errors: `bad-path`, `duplicate-path`, `path-conflict`,
`bad-file`, `bad-link`, `bad-config`, `bad-action`.

## F6 — Restricted POSIX pax payload profile (pm02 implementation)

512-byte ustar headers plus per-entry pax `path`, `linkpath`, `size`, `mtime`,
`atime`, `ctime` only when needed for numeric size/time representability. Canonical
packer normalizes path order, numeric owners, timestamps, zero padding and two
zero end blocks. Size/time records use bounded decimal POSIX syntax, never GNU
base-256 headers. Required bounds: 1 MiB cumulative extension header bytes,
100,000 entries, 16 GiB installed bytes and declared authenticated payload length;
check before allocation and fail on arithmetic overflow. One local extension
header per following file; unused/duplicate keywords reject. Paths and link
semantics are F5. No global pax, GNU headers, devices, sockets, FIFOs, sparse
maps, xattrs, ACLs, set-ID bits or unknown features. Reject checksum/length mismatch,
duplicate paths, malformed text, unknown type, escaping or absent hardlink target,
nonzero padding, overlapping types and inconsistent manifest inventory. Authenticate
the full blob before even staging; verify installed lengths/digests/metadata before
promotion. Never follow an archive-created symlink while staging. No archive is
parsed or extracted by pm01. F6 reader tests are owned by pm02, not claimed here.

**F6.1 — Exact end:** the reader accepts a payload ending exactly after its two
512-byte zero end blocks and refuses every additional byte, including zero-filled
blocks within the authenticated declared length, as `trailing-data`.

**F6.2 — Numeric encoding:** base-256 is forbidden even when a valid local pax
record overrides the value; a base-256 mode, uid, gid, size or mtime is refused
as `header-number`.
