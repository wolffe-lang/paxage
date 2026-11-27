# Disposable install fixture

`fixture-producer.yml` runs only by an explicit hosted dispatch. It never publishes to a package site. It creates a test-only signed repository containing two static scent packages for install, upgrade, removal and recovery tests.

The source inputs are `tests/fixture-producer-inputs.json`: an immutable Ubuntu image digest, an immutable authenticated APT snapshot, a digest-checked public CA bundle for download bootstrap, and two scent source commits/archive digests. Each scent tree fetches and checks its own compiler/runtime/std pin. Each package has its source's unmodified static scent executable, license and a test-version marker. Package versions `1-1` and `2-1` are fixture identities, not upstream release claims. The two executable hashes must differ.

Two independent builds compile paxage and both scent inputs, pack both packages, initialize/sign repository metadata with the existing test publisher, and verify the public repository with the client. The public inventories and canonical tar bytes must agree before anything is exported. The fixed epoch is 2026-11-26T00:00:00Z; metadata validity is one year. Use the descriptor's clock window in guest tests. A future fixture update must review its epoch and source pins rather than silently mixing in the current time.

## Signing boundary

The isolated hosted container derives disposable role material internally from fixed versioned labels. No seed, key path, production root or production credential is a workflow input. The publisher is unprivileged and accepts only its marked test material. The helper refuses ordinary local runs, root and non-dispatch environments; these checks are guardrails, not a production security boundary.

The source checkout is read-only inside the container. Private temporary work stays inside its ephemeral filesystem, not a host-mounted output directory. The producer receives a cleared environment without the checkout credentials or the workflow's service credentials. Child arguments, private bytes and captured child output are never logged. No cache or failure-time workspace upload is configured.

Local tests never generate or load signing material. They inspect generation entrypoints as AST and test only the public environment predicate; no generation entrypoint is called locally, even negatively. They cover the public comparator, controlled-clock sensitivity, canonical archive metadata, export allowlists, digest binding and unsafe source paths. Their unsigned public JSON stubs are deliberately not installable repositories and are not substitutes for a successful producer dispatch.

## Public artifact

The `disposable-install-public` run artifact contains exactly:

- `disposable-install.tar`: public role metadata, hash-named package targets, `pinned-root.json` and `TEST-ONLY.json`;
- `PUBLIC-RECEIPT.json`: producer revision, input-manifest digest, canonical bundle SHA-256/length and public inventory.

The export starts in a fresh directory and accepts only explicit public names. Links, private fields, unexpected files, noncanonical archive metadata and altered hashes refuse. Verification before upload reads the tar without extracting it. Private publisher state, key files, source workdirs and locks never enter the artifact.

The descriptor marks the fixture test-only and records both source/toolchain/executable identities, static libc archive hash, package environment, public-root digest, architecture `x86_64`, slot `default` and the validity window. Do not use this anchor in a production image or channel. The CA bundle under `ci/fixture-ca/` is only build-download bootstrap data, not a package trust anchor or guest configuration.

## Dispatch and consumption

Review and merge the workflow before selecting its immutable producer commit for a dispatch. The workflow must exist on the default branch for GitHub to offer it. A person with dispatch permission runs it; no other workflow triggers it or automatically retries the job. A failed run exports no artifact and does not authorize another dispatch.

After a successful run, download its named artifact into a new empty directory and validate the public output:

```sh
python3 -I tools/check-fixture-producer --export PUBLIC_DIRECTORY
```

Check the run's actual executed steps and reviewed source revision, not only its summary. In a later consuming commit, pin the run ID/attempt, artifact ID/service digest, inner tar SHA-256/length, descriptor/input-manifest digest and public-root digest. The upload service's outer archive digest is not the inner tar digest. Keep the verified public bundle in approved durable content-addressed storage or vendor it as test data before the run artifact expires.

## Pinned consumer

`tests/pax-fixture-pin.json` pins successful producer run `45914664981`, attempt 1, at `d88e8d54befa1b2cef29a2ca2edeaa5e89c28eef`. The approved inner bundle is 2,908,160 bytes, SHA-256 `f185488197c4ac0924b921dabbf39b60c3542f34a034ac0e26b947ccc132ee2e`. Its public root is version 1, SHA-256 `57da38ddbc7279a4a639920256399c03152443161173a8d18462b6c087513288`: root threshold 2 of 3, with independent targets, snapshot and timestamp roles at threshold 1. All roles expire at 2027-11-26T00:00:00Z. The service digest in the pin records provenance; checking the downloaded inner files does not claim to recheck the service's outer archive bytes.

The two scent fixture package versions are `1-1` and `2-1`, with distinct static x86-64 executables. The pin also records their source, source-archive, toolchain and executable digests, plus receipt, descriptor and producer-input digests. These are public test data, never a production trust anchor.

Provide the approved two-file export by a separate, reviewed copy; the consumer never downloads anything. Validate it and optionally extract only its checked public byte snapshot into a new directory:

```sh
python3 -I tools/pax-fixture PUBLIC_DIRECTORY --extract NEW_PUBLIC_REPOSITORY
python3 -I tools/check-pax-fixture --export PUBLIC_DIRECTORY
```

The consumer compares the reviewed bundle digest before archive parsing or extraction, then reuses the public export validator and checks the receipt, descriptor, public root and both package identities. It refuses links and existing outputs. Its built-in unsigned control rows are integrity tests, not signature verification. The real repository's public signature/target check is a separate client operation with new caller-owned state and cache:

```sh
pxg repo verify --repo file:///ABSOLUTE/NEW_PUBLIC_REPOSITORY \
  --root /ABSOLUTE/NEW_PUBLIC_REPOSITORY/pinned-root.json \
  --state /ABSOLUTE/NEW_VERIFY_STATE --cache /ABSOLUTE/NEW_VERIFY_CACHE \
  --now 2026-11-26T00:00:00Z
```

Run that reader unprivileged, with the fixture clock explicitly supplied. It must report six verified targets and success. No publisher command or signing material is involved. Guest tests use this same pinned public input on a non-live synthetic root; filesystem qualification, installed execution and crash recovery still require their own actual guest records. Retain the approved public bytes in durable storage before the service artifact expires.

Until guest records exist, a successful producer dispatch and these public checks do not establish that installation or power-cut recovery worked on PAX.
