# REST/HTTP service mapping

Clause 8.1 Table 10 composes some PIM operations from multiple HTTP calls.

| Clause 2 service | Annex | REST operations and composite behaviors |
| --- | --- | --- |
| ProjectService | A.1 | Project create, list, read, update, delete. |
| ElementNavigationService | A.2 | Commit elements, individual elements, roots, relationships in/out/both. Ownership traversal reads element properties. |
| ProjectDataVersioningService | A.3 | Branch, tag, commit, change, diff and merge operations. Read or set the default branch through the project. Resolve a head or tagged commit through the branch or tag and then the commit. |
| QueryService | A.4 | Saved-query CRUD and execution, plus GET and POST ad hoc execution. |
| ExternalRelationshipService | A.5 | Saved-query execution with type, ID and element-end predicates. |
| ProjectUsageService | A.6 | Saved-query execution, commit changes for creating and deleting usages, and OpenAPI's element-to-usage lookup. |
| Cross-cutting | A.7 | Invalid inputs per bound operation. Wire cases without a distinct operation are marked blocked. |
| REST metadata | OpenAPI | Both datatype endpoints. These are outside the Clause 2 service claims. |
