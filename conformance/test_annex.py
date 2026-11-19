from uuid import UUID

import pytest

from .provider import ids, ref, uid
from .scenarios import change, expect_ids, model, package, query_for, query_results

pytestmark = pytest.mark.live


def test_project_service(api, annex, record_property):
    record_property("annex_case", f"PIM-PS-{annex:03}")
    if annex == 4:
        api.call("getProjectById", projectId=uid(), status=(404,))
        return
    baseline = ids(api.collection("getProjects")) if annex in (1, 2) else set()
    project = api.project()
    if annex == 1:
        assert UUID(project["@id"]).version == 4
        assert project["@id"] not in baseline
        assert project["name"].startswith("omg-beta1-")
        branch = api.call("getBranchesByProjectAndId", projectId=project["@id"],
                          branchId=project["defaultBranch"]["@id"])
        assert branch["owningProject"] == ref(project)
        assert branch["name"] == "main"
        assert UUID(branch["@id"]).version == 4
        assert branch["@id"] not in baseline | {project["@id"]}
        assert api.call("getProjectById", projectId=project["@id"]) == project
    elif annex == 2:
        assert ids(api.collection("getProjects", size=1)) == baseline | {project["@id"]}
    else:
        assert api.call("getProjectById", projectId=project["@id"]) == project


def test_element_navigation(api, annex, record_property):
    record_property("annex_case", f"PIM-EN-{annex:03}")
    project = api.project()
    commit, parent, child, membership, dependency = model(api, project)
    scope = {"projectId": project["@id"], "commitId": commit["@id"]}
    if annex == 1:
        expect_ids(api.collection("getElementsByProjectCommit", size=1, **scope),
                   parent, child, membership, dependency)
    elif annex == 2:
        element = api.call("getElementByProjectCommitId", **scope, elementId=parent["@id"])
        assert element["@id"] == parent["@id"]
        assert element["declaredName"] == parent["declaredName"]
        assert child["@id"] in ids(element["ownedElement"])
    elif annex == 3:
        later_element = package("Later")
        api.commit(project, [change(later_element)])
        api.call("getElementByProjectCommitId", **scope, elementId=later_element["@id"], status=(404,))
    else:
        direction, expected, field = (
            ("out", membership, "source") if annex == 4 else ("in", dependency, "target")
        )
        relationships = api.collection("getRelationshipsByProjectCommitRelatedElement",
                                       **scope, relatedElementId=parent["@id"],
                                       query={"direction": direction})
        expect_ids(relationships, expected)
        assert parent["@id"] in ids(relationships[0][field])


def test_versioning(api, annex, record_property):
    record_property("annex_case", f"PIM-PCB-{annex:03}")
    project = api.project()
    scope = {"projectId": project["@id"]}
    original = project["defaultBranch"]
    baseline = api.commit(project, [change(package("Baseline"))])
    if annex == 10:
        data = package("Addition")
        commit = api.commit(project, [change(data)])
        assert UUID(commit["@id"]).version == 4
        assert commit["@id"] != baseline["@id"]
        assert commit["owningProject"] == ref(project)
        assert commit["previousCommit"] == [ref(baseline)]
        branch = api.call("getBranchesByProjectAndId", **scope, branchId=original["@id"])
        assert branch["head"] == ref(commit)
        item = api.call("getElementByProjectCommitId", **scope,
                        commitId=commit["@id"], elementId=data["@id"])
        assert item["declaredName"] == data["declaredName"]
        return
    if annex in (11, 12):
        commit = baseline if annex == 11 else api.commit(api.project(), [change(package("Other"))])
        result = api.call("getCommitByProjectAndId", **scope, commitId=commit["@id"],
                          status=None if annex == 11 else (404,))
        if annex == 11:
            assert result == baseline
        return
    if annex in (4, 6, 9, 14, 15):
        if annex == 15:
            other = api.project()
            absent = api.branch(other, api.commit(other, [change(package("Other"))]))["@id"]
        else:
            absent = uid()
        if annex == 9:
            api.call("putProjectById", **scope,
                     body={"name": project["name"], "defaultBranch": ref(absent)}, status=(400, 404))
            assert api.call("getProjectById", **scope)["defaultBranch"] == original
        else:
            operation = "deleteBranchByProjectAndId" if annex == 6 else "getBranchesByProjectAndId"
            api.call(operation, **scope, branchId=absent, status=(404,))
        return
    branch = api.branch(project, baseline)
    if annex == 1:
        assert UUID(branch["@id"]).version == 4
        assert branch["@id"] != original["@id"]
        assert branch["owningProject"] == ref(project)
        assert branch["head"] == ref(baseline)
    elif annex == 2:
        expect_ids(api.collection("getBranchesByProject", **scope), original, branch)
    elif annex == 3:
        assert api.call("getBranchesByProjectAndId", **scope, branchId=branch["@id"]) == branch
    elif annex == 5:
        deleted = api.call("deleteBranchByProjectAndId", **scope, branchId=branch["@id"])
        if deleted is not None:
            assert deleted["@id"] == branch["@id"]
        api.call("getBranchesByProjectAndId", **scope, branchId=branch["@id"], status=(404,))
    elif annex in (7, 8):
        expected = original
        if annex == 8:
            expected = ref(branch)
            result = api.call("putProjectById", **scope,
                              body={"name": project["name"], "defaultBranch": expected})
            assert result["defaultBranch"] == expected
        actual = api.call("getProjectById", **scope)["defaultBranch"]
        assert actual == expected
        assert api.call("getBranchesByProjectAndId", **scope, branchId=actual["@id"])["@id"] == actual["@id"]
    else:
        head = api.call("getBranchesByProjectAndId", **scope, branchId=branch["@id"])["head"]
        assert api.call("getCommitByProjectAndId", **scope, commitId=head["@id"]) == baseline


def test_queries(api, annex, record_property):
    record_property("annex_case", f"PIM-QS-{annex:03}")
    project = api.project()
    scope = {"projectId": project["@id"]}
    body = query_for("Package", declaredName="Child")
    if annex == 1:
        query = api.call("postQueryByProject", **scope, body=body)
        assert UUID(query["@id"]).version == 4
        assert query["owningProject"] == ref(project)
        assert query["where"] == body["where"]
        assert api.call("getQueryByProjectAndId", **scope, queryId=query["@id"]) == query
    else:
        commit, _, child, _, _ = model(api, project)
        expect_ids(query_results(api, project, commit, body), child)


def test_external_relationship(api, annex, record_property):
    record_property("annex_case", f"PIM-ER-{annex:03}")
    project = api.project()
    element = package("Linked")
    external = {"@type": "ExternalData", "@id": uid(), "resourceIdentifier": "https://example.org/item"}
    link = {"@type": "ExternalRelationship", "@id": uid(), "elementEnd": ref(element),
            "externalDataEnd": ref(external), "language": None, "specification": None}
    before = api.commit(project, [change(element), change(external)])
    after = api.commit(project, [change(link)])
    body = query_for("ExternalRelationship", **({"@id": link["@id"]} if annex != 1 else {}))
    results = query_results(api, project, before if annex == 3 else after, body)
    if annex == 3:
        expect_ids(results)
    else:
        expect_ids(results, link)
        assert results[0]["externalDataEnd"] == ref(external)
        assert results[0]["elementEnd"] == ref(element)


def test_project_usage(api, record_property):
    record_property("annex_case", "PIM-PU-001")
    library, project = api.project(), api.project()
    item = package("Library")
    used = api.commit(library, [change(item)])
    usage = {"@type": "ProjectUsage", "@id": uid(), "usedProject": ref(library), "usedCommit": ref(used)}
    commit = api.commit(project, [change(usage)])
    results = query_results(api, project, commit, query_for("ProjectUsage"))
    expect_ids(results, usage)
    assert results[0]["usedCommit"] == ref(used)
    assert results[0]["usedProject"] == ref(library)
    scope = {"projectId": project["@id"], "commitId": commit["@id"]}
    assert api.call("getProjectUsageByProjectCommitElement", **scope,
                    elementId=item["@id"])["@id"] == usage["@id"]
    record = next(record for record in api.collection("getChangesByProjectCommit", **scope)
                  if record["payload"]["@type"] == "ProjectUsage")
    deleted = api.commit(project, [change(None, record["identity"])])
    expect_ids(query_results(api, project, deleted, query_for("ProjectUsage")))
    expect_ids(query_results(api, project, commit, query_for("ProjectUsage")), usage)
