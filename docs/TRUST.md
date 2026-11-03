# Trust profile v1

This is the implementation contract, not a claim that the commands below ship.
It profiles TUF 1.0.37 (last modified 2026-10-08), read 2026-11-03:
<https://theupdateframework.github.io/specification/v1.0.37/>.
Canonical encoding follows the OLPC description linked by TUF §4.1:
<https://web.archive.org/web/20251209150702/http://wiki.laptop.org/go/Canonical_JSON>.
Ed25519 follows RFC 8032 §5.1 and §7.1, not implementation source.
The design of record is R-pm00-7 and R-pm00-8, with pm03's ruled amendments.

## T1 — Scope and limits

Only a caller-named `file://` repository, trust directory, cache and staging
area are supported. Bootstrap requires an independently pinned root supplied
by the caller, never the repository's unauthenticated root. No live-root
mutation, privileged operation, HTTP, DNS, redirects, mirror discovery or
installation exists in this profile. Refusals: `unsupported-transport`,
`bootstrap-unpinned`, `offline-recovery-refused`, `unsupported-delegations`.
`install`, `remove`, `upgrade`, `sync` retain their individual C2 refusals.

Local client byte ceilings are timestamp 16,384, root 65,536, snapshot 65,536,
and targets 1,048,576. An authenticated length does not raise these ceilings.
Stop after cap+1 bytes, never read an entire hostile file before checking.
Refuse `metadata-byte-limit`; a bound length must match exactly, otherwise
`metadata-length`. Root rotation accepts at most 32 steps per invocation;
reaching the limit without establishing termination refuses `root-chain-limit`.
Already accepted roots remain durable and the next invocation can continue.
Maximum keys 16, signatures per envelope 16, targets 72 (F3's 24 packages times
F1's three files); refuse `key-limit`, `signature-limit`, `target-limit`.
These are application bounds under TUF §5.3.3, §5.4.1, §5.5.1 and §5.6.1.
The signature ceiling is fixed at 16 from the native kasumi measurement:
five batches of eight verifications of a 1 MiB message gave a median
25.425536 ms/signature (range 25.387417–25.627197), process-inclusive with
signing outside timing. Sixteen signatures therefore represent about 0.41 s
of measured verify work at the largest input, not a wall-clock guarantee.
The forthcoming strict std entrypoint must repeat this qualification.

## T2 — Strict byte-oriented JSON reader

The reader is independent of std.json, not a pre-parser in front of it.
Input must be shortest-form UTF-8 scalar encoding, with no surrogate code
points, overlong sequences, truncated continuations or code points above
U+10FFFF. Validate bytes before constructing strings: `bad-utf8`.
No BOM, comments, trailing commas, leading plus, alternate integer bases,
float, exponent or negative integer. Values are objects, arrays, strings,
nonnegative decimal integers, `true`, `false` and `null`. Objects require quoted
keys; delimiters and whitespace are ASCII JSON punctuation and space/tab/CR/LF.
Exactly one complete value is allowed: `syntax` or `trailing-data` otherwise.

Strings accept JSON's quote, backslash, slash, b, f, n, r, t and `uXXXX`
escapes, with correctly paired surrogates. Refuse `bad-escape`,
`bad-surrogate` and literal bytes below U+0020 as `control-byte`.
Duplicate keys are compared AFTER decoding and refused as `duplicate-key`,
including a literal letter and its equivalent hexadecimal Unicode escape.
No normalization changes Unicode identity. Integers use `0` or a nonzero digit followed by digits,
maximum 9,223,372,036,854,775,807. Refuse `integer-overflow`, `negative-integer`,
`float`, `exponent`; do not convert through floating point.

Before the associated allocation, recursion or append, enforce byte ceiling
(T1), depth 16 containers, 16,384 value nodes, 4,096 members per container,
and 65,536 decoded bytes per key or string. Refusals: `depth-limit`,
`node-limit`, `member-limit`, `string-limit`. Empty containers count toward
depth; keys have string/member budgets but are not value nodes.
Keep each value's half-open byte span into the bounded original input.
Unknown fields are retained, covered by signatures/hashes and preserved on
reserialization as TUF §4 requires; known fields still undergo type and
semantic validation. Unknown fields do not authorize unsupported features.

## T3 — Canonical signed bytes

An envelope's `signed` value must be an object. Its exact source span, from
opening `{` through closing `}`, must already equal its canonical encoding;
otherwise refuse `non-canonical-signed`. Verify that span's own bytes, not a
pretty print and not the envelope. Envelope whitespace is not signed.
Key IDs are SHA-256 over canonical key-object bytes (TUF §4.2.1, §4.3).
Metadata-file hashes bind the WHOLE original envelope, including signatures
and whitespace; do not substitute the signed-value digest.

Canonical encoding uses no token whitespace, lexicographically byte-sorted
decoded keys, decimal integer spelling, and only the mandatory `\"` and `\\`
escapes for quote and backslash. Other string bytes are unchanged; never
normalize Unicode. OLPC canonical strings permit arbitrary bytes and raw
controls. This profile deliberately restricts input to valid UTF-8 and JSON
strings: a decoded control character cannot have a canonical signed spelling
in this profile and therefore causes `non-canonical-signed`. The writer must
refuse such signed data rather than emit JSON control escapes and call them
canonical. Unsigned-envelope strings still obey T2.

TUF §4.1 permits an unambiguous application encoding and §4.2.1 defines the
signature over canonical role data; neither requires accepting a noncanonical
wire spelling. The specification's own pretty-printed examples demonstrate
noncanonical signed spellings are possible; no implementation's output was
inspected. Importing arbitrary other TUF writers' files is not a v1 goal.
This canonical-input restriction is explicit, not a general compatibility claim.

## T4 — Envelopes and common role fields

Require `signed` object and `signatures` array; each signature has `keyid` and
`sig` strings. Common signed fields are `_type`, `spec_version`, `version`,
`expires`. Required-field and type failures are `missing-field`, `field-type`.
`_type` must match the requested role (`role-type`); spec_version must equal
`1.0.37` (`spec-version`), a permitted exact-match policy under TUF §4.3.
Versions are positive bounded integers (`metadata-version`). Expiry is an
actual UTC Gregorian timestamp `YYYY-MM-DDTHH:MM:SSZ`, not just a lexically
matching string; years 1970–9999 only, with no alternate zones or leap-second
spelling (`metadata-time`).
Each expiry must be strictly later than the fixed update start time when its
workflow step requires expiry checking; equal timestamps are expired.

## T5 — Keys, schemes and thresholds

Only `keytype: ed25519` with `scheme: ed25519`, pure RFC 8032 Ed25519, is
supported. Refuse Ed25519ph, Ed25519ctx, RSA, ECDSA and every other scheme as
`unsupported-scheme`; never substitute a prehash. Public keys are exactly 32
bytes encoded as 64 lowercase hexadecimal characters; signatures exactly 64
bytes encoded as 128 lowercase hexadecimal characters. Refuse `key-length`,
`signature-length`, `bad-hex`. Key IDs are lowercase SHA-256 hex and must match
the canonical public key object (`key-id`). No private material belongs in
metadata. Reject multiple IDs for the same decoded public key as `key-alias`,
so one key cannot satisfy a threshold twice under aliases.

Root, targets, snapshot and timestamp have disjoint authorized key sets,
positive thresholds no larger than their distinct authorized keys, and no
missing key references (`role-keys`, `threshold`). Distinct verified authorized
keys count once; duplicate signatures cannot increase the count. Duplicate
key IDs in the signatures array refuse `duplicate-signature` per §4.2.1;
unknown IDs are ignored and never count. Insufficient distinct valid signatures
refuse `signature-threshold`. Revoked keys are no longer authorized.
Malformed authorized signatures fail closed; invalid signatures never count.
T17's stricter invalid-point checks apply before acceptance.

## T6 — Root role

Root signed data contains `keys`, `roles`, and `consistent_snapshot: true`
in addition to T4 fields. All four roles are required; delegations and mirror
roles are unsupported. Keys and thresholds obey T5. Refuse inconsistent
snapshot mode as `consistent-snapshot-required`. Default test root policy is
2-of-3 root keys, and separate 1-of-1 targets, snapshot and timestamp keys.
Published root metadata is `metadata/<version>.root.json` and retained forever
within this writer's lifecycle (TUF §4.3, §6.1, §6.2.1).

## T7 — Timestamp role

`meta` contains exactly `snapshot.json`, with positive `version`, nonnegative
`length`, and `hashes.sha256`. SHA-256 is mandatory in this profile; no other
hash scheme is supported (`unsupported-hash`, `metadata-reference`). Fetch
only `metadata/timestamp.json`. Verify its role threshold, rollback constraints
and expiry before persisting. Timestamp version may not fall below trusted
state (`rollback-timestamp`); its referenced snapshot version may not fall
below the previously trusted timestamp's reference (`rollback-snapshot`).
For equal timestamp versions, different whole bytes refuse
`same-version-rewrite`; identical bytes mean no new timestamp. Expired cached
metadata never becomes usable through this equality shortcut. A later step
that failed previously may resume against the already trusted timestamp, not
a newly accepted equal-version timestamp (TUF §4.6, §5.4).

## T8 — Snapshot role

Timestamp binds whole snapshot envelope hash, exact length and version.
Fetch `metadata/<version>.snapshot.json`; refuse `metadata-hash`,
`metadata-length`, `snapshot-version` as appropriate before trusting it.
Verify threshold and expiry. `meta` contains exactly `targets.json`, with
mandatory version, length and SHA-256 (TUF §4.4 permits these extra bindings).
Snapshot versions and targets references never decrease within the current
key epoch (`rollback-snapshot`, `rollback-targets`). Same snapshot version with
different whole bytes refuses `same-version-rewrite` (§5.5).

## T9 — Targets role and package identities

Snapshot binds whole targets envelope hash, length and version. Fetch
`metadata/<version>.targets.json`, verify binding, role threshold and expiry;
refuse `metadata-hash`, `metadata-length`, `targets-version` or
`expired-targets`. Any `delegations` field refuses `unsupported-delegations`.
Each logical target binds SHA-256, exact nonnegative length and `custom` fields
`name`, `version`, `architecture`, `kind` (manifest, payload or buildinfo).
Identity obeys F3, package versions obey V2, and kind must agree with F1's
suffix. Three targets for a package must agree on identity. Refuse
`target-identity`, `target-kind`, `target-incomplete`; an empty repository is
allowed. Keep all additional custom data authenticated, never executable.
Same targets version with different whole bytes refuses `same-version-rewrite`.
Targets rollback knowledge comes from trusted snapshot metadata and resets
with it under T12, not a permanent independent targets high-water mark.

## T10 — Repository names

Metadata references are logical `snapshot.json` and `targets.json`, NEVER
prefixed paths. The client derives the versioned metadata filename and
`targets/<sha256>.<logical-name>` itself (TUF §6.2.1, §5.7). A logical target
is one F1 basename, no slash, backslash, NUL, control byte, `..` substring,
absolute name, percent-encoded path interpretation or URL query/fragment;
refuse `logical-name`. Its digest prefix is derived from authenticated metadata,
never accepted from an arbitrary mirror filename. Dishonest bytes behind that
prefix refuse `target-hash`; an absent expected filename refuses `target-file`.
No repository bytes choose a host outside the
caller-supplied local directory. Nonregular files and detectable symlinks
refuse `repository-file`; no network endpoint is followed.

## T11 — Bootstrap and trust state ownership

Bootstrap exclusively creates the initial state in a caller-named private
directory from the caller's pinned root file, validates structure and self-threshold, and
records its exact bytes. Self-signature alone is NOT the bootstrap trust
anchor: provenance is the caller's pinned input. Existing state is never
silently overwritten (`trust-state-exists`). State is scoped to that root
history and one caller-supplied repository; switching repositories requires
an explicit new state directory, not a metadata instruction.

## T12 — Sequential root rotation and recovery

Try exactly trusted root N+1, never skip versions. Authenticate each candidate
under BOTH the old root threshold and its own root threshold; reject
`root-old-threshold`, `root-new-threshold`, `root-version` as appropriate.
Old and intermediate roots may be expired during rotation. Persist each fully
verified root atomically before proceeding. The final trusted root must be
unexpired (`expired-root`). A malformed existing N+1 is not treated as absence.
If a root candidate reuses N with different bytes, name `same-version-rewrite`.

When timestamp OR snapshot authorized keys rotate, delete/reset BOTH trusted
timestamp and snapshot state (TUF §5.3.11); target rollback references in that
snapshot disappear with it. Do not reset for an unchanged key set alone or
retain an unconditional numeric high-water mark that prevents fast-forward
recovery. The reset obligation is persisted with the accepted root, so an
interruption cannot forget it. Old targets cease to authorize fetching until a
new complete chain is verified. Preserve the trusted update-time floor across
key rotations. A failed write leaves either the old durable root/state or the
new fully verified durable root/state, never a mixed invalid state.

## T13 — Update order, clock and partial failure

Record one fixed `now` at entry (TUF §5.1), from explicit `--now` UTC or the
system clock. Without `--now`, output explicitly says `clock=system`. Tests
always supply `--now`. Never use repository time. If now precedes the durable
floor refuse `clock-before-floor`; expiry failures name their role.
Update root, timestamp, snapshot, then targets. Persist only a step that has
completed every applicable verification; failures identify the step and leave
all earlier fully verified state usable for a subsequent update. No target
is usable until the complete current chain verifies at the supplied now.
The stored time floor advances monotonically with accepted update state.

## T14 — Durable writes

All trust-state changes use exclusive temporary-file creation within the
caller-named directory, full write, `fs_sync`, atomic rename and `sync_dir`.
An existing temporary name is a refusal, never truncated. Do not claim durable
success until directory sync succeeds. Persist enough root epoch/reset and
verified metadata state in one atomic authoritative generation to prevent
mixed generations; uncommitted temporary files are never read as trusted.
Refuse `state-create`, `state-write`, `state-sync`, `state-rename`,
`state-dir-sync`, `state-invalid`, each with the current workflow step.
A post-rename I/O error may leave the new verified state visible; report the
error, never pretend the old bytes necessarily remain. No automatic deletion
outside caller-named state/cache directories.

Each generation directory `g<N>` contains unprefixed role files and a small
`state.json` header carrying hashes, rollback marks, the canonical repository
path, the time floor and completed stage. The atomic `current` pointer binds
that header by SHA-256. Sync every role file, the header, the generation
and its parent before replacing `current`; then sync the parent again.
Orphan generations and temporary pointers are never selected as authoritative.
Readers recheck the header hash, role hashes, signatures and reference bindings.

## T15 — Test repository writer

Generate test keys only into a caller-named private directory; each file has
an explicit `test-only` marker and mode 0600. Refuse an unmarked key with:
`Real repository keys need std's constant-time signing review and the maintainer's ceremony (R-pm00-7)`.
Never load real keys or put private keys into CI secrets; generate test keys
per run. Signing/public derivation use std curve25519, hashing uses std SHA-2.

Create target objects, versioned targets, then snapshot, with all referenced
files present and synced before timestamp publication. Every immutable output
is create-only, including root; refuse `immutable-rewrite` even if bytes match.
Only `metadata/timestamp.json` may be replaced, using T14's atomic sequence,
with timestamp last (TUF §6.2.1 and §6.3). Failed publication must leave old
published timestamp intact until the atomic replace; orphan immutable files
are harmless, not authorization. Default validity windows are timestamp 48 h,
snapshot 14 d, targets 90 d, root 365 d, overridable explicitly per call.
These defaults await the maintainer's confirmation; they are not crypto facts.

## T16 — Cache and staging

Unverified bytes live separately in `.part`. Stream each entire target through
std SHA-256 and exact-length checking; refuse `target-length`, `target-hash`.
Only after full verification and sync may it become `objects/sha256/<hex>`.
Never consume `.part` as verified; reverify existing objects before exposing
them, since a pathname is not authentication. No unverified prefix is usable.
Fetch records its logical target identity; pm02 stage receives payload digest
and length from verified targets metadata and an authenticated manifest.
Stage still performs its own C6 verification. Staging is not installation.

## T17 — Cryptographic qualification

RFC 8032 §7.1 positive vectors and std-vendored Wycheproof ed25519 invalid
vectors are qualification inputs; vendor data is read directly, never copied
by hand. Refuse noncanonical S >= L (`non-canonical-scalar`), noncanonical
key or R encodings (`non-canonical-key`, `non-canonical-R`), small-order key
or R (`small-order-key`, `small-order-R`), and wrong lengths (T5).
Use std verify, never another Ed25519 implementation. A missing primitive
rejection is a qualification failure to report, not permission to implement
new curve arithmetic here. Native kasumi verify cost, including sample count,
message length and timing distribution, must justify T1's signature bound.

## T18 — Independent and end-to-end evidence

An independently authored Python generator emits canonical bytes from this
profile/specification and signs through OpenSSL Ed25519 as a black box only
inside an unprivileged network-disabled kasumi container. Record OpenSSL's
version. Verdicts come from these clauses, never from a tool's acceptance.
Verify the generator's valid repository, and use OpenSSL to verify this
writer's signatures over the same signed bytes. Pack two packages, publish,
bootstrap, update, fetch and stage on both CI hosts, then publish/update/stage
new versions; check exact tree equality, exits and stdout.

Every prediction attack row has a named outcome. Fuzz at least 100,000 seeded
mutations per CI run across all four roles and trust state, per-input timeout,
and independently verify surviving state after each attempt. Crash, trap,
hang or unverifiable state fails. Memory-growing cases run only on Linux
under a 2 GiB address-space cap. One final-head, one-hunk local plant removes
one check and must fail its named row; it never lands on the main branch.
Every final gauntlet step's END exit is recorded; wrapper success is not proof.
