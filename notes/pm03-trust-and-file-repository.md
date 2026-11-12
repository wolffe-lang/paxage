# pm03 — trust and the file repository

Materialised by the orchestrator from PR #8's body at the merge (trunk `13e167b1`, 2026-11-03).

Footprint: cross-cutting

## Forbidden

No install, privileged run, live-root mutation, HTTP/DNS transport, real signing keys, registry publication, issue action, labels, merge or tag. No foreign package-manager, TUF, crypto or canonicalizer implementation source was consulted. Sources: TUF 1.0.37 text, its cited OLPC canonical JSON description, RFC 8032, and owned Wolf, standard library and project code. OpenSSL CLI ran only inside the pinned offline, unprivileged container on the FHS Linux host. No local curve arithmetic or blacklist was added. No attribution trailers.

## Inputs, verified

Initial base d5e83412b5f0a2a560661116cc1bdc2c560ee1fd; rebased onto the current CI-routing trunk d7c064b8434ad2cf231bdce00946870ed1122610 without changing its label/nightly policy. Wolf 0.2.36 and lupin 0.1.58 archive pins remain unchanged. Std is pinned to 23baa1add4e0f5565e298fa075e7bc7029ac410d and re-staged through tools/fetch-toolchain on both platforms.

Selected commits:
- `24917e1`: prediction before implementation.
- `2704eb7`: bounded span-preserving reader.
- `27fffa0`, `b9778cf`: ordered transitions and atomic generations.
- `5299b6c`, `62a4876`: isolated std pin and strict verification call sites.
- `57521d2`: reviewed stage regression, staging-manifest binding and bootstrap preflight fixes.
- `d083d92`: root-rotation budget before another metadata read.
- `216c8a7`: preserve CI routing and qualify it locally.
- `13e167b`: unmarked-key and timestamp-last interruption coverage.

TUF specification 1.0.37 (modified 2026-10-08), OLPC description and RFC 8032 read 2026-11-03. Canonical signed input is an explicit profile restriction, not a promise to import arbitrary TUF writers. The specification's pretty-printed examples are noncanonical wire spellings; section 4.1 permits an application format and does not require accepting those spellings. Unknown fields remain covered by signatures/hashes.

### std.json fitness

At the inspected std revision (unchanged from the original pin for these files):
- Duplicate keys: NOT suitable. `std/json/json.lu:119–128,753–787` intentionally keeps the last value; `tests/json/parse_shapes.lu:96–100` requires it.
- Allocation bounds: depth 64 exists (`json.lu:162–164,679–682`), but no byte/node/member budgets in `:620–640,723–787`; depth tests are `tests/json/parse_misses.lu:111–126`.
- Integers: `as_int` rejects Num (`json.lu:314–318`), but parsing accepts fractions/exponents/out-of-int-range numbers as Num (`:851–905`; `parse_shapes.lu:30–55`). Schema checks alone could handle this part.
- UTF-8: `parse` takes str (`json.lu:620`), not raw bytes. Escaped surrogates are checked (`:1143–1166`, `tests/json/unescape_shapes.lu:75–81`); a raw-byte validation boundary still needs qualification.
- Canonical bytes/spans: no guarantee. Key order is explicitly unspecified (`json.lu:71–75,1365–1378`, `tests/json/stringify_shapes.lu:12–14`), and Value retains no source spans (`:137–145`).

The ruled strict reader is independent of std.json, not a pre-parser. Std.json was not modified.

## Prediction

The original prediction forecast eighteen clauses and 1–50 ms native verification. R6 and R7 explicitly added T19/T20. The 16-signature ceiling is retained from the 1 MiB measurement, not an unbounded signature loop. The initial primitive qualification failed both named small-order identity rows; the same rows pass through std verify_strict, with all 5 RFC and 151 Wycheproof verdicts preserved.

Red-first records include the reader, state/clock checks, real CLI entrypoints, write cuts, committed corruption, same-root stage regression, manifest replacement at consumption, nonempty bootstrap and root-chain allocation ordering. Original pre-rebase records remain under evidence/; they are historical evidence, not final-head records.

The deliberate off-line plant is described below. It is not part of pm03 and has no PR.

## Evidence index

### Clause-to-row map

| Clause | Qualification |
|---|---|
| T1 scope/count/byte limits | T1 network/offline/count ceilings; root-chain limit and resume; Linux hostile lengths |
| T2 strict JSON | T2 unit refusal/max-bound rows; decoded duplicates, UTF-8, integers, depth/nodes/members/strings |
| T3 own canonical signed span | T3 exact-span/order/whitespace/escape/control rows; independent signed repositories |
| T4 role/version/time schema | T4 required fields, exact spec version, Gregorian UTC boundaries |
| T5 keys/thresholds | independent below-threshold, duplicate, unknown, revoked, wrong-length and scheme rows |
| T6 root | pinned self-threshold, immutable root publication and rotation cases |
| T7 timestamp | each-role/whole-snapshot rollback, freeze, same-version rewrite |
| T8 snapshot | exact whole-file binding, mix-and-match, version/length/hash refusals |
| T9 targets | target schema/identity/triplets, delegation refusal, exact stage source trees |
| T10 names | slash/dotdot/NUL/prefix/content mismatch vectors |
| T11 bootstrap | caller-pinned root; nonempty/missing-current preflight; no damaged-directory reuse |
| T12 rotation | skipped/new-only/old-only/dual thresholds, fast-forward reset, 32-step cap/resume |
| T13 partial update/clock | phase/history/clock rows; verified intermediate state; independent surviving-state oracle |
| T14 persistence | partial-root, synced-generation, synced-pointer and post-rename cut points |
| T15 writer | six marked 0600 keys; unmarked refusal; create-only; interrupted publication leaves timestamp unchanged |
| T16 cache/stage | full-object digest/length; isolated .part; bound manifest at consumption; two-package/two-publication roundtrip |
| T17 crypto | 5 RFC8032 + 151 Wycheproof; S/point/length/small-order rows; native timing |
| T18 independent/e2e/fuzz | 41 independent cases; OpenSSL verifies writer; 100000 individually timed mutations with independent proof checks |
| T19 corruption boundary | current/header/four roles/oversized/missing current refuse with zero writes and explicit new-directory re-bootstrap |
| T20 local-storage limit | labelled coherent-local-current replay witness; never presented as protection |

### Attack table

| Family | Named rows / expected outcome |
|---|---|
| rollback | root, timestamp, snapshot, targets, whole snapshot -> named rollback refusals |
| freeze | timestamp, snapshot, targets, expired final root -> named expiry refusals |
| mix and rewrite | mix-and-match -> metadata-hash; every role rewrite -> same-version-rewrite |
| signatures | threshold/unknown/revoked -> signature-threshold; duplicate -> duplicate-signature; length/scheme -> respective refusal |
| root rotation | skipped -> root-version; only-new/only-old -> respective threshold refusal; dual-signed recovery -> verified update |
| lengths | endless FIFO -> repository-file; timestamp ceiling -> metadata-byte-limit; snapshot/targets long/short -> metadata-length; object long/short -> target-length |
| target naming/content | slash/dotdot -> logical-name; escaped NUL -> non-canonical-signed; dishonest prefix/content -> target-hash |
| clock | before durable floor -> clock-before-floor; no unexpired final root -> expired-root |
| interruption | verified old/new generation at the specified cut; failed repository publish retains old timestamp |
| committed corruption | state-invalid plus explicit operator guidance; zero writes, no fallback |

Independent fixtures were generated from specification-derived bytes with OpenSSL 3.0.13 in image 77fdad6b841abfdb3968ea6137b1edf7248578bdfc4f92e4aab6b2a05f241485. The 406 committed fixture files contain public metadata/objects/witnesses, not private signing keys. Three all-space oversized metadata fixtures are intentional hostile bytes, not whitespace-formatting mistakes. The independent target objects are opaque trust fixtures; real F3/F6 package validity is exercised by the separate pack/fetch/stage roundtrip.

### Measurements and final records

Native empty-message qualification: median 1.730786 ms/signature. Initial 1 MiB qualification: median 25.425536 ms/signature. Strict 1 MiB requalification: median 24.004555 ms/signature, range 23.911569–27.006438, five batches of eight after warm-up, signing in a separate untimed process. Process startup/message construction are included; these separate runs are not a controlled speedup claim. Final-head measurements are in the Linux record below.

Mac uses bounded rows only, preserving the canonical payload identity artifact. All growth/fuzz/large-cost skips are loud. Linux runs both 100000-mutation payload and trust gates under the 2 GiB address-space cap; trust mutations have 5-second per-input timeouts and seed 1347224369. The state oracle checks original signed bytes against independent signature witnesses and checks the protected accepted files after every input.

Final main head: 13e167b1e04bc38aad943c36082762c2739d38f3. Both records were independently verified by gauntlet-record.sh. Linux: 31 zero-exit steps; Mac: 23 zero-exit steps plus the explicit platform skips.

Trust fuzz: 20038 verified updates / 79962 named refusals, 100000 total. Payload fuzz: 9359 accepted / 90641 refused, 100000 total. Final Linux 1 MiB strict cost: median 23.629633 ms/signature, range 23.602201–23.781660. Whole-reader RSS: 3276 KiB at 64 MiB, 3352 KiB at 1 GiB (+76 KiB). Canonical payload digest on both hosts: 5c3e99659affd3370210b28108617b5f6f66773ead7956bd30634056ed9df9aa.

OpenSSL verified all 107 signatures across 39 writer metadata files for each host. Mac-writer contrast record: evidence/interop-mac-writer-13e167b.record.

evidence/green-linux-13e167b.record

```text
END fmt exit=0 secs=0
END ci-routing exit=0 secs=0
END build exit=0 secs=1
END runtime-witness exit=0 secs=0
END unit exit=0 secs=2
END cli exit=0 secs=0
END payload exit=0 secs=18
END container exit=0 secs=3
END inventory-bound exit=0 secs=3
END chunk-rss exit=0 secs=2
END rss exit=0 secs=33
END trust_json-build exit=0 secs=0
END trust_json exit=0 secs=0
END trust_metadata-build exit=0 secs=0
END trust_metadata exit=0 secs=0
END trust_state-build exit=0 secs=0
END trust_state exit=0 secs=1
END trust-harness exit=0 secs=0
END trust-crypto-generate exit=0 secs=0
END trust-crypto-build exit=0 secs=0
END trust-crypto-cost exit=0 secs=2
END trust-crypto-vectors exit=0 secs=0
END trust-crypto-qualification exit=0 secs=0
END trust-cli-build exit=0 secs=1
END trust-cli-e2e exit=0 secs=5
END trust-corruption exit=0 secs=1
END trust-independent exit=0 secs=12
END trust-openssl-writer exit=0 secs=0
END trust-fuzz-build exit=0 secs=2
END trust-fuzz exit=0 secs=495
END trust-local-replay-limit exit=0 secs=0
RECORD-END worst=0 steps=31 end=2026-11-03T11:01:55Z
```

evidence/green-mac-13e167b.record

```text
END fmt exit=0 secs=0
END ci-routing exit=0 secs=0
END build exit=0 secs=1
END runtime-witness exit=0 secs=1
END unit exit=0 secs=3
END cli exit=0 secs=0
END payload-roundtrip exit=0 secs=0
SKIP payload-growth reason=Linux-only capped entry, cumulative-extension and allocation bounds
SKIP payload-fuzz reason=Linux-only capped 100000 mutations; never on the Mac
SKIP container reason=Linux-only container interoperability and confinement
SKIP inventory-bound reason=Linux-only capped maximum-inventory measurement
SKIP chunk-rss reason=Linux-only capped allocation measurement
SKIP rss reason=Linux-only capped large-file measurement; never on the Mac
END trust_json-build exit=0 secs=1
END trust_json exit=0 secs=0
END trust_metadata-build exit=0 secs=0
END trust_metadata exit=0 secs=0
END trust_state-build exit=0 secs=1
END trust_state exit=0 secs=0
END trust-harness exit=0 secs=1
END trust-crypto-generate exit=0 secs=0
END trust-crypto-build exit=0 secs=0
SKIP trust-crypto-cost reason=Linux-only capped 1MiB measurement; never on the Mac
END trust-crypto-vectors exit=0 secs=0
END trust-crypto-qualification exit=0 secs=0
END trust-cli-build exit=0 secs=1
END trust-cli-e2e exit=0 secs=3
END trust-corruption exit=0 secs=1
END trust-independent exit=0 secs=6
SKIP trust-large-metadata reason=three byte-limit cases run only on capped Linux
SKIP trust-openssl-writer reason=OpenSSL CLI runs only in the FHS Linux host container
SKIP trust-fuzz reason=Linux-only capped 100000 mutations; never on the Mac
END trust-local-replay-limit exit=0 secs=1
RECORD-END worst=0 steps=23 end=2026-11-03T10:56:22Z
```

Plant branch `pm03-plant-timestamp-13e167b`, head 979e536ccf1853ffd4482f53d1f1b77567b714f8: one commit, one file, one hunk on the main head. It omits only timestamp rollback refusal; the independent attack accepts an older timestamp and the expected-refusal row fails. The plant never lands on pm03.

evidence/red-plant-979e536.record

```text
END plant-build exit=0 secs=1
FAIL independent-rollback-timestamp rollback-timestamp: expected=rollback-timestamp exit=0 stdout='update ok\n' stderr=''
END plant-attacks exit=1 secs=0
END record-wrapper exit=1 secs=0
RECORD-END worst=1 steps=3 end=2026-11-03T11:04:28Z
```

### R-list and limits

- Selected approach: require a canonical signed span; verify its own bytes. No arbitrary writer-import goal.
- Selected approach: local strict bounded reader; std.json untouched.
- Built with timestamp 48 h, snapshot 14 d, targets 90 d, root 365 d defaults; confirmation remains owed.
- Selected approach: timestamp alone is atomically replaced, last; other outputs remain create-only.
- Selected approach: pin std's additive verify_strict; no local blacklist or point arithmetic.
- Selected approach: candidate fuzz protects accepted state; committed corruption refuses without repair. B, a recovery anchor/redundancy policy, remains later work.
- Selected approach: a writer of trusted local storage can coherently replace it, root included. This is outside v1. An independent monotonic anchor (B) belongs to pm04/pm05; production state will be root-owned.

Existing same-uid staging ancestor races remain documented; this is not an installer or a security certification. Interruption rows are deterministic syscall-boundary failures, not physical power-cut tests. The wrapper's earlier compile-status masking was corrected and separately witnessed; superseded records are not substituted for final-head greens.

## Done-when

- [x] Prediction, numbered profile, strict reader, reused crypto and test-only keys.
- [x] File repository/client/cache, authenticated staging inputs, atomic state and explicit refusals.
- [x] Red-first regressions and independent signed attack fixtures.
- [x] README read and refreshed; current CI label/nightly routing preserved and locally tested.
- [x] Final-head Linux/Mac records and named one-hunk local plant, quoted above.
- [x] PR #8 opened; immediate run lookup read once (no run existed yet); audit executed once.
- [ ] Coordinator requests full-matrix CI and watches its full result before merge.

Test checklist:
- [x] fmt, native build, runtime witness, units, classic CLI fixtures
- [x] bounded Mac payload roundtrip and Linux payload corpus/fuzz/RSS/container targets
- [x] strict JSON/metadata/state/crypto units and build-status regression
- [x] trust two-publication e2e, corruption, independent attacks and operator-limit witness
- [x] final Linux trust 100000 mutations, final OpenSSL writer contrast, plant record

No issue was filed or closed. No branch is to be merged by this lane. This PR body carries the five report sections; the coordinator may materialize the lane note after merge.

Audit executed once after opening: local/plant/head/report/fast-forward checks passed. The audit observed cheap-only run 41624939995, completed success, which is not cross-cutting merge evidence. Exact final line: `AUDIT FAIL (footprint: cross-cutting)`. No CI polling, label action or audit rerun was performed. Audit log: lane-audit-pr8.log.
