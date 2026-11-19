"""Table 10 bindings for invalid-input cases in Annex A.7."""

import pytest

from .provider import ref, uid
from .scenarios import change, package, query_for

pytestmark = pytest.mark.live

ELEMENTS = "getElementsByProjectCommit"
ELEMENT = "getElementByProjectCommitId"
RELATIONSHIPS = "getRelationshipsByProjectCommitRelatedElement"
BRANCH_CREATE = "postBranchByProject"
BRANCH_GET = "getBranchesByProjectAndId"
BRANCH_DELETE = "deleteBranchByProjectAndId"
PROJECT_GET = "getProjectById"
PROJECT_PUT = "putProjectById"
COMMIT_GET = "getCommitByProjectAndId"
COMMIT_OPS = (ELEMENTS, ELEMENT, RELATIONSHIPS + ":out", RELATIONSHIPS + ":in", BRANCH_CREATE)
PROJECT_OPS = (*COMMIT_OPS, "getBranchesByProject", BRANCH_GET, BRANCH_DELETE,
               PROJECT_GET + ":default-branch", PROJECT_PUT, "postCommitByProject", COMMIT_GET,
               BRANCH_GET + ":head", "postQueryByProject")
UUID_OPS = (PROJECT_GET, ELEMENT, RELATIONSHIPS + ":out", RELATIONSHIPS + ":in",
            BRANCH_GET, BRANCH_DELETE, PROJECT_PUT, COMMIT_GET)
CROSS_CASES = {
    1: PROJECT_OPS, 2: COMMIT_OPS, 3: PROJECT_OPS, 4: COMMIT_OPS,
    5: COMMIT_OPS, 6: ("postProject", BRANCH_CREATE), 7: UUID_OPS,
}


@pytest.mark.parametrize(
    "annex,binding",
    [pytest.param(case, operation, id=f"PIM-CC-{case:03}-{operation}")
     for case, operations in CROSS_CASES.items() for operation in operations],
)
def test_cross_cutting(api, annex, binding, record_property):
    operation, _, variant = binding.partition(":")
    record_property("annex_case", f"PIM-CC-{annex:03}")
    record_property("operation_id", operation)
    if annex == 1 or (annex == 2 and operation != BRANCH_CREATE) or (
        annex == 7 and operation != PROJECT_PUT
    ):
        pytest.skip("Missing mandatory path segment has no distinct Beta 1 REST operation")
    if annex == 7:
        pytest.skip("ProjectRequest.defaultBranch is optional on an update")

    if operation == "postProject":
        api.call(operation, body={}, status=(400,))
        return

    project = api.project()
    element = package("Element")
    commit = api.commit(project, [change(element)])
    branch = api.branch(project, commit)
    project_id = uid() if annex == 3 else project["@id"]
    commit_id = commit["@id"]
    if annex == 4:
        commit_id = uid()
    elif annex == 5:
        other = api.project()
        commit_id = api.commit(other, [change(package("Other"))])["@id"]

    scope = {"projectId": project_id}
    if operation in (ELEMENTS, ELEMENT, RELATIONSHIPS, COMMIT_GET):
        scope["commitId"] = commit_id
    if operation == ELEMENT:
        scope["elementId"] = element["@id"]
    if operation == RELATIONSHIPS:
        scope["relatedElementId"] = element["@id"]
    if operation in (BRANCH_GET, BRANCH_DELETE):
        scope["branchId"] = branch["@id"]
    bodies = {
        "postCommitByProject": {"change": [change(package("New"))]},
        BRANCH_CREATE: {"head": ref(commit_id)},
        PROJECT_PUT: {"name": project["name"]},
        "postQueryByProject": query_for("Package"),
    }
    if annex != 6:
        bodies[BRANCH_CREATE]["name"] = "cross-cutting"
    if annex == 2:
        del bodies[BRANCH_CREATE]["head"]
    if annex != 7:
        bodies[PROJECT_PUT]["defaultBranch"] = ref(branch)

    status = (400,) if annex in (2, 6) else (400, 404) if annex == 5 else (404,)
    api.call(operation, **scope, query={"direction": variant} if operation == RELATIONSHIPS else None,
             body=bodies.get(operation), status=status)
