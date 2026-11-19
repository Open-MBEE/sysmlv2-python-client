import csv
from hashlib import sha256
import json
from unittest.mock import Mock

import pytest
from requests import Response

from .conftest import ANNEX_GROUPS
from .provider import API_NS, OPERATIONS, ROOT, Provider, ref, uid, validate
from .scenarios import model, query_for
from .test_cross_cutting import CROSS_CASES


def matrix(name):
    with (ROOT / "matrices" / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_pinned_references():
    folder = ROOT / "references"
    manifest = json.loads((folder / "manifest.json").read_bytes())
    for filename, source in manifest.items():
        assert sha256((folder / filename).read_bytes()).hexdigest() == source["sha256"]


def test_matrices_cover_published_ids(request):
    annex = matrix("annex-a.csv")
    rest = matrix("rest-operations.csv")
    expected = {
        f"PIM-{prefix}-{number:03}"
        for prefix, count in ANNEX_GROUPS.values()
        for number in range(1, count + 1)
    } | {"PIM-PU-001"} | {f"PIM-CC-{number:03}" for number in CROSS_CASES}
    assert len(expected) == 37
    assert {row["case_id"] for row in annex} == expected
    assert len(rest) == len(OPERATIONS) == 35
    assert {row["operation_id"] for row in rest} == set(OPERATIONS)
    for row in rest:
        method, path, _ = OPERATIONS[row["operation_id"]]
        assert (row["method"], row["path"]) == (method.upper(), path)
    collected = {
        item.nodeid.removeprefix("conformance/") for item in request.session.items
    }
    if any(node.startswith("test_annex.py::") for node in collected):
        assert {row["pytest_node"] for row in annex + rest} <= collected


def test_fixture_payloads_validate_offline():
    provider = Mock()
    model(provider, {})
    changes = provider.commit.call_args.args[1]
    validate({"$ref": API_NS + "CommitRequest"}, {"change": changes}, "model fixture")
    validate({"$ref": API_NS + "QueryRequest"},
             query_for("Package", declaredName="Child"), "query fixture")
    with pytest.raises(AssertionError, match="JSON validation failed"):
        validate({"$ref": API_NS + "ProjectRequest"}, {}, "missing name")


def mock_json(payload, status=200):
    result = Response()
    result.status_code = status
    result.headers["Content-Type"] = "application/json"
    result._content = json.dumps(payload).encode()
    return result


@pytest.mark.parametrize(
    "value", ["example.jwt.value", "Bearer example.jwt.value", "  bearer  example.jwt.value  "],
)
def test_provider_accepts_notebook_and_raw_tokens(value):
    with Provider("https://fixture.example.org", value).session as session:
        assert session.headers["Authorization"] == "Bearer example.jwt.value"


def test_invalid_creation_response_still_tracks_project(monkeypatch):
    api = Provider("https://fixture.example.org/api", "memory-only")
    project_id = uid()
    response = mock_json({"@id": project_id, "name": "omg-beta1-mock"}, 201)
    send = Mock(return_value=response)
    monkeypatch.setattr(api.session, "request", send)
    with pytest.raises(AssertionError, match="postProject response"):
        api.call("postProject", body={"name": "omg-beta1-mock"})
    assert api.projects == [project_id]
    assert api.evidence == ["postProject HTTP 201"]
    assert not send.call_args.kwargs["allow_redirects"]


def test_pagination_validates_links_and_visits_previous_page(monkeypatch):
    api = Provider("https://fixture.example.org/api", None)
    first, second = (
        {"@id": uid(), "@type": "Project", "name": name, "description": None,
         "created": "2023-02-01T00:00:00Z", "defaultBranch": ref(uid())}
        for name in ("first", "second")
    )
    one, two = mock_json([first]), mock_json([second])
    one.headers["Link"] = '<?page%5Bafter%5D=token>; rel="next"'
    two.headers["Link"] = '<?page%5Bbefore%5D=token>; rel="prev"'
    send = Mock(side_effect=[one, two, one])
    monkeypatch.setattr(api.session, "request", send)
    assert api.collection("getProjects", size=1) == [first, second]
    assert send.call_count == 3
    with pytest.raises(AssertionError, match="switched endpoint"):
        api.request("getProjects", follow="https://other.example.org/api/projects")
