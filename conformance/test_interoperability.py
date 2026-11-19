import pytest

from .scenarios import expect_ids, model

pytestmark = [pytest.mark.live, pytest.mark.interoperability]


def test_client_reads_seeded_model(api):
    from sysmlv2_client import SysMLV2Client

    project = api.project()
    commit, parent, child, membership, dependency = model(api, project)
    # The client requires a Bearer header even for a local unauthenticated pilot.
    client = SysMLV2Client(api.url, api.session.headers.get("Authorization", "Bearer pilot"))
    assert client.get_project_by_id(project["@id"])["@id"] == project["@id"]
    assert client.get_commit_by_id(project["@id"], commit["@id"])["@id"] == commit["@id"]
    element = client.get_element(project["@id"], parent["@id"], commit["@id"])
    assert element["@id"] == parent["@id"]
    assert child["@id"] in {item["@id"] for item in element["ownedElement"]}
    expect_ids(client.list_elements(project["@id"], commit["@id"]),
               parent, child, membership, dependency)
    expect_ids(client.list_relationships(project["@id"], parent["@id"], commit["@id"], "both"),
               membership, dependency)
