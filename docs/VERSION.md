# Version order v1

## V1 — Authority

The following policy is copied verbatim from the PAX design at `5da8daaf`.
It is paxage's own order, not
Arch's, RPM's or Debian's. No imported comparator or vectors are used.

Version v1 is **epoch:upstream-release**: nonnegative decimal epoch (omitted means 0); nonempty upstream restricted to ASCII letters/digits plus `.`, `_`, `+`, `~`; positive integer package release. Compare epoch, then upstream tokens, then release. Tokenize maximal digit runs, maximal letter runs and individual punctuation; order token classes `~ < end < separator < letters < digits`. Separators compare ASCII (`+ < . < _`); letter runs compare case-sensitive ASCII lexicographically; digit runs strip leading zeroes and compare length then bytes, with all-zero runs equal. Numeric comparisons never parse into a bounded integer. Thus `1~rc < 1 < 1.0`, `1.0` equals `1.00` at the upstream level, and an epoch increase dominates all upstream changes. Reject comparator-equal duplicate versions for a name/slot in one snapshot. This is a new, versioned distro policy, **not Arch/RPM/Debian compatibility**; pm01 freezes this token-order proposal with golden/property vectors before publication. Upstream version strings requiring other semantics need an explicit recipe mapping plus provenance, not a guessed semver conversion. Epoch and release handle upstream resets and recipe rebuilds. No existing package namespace is imported implicitly.

## V2 — Syntax and bounds

CLI and manifest versions require the final `-release`; the abbreviated upstream
examples in V1 mean release 1. Only one colon and one hyphen are permitted, no
signs, whitespace, empty components or Unicode. Release must contain a nonzero
digit. Epoch/release may have leading zeroes. Maximum encoded version: 4096 bytes.
Epoch and release, like upstream digit tokens, compare without bounded integers.

## V3 — Golden and property rows

`tests/versions.tsv` is hand-derived from V1, not another tool.
Generated version sets check reflexivity, antisymmetry, transitivity, epoch
precedence, zero normalization and the V1 examples. `compare` emits -1, 0 or 1.
