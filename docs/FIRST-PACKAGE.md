# First package from the live repository

The public repository is `https://pkg.lupp.us/pax/`. The released 0.2.1 Linux
x86-64 client has fetched, staged and installed a package from it into a scratch
journalled filesystem. This is an experimental, disposable-root example, not
permission to manage the running `/`. PAX guest network installation is not
claimed here. macOS roots are development roots and carry no durability claim;
a Linux package may be inspected or staged there, but its ELF is not a macOS
program to execute.

Use the [released client](../README.md#install-021), Python 3 and curl. Keep the
client outside the working directory and replace the absolute path below. Run
as an ordinary user, not with `sudo`. **Stop if any command fails.** Do not run
the later steps after a failed checksum, TLS, freshness or signature check.

```sh
PXG=/absolute/path/to/pxg
"$PXG" --version
umask 077
mkdir first-package
cd first-package
REPO=https://pkg.lupp.us/pax/
```

The working directory must be new, private and owned by you. Keep your system
clock at current UTC. TLS certificate validity and signed-metadata expiry use
the command's fixed start time; do not pass `--now` to work around an expiry or
clock refusal. A missing or wrong clock is a prerequisite to fix, not a reason
to weaken verification.

## 1. Authenticate the repository root

Follow [Trust anchor](TRUST-ANCHOR.md#check-a-download-before-bootstrap) to
download `1.root.json` into this directory and verify its exact SHA-256 and
2,305-byte size. Use the fingerprint published on that page, not a checksum
fetched alongside the root from the repository. A mismatch means stop and
report it. Keep this checked file for both the trust-only commands and `init`.

This public TUF root and the TLS CA bundle below serve different purposes.
Neither replaces the other.

## 2. Supply TLS CA roots

The client's default is `/etc/ssl/certs/ca-roots.der`, a concatenation of DER
certificates. It is not a PEM file or a directory of certificates, and it is not
normally present at that path on Linux or macOS. `--tls-roots FILE` selects an
explicit file; no environment variable selects one. This example prepares a
public bundle using the same published inputs pinned for PAX's bundle:

- Mozilla CA extract from curl, dated 2026-10-20, 118 certificates:
  `https://curl.se/ca/cacert-2026-10-20.pem`
- PEM SHA-256:
  `796f1389bfea13c0ed78f663b765baaff54a508e5483786bd6ece73c5e3e3cbe`
- Concatenated DER SHA-256:
  `7a713f238d42397d0360c7f8523d45bedee6824f583372d6afd96a129ea5c1f1`

Download, check the public PEM bytes, convert only certificate blocks and check
the resulting DER bytes. Python's standard library conversion works on both
platforms; it does not use a platform-specific certificate directory.

```sh
curl --disable --proto '=https' --fail --silent --show-error \
  https://curl.se/ca/cacert-2026-10-20.pem -o cacert.pem
python3 -I - <<'PY'
import hashlib
import re
import ssl
from pathlib import Path
pem = Path('cacert.pem').read_bytes()
if hashlib.sha256(pem).hexdigest() != '796f1389bfea13c0ed78f663b765baaff54a508e5483786bd6ece73c5e3e3cbe':
    raise SystemExit('STOP: public CA download does not match')
blocks = re.findall(r'-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----',
                    pem.decode('ascii'), re.S)
if len(blocks) != 118:
    raise SystemExit('STOP: unexpected public certificate count')
der = b''.join(ssl.PEM_cert_to_DER_cert(block) for block in blocks)
if hashlib.sha256(der).hexdigest() != '7a713f238d42397d0360c7f8523d45bedee6824f583372d6afd96a129ea5c1f1':
    raise SystemExit('STOP: converted CA bundle does not match')
with Path('ca-roots.der').open('xb') as output:
    output.write(der)
print('Public CA bundle matches; 118 certificates')
PY
TLS_ROOTS="$PWD/ca-roots.der"
```

If you already have an authenticated, suitable public bundle, convert its PEM
certificates to concatenated DER and identify its source and digest explicitly;
this page's two CA digests apply only to the dated download above. Never turn
certificate checking off. A future CA update needs a separately reviewed input,
not a changed checksum chosen to make a failing download pass.

## 3. Refresh and inspect authenticated offerings

```sh
"$PXG" bootstrap --repo "$REPO" --root "$PWD/1.root.json" --state "$PWD/trust"
"$PXG" update --repo "$REPO" --state "$PWD/trust" --tls-roots "$TLS_ROOTS"
```

Bootstrap creates fresh private trust state; it does not discover an anchor.
Update must succeed before a target is usable. An expired timestamp, rollback,
bad signature or TLS error is a refusal, not permission to delete this state or
fetch through another transport.

There is no live list/search verb in 0.2.1. After a successful update, inspect
its authenticated current targets file. The current pointer chooses the
accepted generation; do not select an arbitrary saved file by its name.

```sh
GEN=$(python3 -I - <<'PY'
import json
from pathlib import Path
value = json.loads(Path('trust/current').read_text())['generation']
if type(value) is not int or value < 1:
    raise SystemExit('STOP: invalid accepted trust generation')
print(value)
PY
)
"$PXG" repo inspect --file "$PWD/trust/g$GEN/targets.json"
```

Targets output has `entry NAME VERSION KIND LENGTH SHA256` rows. Choose a
currently offered payload and its exact package version. The repository may
change between commands: do not assume an old example version remains
available or combine metadata and payloads from different accepted chains.
`repo inspect` alone is an inspection command, not a substitute for the
successful authenticated update above.

## 4. Fetch and stage a current package

Replace both values below from that inspection. `PAYLOAD` is the logical
payload target name, not a URL or its hash-prefixed download filename. For
example, an offered scent version `0.2.0~pre1-1` would have the logical name
`scent-0.2.0~pre1-1.payload.tar`; this is an example, not a promise that it is
still offered.

```sh
VERSION='replace-with-an-offered-version'
PAYLOAD="scent-$VERSION.payload.tar"
mkdir stage
chmod 700 stage
"$PXG" fetch --repo "$REPO" --state "$PWD/trust" --cache "$PWD/cache" \
  --target "$PAYLOAD" --stage "$PWD/stage" --tls-roots "$TLS_ROOTS"
```

Fetch rechecks the chain and authenticates the payload, manifest and buildinfo;
staging checks complete bytes and inventory. `fetch ok` is not an installation.
If staging refuses `directory-owner`, check that the directory is empty, real,
owned by your current user and not group- or world-writable. Do not run the
trust/staging commands as root to evade the refusal. Use a new private stage
for another attempt rather than treating a failed partial tree as verified.

## 5. Install only into a disposable root

On Linux, put the working root on ext3/ext4 with its own active journal; an
unjournalled or read-only filesystem is refused. Do not use `/`, a mount alias
of it, or system directories. A separate non-root filesystem does not require
permission to mutate the running root. On macOS this is logical development
installation only, not a filesystem durability result.

```sh
mkdir root
"$PXG" init --root "$PWD/root" --repo "$REPO" --pinned-root "$PWD/1.root.json" \
  --arch x86_64 --slot default
"$PXG" install --root "$PWD/root" "scent=$VERSION" --tls-roots "$TLS_ROOTS"
"$PXG" verify --root "$PWD/root"
"$PXG" status --root "$PWD/root" --json
```

The root owns its own trust state and cache; these commands do not adopt the
separate inspection state or stage. Install refreshes and verifies its own
chain, so a package that disappeared since inspection can refuse rather than
installing the staged prefix. Successful `verify` and `status` should agree on
the selected exact version. Do not execute a Linux ELF on macOS. Installing
into `/`, manager self-update, boot changes and online replacement of in-use
files remain outside this walkthrough.

If a download is truncated or a connection drops, follow the reported refusal
and bounded retry behavior; unverified `.part` bytes are not an installed
package. Preserve diagnostics and accepted trust state. Do not disable length,
hash, signature, time or TLS checks. Report unexpected behavior through the
[issue tracker](https://github.com/wolffe-lang/paxage/issues).

See [CLI](CLI.md#c9--bootstrap-and-update), [Trust profile](TRUST.md#t21--network-transport)
and [Transactions](TRANSACTIONS.md) for exact limits and refusal rules.
