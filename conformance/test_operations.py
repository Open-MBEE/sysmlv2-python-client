"""Coverage beyond the individual Annex A scenarios."""

import pytest

from .provider import API_NS, ids, ref, uid
from .scenarios import change, expect_ids, model, package, query_for, query_results

pytestmark = pytest.mark.live


def test_project_update_delete(api):
    project = api.project()
    scope = {"projectId": project["@id"]}
    body = {"name": project["name"] + "-updated", "description": "Beta 1 conformance"}
    updated = api.call("putProjectById", **scope, body=body)
    assert updated["@id"] == project["@id"]
    assert updated["name"] == body["name"]
    assert updated["description"] == body["description"]
    assert api.call("getProjectById", **scope) == updated
    deleted = api.call("deleteProjectById", **scope)
    api.projects.remove(project["@id"])
    if deleted is not None:
        assert deleted["@id"] == project["@id"]
    api.call("getProjectById", **scope, status=(404,))


def test_root_elements(api):
    project = api.project()
    commit, parent, child, _, _ = model(api, project)
    scope = {"projectId": project["@id"], "commitId": commit["@id"]}
    roots = ids(api.collection("getRootsByProjectCommit", **scope))
    assert parent["@id"] in roots
    assert child["@id"] not in roots


def test_relationships_both(api):
    project = api.project()
    commit, parent, _, membership, dependency = model(api, project)
    scope = {"projectId": project["@id"], "commitId": commit["@id"],
             "relatedElementId": parent["@id"]}
    for query in (None, {"direction": "both"}):
        expect_ids(api.collection("getRelationshipsByProjectCommitRelatedElement",
                                  query=query, **scope), membership, dependency)


def test_element_versions_and_diff(api):
    project = api.project()
    item = package("Before")
    first = api.commit(project, [change(item)])
    scope = {"projectId": project["@id"]}
    first_scope = dict(scope, commitId=first["@id"])
    versions = api.collection("getChangesByProjectCommit", **first_scope)
    assert len(versions) == 1
    version = versions[0]
    assert version["payload"]["@id"] == item["@id"]
    assert api.call("getChangeByProjectCommitId", **first_scope, changeId=version["@id"]) == version
    updated = dict(item, declaredName="After")
    second = api.commit(project, [change(updated, version["identity"])])
    third = api.commit(project, [change(None, version["identity"])])
    expect_ids(api.collection("getCommitsByProject", **scope), first, second, third)
    for commit, expected in ((first, item), (second, updated)):
        actual = api.call("getElementByProjectCommitId", **scope,
                          commitId=commit["@id"], elementId=item["@id"])
        assert actual["declaredName"] == expected["declaredName"]
    api.call("getElementByProjectCommitId", **scope, commitId=third["@id"],
             elementId=item["@id"], status=(404,))
    differences = api.call("diff", **scope, compareCommitId=second["@id"],
                           query={"baseCommitId": first["@id"]})
    assert len(differences) == 1
    assert differences[0]["baseData"]["payload"]["declaredName"] == "Before"
    assert differences[0]["compareData"]["payload"]["declaredName"] == "After"


def test_tags(api):
    project = api.project()
    commit = api.commit(project, [change(package("Baseline"))])
    scope = {"projectId": project["@id"]}
    tag = api.call("postTagByProject", **scope, body={"name": "baseline", "taggedCommit": ref(commit)})
    assert tag["taggedCommit"] == ref(commit)
    assert tag["owningProject"] == ref(project)
    expect_ids(api.collection("getTagsByProject", **scope), tag)
    tag_scope = dict(scope, tagId=tag["@id"])
    assert api.call("getTagByProjectAndId", **tag_scope) == tag
    assert api.call("getCommitByProjectAndId", **scope,
                    commitId=tag["taggedCommit"]["@id"]) == commit
    deleted = api.call("deleteTagByProjectAndId", **tag_scope)
    if deleted is not None:
        assert deleted["@id"] == tag["@id"]
    api.call("getTagByProjectAndId", **tag_scope, status=(404,))


def test_merge(api):
    project = api.project()
    base = api.commit(project, [change(package("Baseline"))])
    branch = api.branch(project, base)
    addition = package("Source")
    source = api.commit(project, [change(addition)], branch)
    target = project["defaultBranch"]
    scope = {"projectId": project["@id"]}
    merged = api.call("merge", **scope, targetBranchId=target["@id"],
                      query={"sourceCommitId": [source["@id"]]})
    assert source["@id"] in ids(merged["previousCommit"])
    assert api.call("getBranchesByProjectAndId", **scope, branchId=target["@id"])["head"] == ref(merged)
    assert api.call("getElementByProjectCommitId", **scope, commitId=merged["@id"],
                    elementId=addition["@id"])["declaredName"] == "Source"


def test_query_lifecycle_and_ad_hoc(api):
    project = api.project()
    commit, parent, child, _, _ = model(api, project)
    scope = {"projectId": project["@id"]}
    at_commit = {"commitId": commit["@id"]}
    first = query_for("Package", declaredName="Parent")
    second = query_for("Package", declaredName="Child")
    saved = api.call("postQueryByProject", **scope, body=first)
    saved_scope = dict(scope, queryId=saved["@id"])
    expect_ids(api.collection("getQueriesByProject", **scope), saved)
    expect_ids(api.collection("getQueryResultsByProjectIdQueryId", **saved_scope,
                              query=at_commit), parent)
    updated = api.call("putQueryByProjectAndId", **saved_scope, body=second)
    assert updated["@id"] == saved["@id"]
    expect_ids(api.collection("getQueryResultsByProjectIdQueryId", **saved_scope,
                              query=at_commit), child)
    for operation in ("getQueryResultsByProjectIdQuery", "getQueryResultsByProjectIdQueryPost"):
        expect_ids(api.call(operation, **scope, query=at_commit, body=first), parent)
    deleted = api.call("deleteQueryByProjectAndId", **saved_scope)
    if deleted is not None:
        assert deleted["@id"] == saved["@id"]
    api.call("getQueryByProjectAndId", **saved_scope, status=(404,))


def test_external_relationships_by_element(api):
    project = api.project()
    matched, other = package("Matched"), package("Other")
    external = {"@type": "ExternalData", "@id": uid(), "resourceIdentifier": "https://example.org/item"}
    links = [
        {"@type": "ExternalRelationship", "@id": uid(), "elementEnd": ref(item),
         "externalDataEnd": ref(external), "language": None, "specification": None}
        for item in (matched, other)
    ]
    commit = api.commit(project, [change(item) for item in (matched, other, external, *links)])
    expect_ids(query_results(api, project, commit,
                             query_for("ExternalRelationship", elementEnd=matched["@id"])), links[0])


def test_datatype_contract(api):
    document = api.call("getDatatypes")
    assert "Project" in document["$defs"]
    datatype = api.call("getDatatypeById", datatypeId=API_NS + "Project")
    assert datatype["$id"] == API_NS + "Project"
    assert datatype["title"] == "Project"
