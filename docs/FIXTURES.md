# Disposable install fixture

`fixture-producer.yml` runs only by an explicit hosted dispatch. It never publishes to a package site. It creates a test-only signed repository containing two static scent packages for install, upgrade, removal and recovery tests.

The source inputs are `tests/fixture-producer-inputs.json`: an immutable Ubuntu image digest, an immutable authenticated APT snapshot, a digest-checked public CA bundle for download bootstrap, and two scent source commits/archive digests. Each scent tree fetches and checks its own compiler/runtime/std pin. Each package has its source's unmodified static scent executable, license and a test-version marker. Package versions `1-1` and `2-1` are fixture identities, not upstream release claims. The two executable hashes must differ.

Two independent builds compile paxage and both scent inputs, pack both packages, initialize/sign repository metadata with the existing test publisher, and verify the public repository with the client. The public inventories and canonical tar bytes must agree before anything is exported. The fixed epoch is 2026-11-26T00:00:00Z; metadata validity is one year. Use the descriptor's clock window in guest tests. A future fixture update must review its epoch and source pins rather than silently mixing in the current time.

## Signing boundary

The isolated hosted container derives disposable role material internally from fixed versioned labels. No seed, key path, production root or production credential is a workflow input. The publisher is unprivileged and accepts only its marked test material. The helper refuses ordinary local runs, root and non-dispatch environments; these checks are guardrails, not a production security boundary.

The source checkout is read-only inside the container. Private temporary work stays inside its ephemeral filesystem, not a host-mounted output directory. The producer receives a cleared environment without the checkout credentials or the workflow's service credentials. Child arguments, private bytes and captured child output are never logged. No cache or failure-time workspace upload is configured.

Local tests never generate or load signing material. They cover the public comparator, controlled-clock sensitivity, canonical archive metadata, export allowlists, digest binding, unsafe source paths and refusal of local signing. Their unsigned public JSON stubs are deliberately not installable repositories and are not substitutes for a successful producer dispatch.

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

Until that dispatch and digest pin exist, guest install/power-cut tests have no fixture result. No production publication is needed, but a pure local comparator pass does not establish that the hosted build, signing path or resulting PAX executable worked.
