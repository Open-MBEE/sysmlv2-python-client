# Starforge REST API conformance test report

The authenticated rerun on 18 November 2026 found two differences from the pinned OMG Systems Modeling API 1.0 Beta 1 REST/HTTP contract. The deployed OpenMBEE Flexo revision was unknown. The run took 98 seconds and recorded zero HTTP 401 or 403 responses.

| Test group | Passed | Failed in pytest | Skipped |
| --- | ---: | ---: | ---: |
| Annex A service cases | 1 | 29 | 0 |
| Annex A.7 cross-cutting variants | 1 | 26 | 26 |
| Additional REST operation checks | 0 | 9 | 0 |
| Python client interoperability | 0 | 1 | 0 |
| **Total** | **2** | **65** | **26** |

Eight offline checks were deselected. The [Annex A matrix](matrices/annex-a.csv) documents the 26 skips.

| Operation | Expected | Observed | Effect |
| --- | --- | --- | --- |
| `POST /projects` with a valid request | HTTP 201 | HTTP 200. A separate diagnostic confirmed that the returned Project passed schema validation and could be read back. | One direct failure and 63 checks blocked during project fixture setup. |
| `GET /meta/datatypes/{datatypeId}` with the URL-encoded Beta 1 Project URI | HTTP 200 | HTTP 404. The preceding datatype listing returned HTTP 200. | One independent metadata failure. |

The passing checks were PIM-PS-004 (missing project returns HTTP 404) and the project-creation variant of PIM-CC-006 (missing name returns HTTP 400). All 64 suite cleanup deletions returned HTTP 200. The separate diagnostic project returned HTTP 404 on read-back after deletion.

The run did not establish provider conformance. The blocked operations remain unverified. The local JUnit file was written to `conformance/results/starforge-rerun.xml`.

[OMG Beta 1 OpenAPI contract](https://www.omg.org/spec/SystemsModelingAPI/20230201/OpenAPI.json) · [Pinned artifact manifest](references/manifest.json)
