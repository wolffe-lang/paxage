# Trust anchor

The initial public trust root for `https://pkg.lupp.us/pax/` is the following
version 1 metadata file. Its fingerprint was confirmed independently of the
repository download. This page and the release notes publish that identity
separately from the repository it authenticates.

SHA-256: `c770e228533144c436ae8e5ee8d62de0a74f56c5bf9e7aade0259701b7b2b0f3`

- File: `metadata/1.root.json`
- Size: 2,305 bytes
- Version: 1
- Expires: `2027-11-24T00:00:00Z`
- Root threshold: 2 of 3

The three root-role key IDs are:

```text
03bebe4e1fb532ef1c0e42f6ea1ba995c90d096468f0b7963b788d453cb1f02d
27afc285c504af7ced0909838c4d03bea86d1778ee5d4da8f831a065ebefb567
42d930f347a5ae8827b52d2b35894c6124d22480e26b0b376f8c1ab347e82c62
```

These are root-role IDs, not the IDs for the other metadata roles. The
fingerprint identifies the exact complete file, including its signatures and
whitespace. Do not reformat it before checking.

## Check a download before bootstrap

Download into a new private working directory, then check the bytes before
passing the file to `bootstrap --root` or `init --pinned-root`:

```sh
curl --disable --proto '=https' --fail --silent --show-error \
  https://pkg.lupp.us/pax/metadata/1.root.json -o 1.root.json
python3 -I - <<'PY'
import hashlib
from pathlib import Path
raw = Path('1.root.json').read_bytes()
expected = 'c770e228533144c436ae8e5ee8d62de0a74f56c5bf9e7aade0259701b7b2b0f3'
actual = hashlib.sha256(raw).hexdigest()
if len(raw) != 2305 or actual != expected:
    raise SystemExit('STOP: trust root fingerprint or size does not match')
print('Trust root matches:', actual, len(raw), 'bytes')
PY
```

For a file already downloaded, run just the Python check. Alternatively,
compare `sha256sum 1.root.json` on Linux or `shasum -a 256 1.root.json` on macOS
with the full fingerprint above, and check `wc -c < 1.root.json` is 2305.

On any mismatch, **stop**. Do not bootstrap, install, overwrite existing trust
state, accept a replacement fingerprint from the same download location, or
change the expected value to make the check pass. Keep the downloaded file and
report its URL, observed digest and size through the
[issue tracker](https://github.com/wolffe-lang/paxage/issues).

A matching digest supplies this bootstrap identity; the client still validates
the root's structure and threshold. HTTPS certificate validation is a separate
layer and needs a public TLS CA bundle. A root's self-signature or a fingerprint
served alongside it does not by itself establish independent provenance.

After bootstrap, let the client verify sequential root rotations using its
existing trusted state. Do not replace that state with a newly downloaded root
or bypass expiry by changing the clock. If this pinned root is expired when
starting a new state, stop and consult updated, independently authenticated
instructions rather than guessing a newer anchor.

See [First package](FIRST-PACKAGE.md) for TLS roots, current time, repository
inspection and a disposable installation. [Trust profile](TRUST.md) describes
rotation, metadata freshness and rollback limits.
