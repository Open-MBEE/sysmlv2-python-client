import pytest

from sysmlv2_client import SysMLV2Client, SysMLV2NotFoundError

from .provider import ref, uid
from .scenarios import change, expect_ids, model, package

pytestmark = [pytest.mark.live, pytest.mark.interoperability]


@pytest.fixture
def client(api):
    svc_token = api.session.headers.get("X-SysMLv2-Svc-Token")
    bearer_token = api.session.headers.get("Authorization")
    # The local pilot accepts a placeholder when neither credential is configured.
    if svc_token is None and bearer_token is None:
        bearer_token = "Bearer pilot"
    return SysMLV2Client(api.url, bearer_token, svc_token=svc_token)


def test_client_reads_seeded_model(api, client):
    project = api.project()
    commit, parent, child, membership, dependency = model(api, project)
    assert client.get_project_by_id(project["@id"])["@id"] == project["@id"]
    assert client.get_commit_by_id(project["@id"], commit["@id"])["@id"] == commit["@id"]
    element = client.get_element(project["@id"], parent["@id"], commit["@id"])
    assert element["@id"] == parent["@id"]
    assert child["@id"] in {item["@id"] for item in element["ownedElement"]}
    expect_ids(client.list_elements(project["@id"], commit["@id"]),
               parent, child, membership, dependency)
    expect_ids(client.list_relationships(project["@id"], parent["@id"], commit["@id"], "both"),
               membership, dependency)


def test_client_writes_project_lifecycle(api, client):
    name = f"omg-beta1-{uid()}"
    project = client.create_project({"name": name})
    project_id = project["@id"]
    api.projects.append(project_id)
    assert client.get_project_by_id(project_id)["name"] == name

    element = package("Client-created package")
    commit = client.create_commit(project_id, {"change": [change(element)]})
    branch = client.create_branch(project_id, {"name": "test-branch", "head": ref(commit)})
    tag = client.create_tag(project_id, {"name": "test-tag", "taggedCommit": ref(commit)})
    assert client.get_element(project_id, element["@id"], commit["@id"])["@id"] == element["@id"]
    assert client.get_branch_by_id(project_id, branch["@id"])["head"] == ref(commit)
    assert client.get_tag_by_id(project_id, tag["@id"])["taggedCommit"] == ref(commit)

    client.delete_tag(project_id, tag["@id"])
    client.delete_branch(project_id, branch["@id"])
    client.delete_project(project_id)
    with pytest.raises(SysMLV2NotFoundError):
        client.get_project_by_id(project_id)
    api.projects.remove(project_id)
