# Bounded archive sink

This checkpoint adds a reusable framing layer, not a new archive format or a backup/encryption implementation. The package packer keeps its CLI, template limits, reserved paths, normalized owners/times and canonical bytes. A consumer supplies its own admitted profile and a stable runtime I/O handle; it owns source reads, hashing, encryption, lifetime and publication.

## Resource profile

`payload.Profile` has `max_entries`, `max_data_bytes`, `max_extension_bytes` and `chunk_bytes`, all checked before allocation/accounting. Counts/aggregate limits may be zero but not negative. Body chunks are positive and at most 131072 bytes. One extension body remains bounded at 1 MiB independently of the cumulative extension budget. The metadata inventory is in memory and bounded by the explicitly admitted entry count; this is not a measured application-level memory budget.

`payload.package_profile()` returns the unchanged defaults: 100000 entries, 17179869184 data bytes, 1048576 cumulative extension bytes, 65536-byte body chunks. `payload.inspect()` delegates to `inspect_with_profile(stream, package_profile())`. No package CLI option imports a profile from untrusted archive/manifest data, and no profile relaxes path, type, numeric, link or exact-end rules.

## Writer interface

The public surface is in `packing`:

```text
Header { path, kind, mode, length, target, epoch }
Writer = writer_start(handle, profile)
writer_begin(mut writer, header) -> error string or empty
writer_data(mut writer, bytes) -> error string or empty
writer_end(mut writer) -> error string or empty
writer_finish(mut writer) -> error string or empty
writer_abort(mut writer) -> error string
```

The handle is one accepted by the pinned runtime's bulk I/O functions, such as an opened file handle or standard output connected to a pipe. It is not permission to treat arbitrary native OS descriptors as interchangeable with runtime handles. Keep it open and stable throughout the writer lifetime. The writer never opens, closes, duplicates, seeks, syncs or publishes it. Successful framing is not durable storage or a complete backup.

Headers normalize uid/gid to zero explicitly; original application ownership belongs in separate logical metadata. Modes are at most 0777 and epoch is nonnegative. Allowed member types and path/link rules remain F6. Member names are supplied in strictly increasing UTF-8 byte order. Data is opaque bytes and must exactly match the open member's declared length. Begin/data/end/finish phases are checked, as are per-chunk and aggregate budgets and signed-64-bit wire accounting, including padding and the reserved final blocks.

Cross-entry directory/hard-link relationships are checked before successful finish. Metadata retained for this check is part of the caller's admitted in-memory budget. Finish writes exactly two zero blocks and nothing else. Repeated finish or operations after finish refuse without writing. Abort and the first error latch permanently; no later operation can turn a failed writer into success. A sink error may follow a partial underlying write, so byte counters are authoritative only after successful calls; never resume a failed encryption session or publish partial output.

This API does not buffer a whole archive or create a plaintext spool. A controller can connect the borrowed output handle to a standard encryption process/stage and apply backpressure through the pipe. It must verify source stability and propagate source/encryption/store errors; the framing layer cannot infer those external facts.

## Compatibility and proof

The existing packer uses the same header/extension helpers through this state machine. Its source walk, schema validation, template/node budget, file hashes and output-file ownership remain its responsibility. Its package limits are unchanged; new callers choose resource profiles explicitly rather than widening package policy.

Rows cover independent exact bytes, lowered caps, explicit over-16-GiB header admission, numeric overflow, invalid metadata/ordering, incomplete/extra member data, phase misuse, abort/error latching, borrowed-handle lifetime, pipe backpressure and consumer failure, and the old canonical package fixture. Header-only large-size tests do not claim a full 16/32-GiB streaming pass. Full large-input and consumer memory qualification remains separate before a backup tool enables such sizes.

Process-pipe and filesystem-handle rows are host-dependent. Both Linux x86-64 and macOS arm64 hosted gates are required before merge, not just local unit success. The format/CLI defaults are held to the existing vectors and black-box archiver contrasts; no foreign implementation source is used.
