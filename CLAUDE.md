# Working on paxage

Authority: `docs/{FORMAT,RECIPE,VERSION,SOLVER,CLI}.md`, with numbered rules;
`prediction.txt` records pm01's implementation prediction. The design of record
is pax trunk 5da8daaf, notes/pm00-the-design.md and notes/pm00/{matrix,SOURCES}.md.
The pm01 contract lives in wolf at dc6a5b1,
sprints/pm/01-the-format/pm01-the-format-and-harness.md.

- Keep this repository PRIVATE. No namespace registrations or publication.
- Clean room: never read implementation source of a package manager, version
  comparator, resolver, solver, compressor, archiver, signature/TLS/HTTP library.
  Specifications/docs only; std SHA-256 is reused, not reimplemented.
- Wolf 0.2.38, lupin 0.1.60, std pinned in wolf-toolchain.toml.
- `TMPDIR` must be lane-local, never /tmp or /var/folders. Fetch first with
  tools/fetch-toolchain; build/check with tools/gauntlet from a committed copy.
- Runtime capabilities are env and fs. Root mutation happens only through the
  transaction verbs over a `--root` synthetic root (docs/TRANSACTIONS.md); no
  process execution (failpoint crashes are traps, never os_exit).
- Tests are first class. Add fixture CLI e2e and unit rows with every rule.
  Search/checker share data/version order only, never feasibility predicates.
- No attribution/co-author trailers, labels, merge, tag or release by lanes.
- The former name stays only in the records `tools/check-census` lists. A new
  lane note or prediction that must name it goes on that list by path.
