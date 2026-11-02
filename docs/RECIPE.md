# Recipe v1

## R1 — Declared graph

`recipe { schema, features, name, version, inputs, requires, environment, steps,
source_date_epoch }` uses F2 data. schema is 1; features empty; identity follows
F3; inputs is a nonempty list of `input { name, sha256, length, kind }`, with
kind `source`, `script`, `toolchain`, `container` or `dependency`. All hashes and
lengths are immutable, names unique and logical, no host paths or secrets.
requires is F4 edges, never executable graph discovery. source_date_epoch is a
nonnegative integer. No recipe is evaluated or executed by pm01.

## R2 — Environment and argv

environment is a list of `env { name, value }`, unique ASCII environment names
`[A-Z_][A-Z0-9_]*`; values literal strings. steps is an ordered nonempty list of
`step { phase, argv }`, phase `build`, `check` or `package`, argv a nonempty list
of nonempty strings. No shell interpretation is implicit. An explicitly invoked
script must be a digest-pinned input. There are no install hooks or install phase.

## R3 — Builder policy (pm08)

Fetch and verify declared inputs before isolation; no network during build,
check or packaging, no home/secrets/privileged mounts, only declared tools and a
writable output root. A chroot alone is not hostile-code isolation. Two clean
builds vary path/time-zone/environment/order and compare all artifact hashes.
Scripts execute only as explicitly pinned build inputs inside the sandbox, never
in discovery, fetch, resolve or install. This is distro policy separate from D33;
`wolf add/build` and language resolution do not execute a distro recipe.

## R4 — Build provenance

`buildinfo { schema, features, recipe, sources, toolchain, container, dependencies,
source_date_epoch, source_package }`: schema 1, empty features, SHA-256 strings
for recipe/toolchain/container/source_package, lists of source records F3 for
sources and dependencies, nonnegative source_date_epoch. No signing keys, secrets
or host paths. Source package reference preserves licence-compliance provenance.
R1–R4 are frozen schemas; recipe execution, reproducibility and buildinfo production
are later gates, not implemented CLI verbs in pm01.
