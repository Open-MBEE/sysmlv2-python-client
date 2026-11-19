# OMG Systems Modeling API 1.0 Beta 1 REST/HTTP conformance

The provider suite translates Annex A and Clause 8.1 into live pytest checks. It indexes all 37 published Annex A case IDs and all 35 operations in the Beta 1 OpenAPI artifact. It checks wire status, media type, JSON shape, and observable state. It also includes a separate Python client interoperability scenario.

## Run

From the repository root, install the project and the suite dependencies, then run the offline harness checks.

```sh
python -m pip install -e . -r conformance/requirements.txt
python -m pytest -c conformance/pytest.ini conformance -m "not live"
```

Set `SYSML_CONFORMANCE_URL` to the REST API base URL. Set `SYSML_CONFORMANCE_TOKEN` to the raw JWT or the full `Bearer <JWT>` value used by the notebook when the provider requires authentication. Supply secrets through the process environment. Use an isolated provider or test tenant. The suite creates projects named `omg-beta1-<UUID>`, uses those projects for writes, and attempts to delete them in teardown. Reported cleanup errors warrant checking the provider for leftover fixtures before retrying.

```sh
python -m pytest -c conformance/pytest.ini conformance -m "live and not interoperability" --live --provider-build "provider name and deployed revision" --junitxml=conformance/results/provider.xml
python -m pytest -c conformance/pytest.ini conformance -m interoperability --live --provider-build "provider name and deployed revision" --junitxml=conformance/results/client.xml
```

For the Flexo gateway, set `SYSML_CONFORMANCE_SVC_TOKEN` to the opaque token sent in the `X-SysMLv2-Svc-Token` header. Set both credential variables if the deployment requires both headers. For GitHub Actions, use a secret with the same name.

Use `-k PIM-PS` for the Annex A.1 slice or select the pytest nodes in the matrices. Some scenarios use other services to create their fixtures. A blocked fixture provides no result for the operation it was meant to exercise. Raw HTTP evidence in JUnit records operation IDs and statuses. Result files are ignored by Git.

For manual CI runs, configure the `sysml-conformance` GitHub environment with the URL variable and optional token secret named above, then dispatch **OMG Beta 1 REST conformance** with the provider revision. The workflow uploads JUnit results even when tests fail.

## References and coverage

- [Artifact manifest](references/manifest.json) records OMG file IDs, original URLs, and SHA-256 checksums for the unmodified PDF, OpenAPI, and schema documents. [OMG Beta 1 artifact index](https://www.omg.org/spec/SystemsModelingAPI/1.0/Beta1/About-SystemsModelingAPI)
- [Annex A case matrix](matrices/annex-a.csv) maps every case ID and its exercised REST operation or composition to pytest nodes. [REST operation matrix](matrices/rest-operations.csv) maps every OpenAPI operation to positive coverage. [Service matrix](matrices/services.md) records the Table 10 mapping.
- The project/commit/branch/tag, element mutation, ownership and query recipes informed the small fixtures in `scenarios.py`. The dated Cookbook release and OMG archive preserve the baseline. [Cookbook 2023-02](https://github.com/Systems-Modeling/SysML-v2-API-Cookbook/releases/tag/2023-02) · [OMG Cookbook archive](https://www.omg.org/cgi-bin/doc?ad/23-02-27.zip)
- To reproduce against the pilot, check out API Services tag `2023-02` (release commit starts with `2487e7c`), use its JDK 11, sbt/Play and PostgreSQL setup, then point the runner at `http://localhost:9000`. Its controller tests and Postman collection can help diagnose discrepancies. [API Services releases](https://github.com/Systems-Modeling/SysML-v2-API-Services/releases) · [Pilot setup](https://github.com/Systems-Modeling/SysML-v2-API-Services#setting-up-pilot-implementation-of-sysml-v2-api-and-services-on-your-local-machine)
- Flexo is another REST target. Use its SysML v2 API URL and a token issued for that deployment. [OpenMBEE Flexo documentation](https://github.com/Open-MBEE/flexo-mms.openmbee.org)

## Beta 1 limits to account for when reviewing results

- The OpenAPI file has an empty `components.schemas` map. The validator binds those pointers to the corresponding IDs in the published JSON schema bundle and resolves references locally. It registers `PrimitiveConstraintRequest` under its referenced URI to resolve the duplicate ID. The bundle has request schemas for SysML elements and relationships, so the suite uses those plus required response identity as a partial validation of those response types.
- Missing mandatory path parameters have no distinct operation in the binding. Removing a segment can address a different resource. Those rows are recorded as blocked. For A.7 missing branch head, the request omits the required key. An explicit null is permitted by the REST schema. Omission of `ProjectRequest.defaultBranch` is allowed on project updates.
- The REST schemas omit explicit predecessors in `CommitRequest` and scope and ordering in `QueryRequest`. The corresponding Annex A rows test the behavior the binding exposes and are marked partial. A missing external relationship is an empty result through the Table 10 query mapping.
- The suite covers the REST/HTTP binding. Optional Derived Property Conformance, the OSLC binding, and proposed PIM-only bindings require additional coverage. A passing pytest status alone does not establish Clause 2 conformance when a required assertion is blocked, partial, or unverified.
- [Starforge run record](starforge-results.md) documents the authenticated attempt and its outcome.
