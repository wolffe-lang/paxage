# Solver v1

## S1 — Snapshot and completeness

`DIR/snapshot.pxg` is an immutable F2 `snapshot { schema: 1, features: [], arch,
slot, packages, installed, holds, budget }`. packages contains F3 manifest
literals (maximum 24). installed and holds contain unique package IDs, spelled
`name@arch/slot=version`, each referring to exactly one manifest; holds is a
subset of installed. arch and slot are default request identity, never a host
probe. budget is positive, at most 100,000,000; default fixtures use 1,000,000.
No input directory is modified. No live installed state or trust is inferred.

Search is complete over all subsets of this bounded snapshot when enough budget
is available. A valid final set satisfies all requested requirements, all selected
packages' required edges, exact architecture and ABI slot constraints, symmetric
conflicts, holds and at most one version per `(name, arch, slot)`. It retains each
installed slot unless a selected package explicitly replaces the named old
package. Replacement is a proposed named removal, not deletion or overwrite: an installed
target cannot remain selected alongside its replacing package. Holds therefore
prevent such a replacement. Optional dependencies do not
extend the hard closure. A package from another architecture cannot be selected;
multiple explicit ABI slots of the target architecture may coexist.

## S2 — Deterministic policy and work bound

Candidates sort by version (descending, V1), then name, architecture, slot
(ASCII ascending) to break ties. Depth-first backtracking satisfies the first
unmet obligation: holds, wants in request order, selected packages' required
edges, then installed slots in installed order. For an installed slot, either a
same-slot candidate or an explicitly replacing candidate can discharge it.
Candidates already selected are not selected twice. Conflicting partial choices
backtrack. Thus the first complete plan uses latest compatible candidates; this
is not a global version-sum optimization or a minimum-download claim. Optional
edges never create obligations.
One recursive search node consumes one budget unit, including the root and leaf. Exceeding
budget returns no plan: `budget-exceeded`, exit 4. An exhaustive search with no
valid leaf returns `unsatisfiable`, exit 3. Neither returns a partial plan.

## S3 — Explanation and independent checker

A refusal identifies its category, snapshot package count, searched node count,
and the request-ordered wants and sorted hold/installed identities. UNSAT is a bounded exhaustive
proof for this exact snapshot, not a claim that no external package could help.
The explanation includes the first rejected leaf's named constraint (`want`,
`dependency`, `conflict`, `slot`, `architecture`, `hold`, `installed`) with the
responsible identity. Budget refusal says search incomplete explicitly.
A successful plan lists selected identities and proposed removals by name,
old identity and replacement reason. No implicit filesystem action.

A separately written checker validates selected IDs and all S1 constraints
without calling the search or its feasibility predicates. Solver and checker
share only data types, version policy and schema parsing. No plan is emitted
unless the checker accepts it; disagreement is `internal-plan-error`, exit 5.
Tests also enumerate every subset of at least 10,000 seeded small graphs,
compare existence and candidate policy, and check every returned plan. The seed
and graph count are printed. Handwritten rows cover budgets, ABI, holds, virtual
versions, symmetric conflicts, proposed replacements and optional edges.
