# Working on larder

Authority: `docs/{FORMAT,RECIPE,VERSION,SOLVER,CLI}.md`, with numbered rules;
`prediction.txt` records pm01's implementation prediction. The design of record
is pax trunk 5da8daaf, notes/pm00-the-design.md and notes/pm00/{matrix,SOURCES}.md.
The pm01 contract lives in wolf at dc6a5b1,
sprints/pm/01-the-format/pm01-the-format-and-harness.md.

- Keep this repository PRIVATE. No namespace registrations or publication.
- Clean room: never read implementation source of a package manager, version
  comparator, resolver, solver, compressor, archiver, signature/TLS/HTTP library.
  Specifications/docs only; std SHA-256 is reused, not reimplemented.
- Wolf 0.2.36, lupin 0.1.58, bundled std pinned in wolf-toolchain.toml.
- `TMPDIR` must be lane-local, never /tmp or /var/folders. Fetch first with
  tools/fetch-toolchain; build/check with tools/gauntlet from a committed copy.
- Runtime capabilities are env and fs for reading arguments and literal files;
  no root/cache/database mutation, no signing, fetching or process execution.
- Tests are first class. Add fixture CLI e2e and unit rows with every rule.
  Search/checker share data/version order only, never feasibility predicates.
- No attribution/co-author trailers, labels, merge, tag or release by lanes.
