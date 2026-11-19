from functools import lru_cache
import json
from pathlib import Path
from urllib.parse import quote, urljoin, urlsplit
from uuid import UUID, uuid4

import requests

ROOT = Path(__file__).resolve().parent
API = json.loads((ROOT / "references/OpenAPI.json").read_bytes())
OPERATIONS = {
    spec["operationId"]: (method, path, spec)
    for path, methods in API["paths"].items()
    for method, spec in methods.items()
}
API_NS = "https://www.omg.org/spec/SystemsModelingAPI/20230201/"
SYSML_NS = "https://www.omg.org/spec/SysML/20230201/"


def ref(value):
    return {"@id": value["@id"] if isinstance(value, dict) else value}


def ids(records):
    values = [record["@id"] for record in records]
    assert len(values) == len(set(values)), "Duplicate record IDs"
    return set(values)


def uid():
    return str(uuid4())


def resolve(value):
    if "$ref" in value and value["$ref"].startswith("#/"):
        target = API
        for key in value["$ref"][2:].split("/"):
            target = target[key]
        return target
    return value


@lru_cache
def schema_registry():
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012

    definitions = json.loads((ROOT / "references/Schemas.json").read_bytes())["$defs"]
    resources = {
        definition["$id"]: definition
        for key, definition in definitions.items()
        if key != "PrimitiveConstraintRequest"
    }
    resources[API_NS + "PrimitiveConstraintRequest"] = {
        **definitions["PrimitiveConstraintRequest"],
        "$id": API_NS + "PrimitiveConstraintRequest",
    }
    # The Beta 1 bundle publishes only request variants for SysML elements.
    # Also enforce identity on responses, which the request schemas omit.
    for kind in ("Element", "Relationship"):
        resources[SYSML_NS + kind] = {
            "$id": SYSML_NS + kind,
            "allOf": [
                {"$ref": API_NS + kind + "Request"},
                {"required": ["@id", "@type"]},
            ],
        }
    return Registry().with_resources(
        (uri, Resource.from_contents(schema, default_specification=DRAFT202012))
        for uri, schema in resources.items()
    ).crawl()


def validate(schema, payload, label):
    from jsonschema import Draft202012Validator

    def bind(value):
        if isinstance(value, list):
            return [bind(item) for item in value]
        if not isinstance(value, dict):
            return value
        result = {key: bind(item) for key, item in value.items()}
        pointer = value.get("$ref", "")
        if pointer.startswith("#/components/schemas/"):
            name = pointer.rsplit("/", 1)[-1]
            namespace = SYSML_NS if name in ("Element", "Relationship") else API_NS
            result["$ref"] = namespace + name
        return result

    validator = Draft202012Validator(
        bind(schema), registry=schema_registry(),
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )
    error = next(validator.iter_errors(payload), None)
    if error is not None:
        raise AssertionError(
            f"{label}: JSON validation failed at {error.json_path} ({error.validator})"
        )


class Provider:
    def __init__(self, base_url, token):
        self.url = base_url.rstrip("/")
        parts = urlsplit(self.url)
        if parts.scheme not in ("http", "https") or not parts.hostname or (
            parts.username or parts.password or parts.query or parts.fragment
        ):
            raise ValueError("Use an HTTP(S) base URL without embedded credentials, query or fragment")
        self.session = requests.Session()
        self.session.headers["Accept"] = "application/json"
        credential = (token or "").split()
        if credential and credential[0].lower() == "bearer":
            credential = credential[1:]
            if not credential:
                raise ValueError("Bearer authentication requires a token")
        if len(credential) > 1:
            raise ValueError("Set one raw JWT or one Bearer token")
        if credential:
            self.session.headers["Authorization"] = "Bearer " + credential[0]
        self.projects = []
        self.evidence = []

    def request(self, operation, *, query=None, body=None, status=None, follow=None, **path_ids):
        method, template, spec = OPERATIONS[operation]
        path = template.format(**{key: quote(value, safe="") for key, value in path_ids.items()})
        url = self.url + path
        if follow is not None:
            link = urlsplit(urljoin(url, follow))
            origin = urlsplit(url)
            assert (link.scheme, link.netloc, link.path) == (
                origin.scheme, origin.netloc, origin.path
            ), f"{operation}: pagination URL switched endpoint"
            url = link.geturl()

        if status is None and body is not None:
            schema = spec["requestBody"]["content"]["application/json"]["schema"]
            validate(schema, body, f"{operation} request")
        try:
            response = self.session.request(
                method, url, params=query, json=body, timeout=(5, 30), allow_redirects=False,
            )
        except requests.RequestException as error:
            self.evidence.append(f"{operation} {type(error).__name__}")
            raise AssertionError(f"{operation}: {type(error).__name__}") from None
        self.evidence.append(f"{operation} HTTP {response.status_code}")
        if operation == "postProject" and response.ok:
            self.track_project(response, body)
        allowed = status if status is not None else tuple(
            int(code) for code in spec["responses"] if code.startswith("2")
        )
        assert response.status_code in allowed, (
            f"{operation}: HTTP {response.status_code}, expected {allowed}"
        )
        if response.status_code == 204:
            assert not response.content, f"{operation}: expected empty 204 body"
            return None, response.links
        contract = resolve(spec["responses"].get(str(response.status_code), spec["responses"]["default"]))
        content = contract["content"]
        media = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
        assert media in content, f"{operation}: unexpected response media type"
        try:
            payload = response.json()
        except ValueError:
            raise AssertionError(f"{operation}: response is not valid JSON") from None

        validate(content[media]["schema"], payload, f"{operation} response")
        if response.status_code >= 400 and isinstance(payload, dict):
            assert (payload.get("description") or "").strip(), f"{operation}: missing error explanation"
        return payload, response.links

    def track_project(self, response, body):
        # Track before validation in case a successful response violates the contract.
        try:
            payload = response.json()
        except ValueError:
            return
        if isinstance(payload, dict):
            project_id = payload.get("@id")
            if isinstance(project_id, str) and project_id not in ("", ".", ".."):
                if body and payload.get("name") == body.get("name"):
                    self.projects.append(project_id)
                elif response.status_code == 201 and body == {}:
                    # The missing-name probe can create a project on a permissive server.
                    try:
                        UUID(project_id)
                    except ValueError:
                        return
                    self.projects.append(project_id)

    def call(self, operation, **kwargs):
        return self.request(operation, **kwargs)[0]

    def collection(self, operation, *, query=None, size=None, **params):
        query = dict(query or {})
        if size is not None:
            query["page[size]"] = size
        page, links = self.request(operation, query=query, **params)
        assert isinstance(page, list)
        result = list(page)
        seen = set()
        if size is not None:
            assert len(page) <= size
        while "next" in links:
            url = links["next"]["url"]
            assert url not in seen and len(seen) < 200, f"{operation}: pagination did not terminate"
            seen.add(url)
            previous = ids(page)
            page, links = self.request(operation, follow=url, **params)
            if size is not None:
                assert 0 < len(page) <= size
                back = links.get("prev", {}).get("url")
                assert back, f"{operation}: missing previous page link"
                prior, _ = self.request(operation, follow=back, **params)
                assert ids(prior) == previous
            result.extend(page)
        ids(result)
        return result

    def project(self):
        body = {"name": f"omg-beta1-{uid()}", "description": "Disposable Beta 1 test fixture"}
        project = self.call("postProject", body=body)
        assert project["name"] == body["name"]
        assert project["description"] == body["description"]
        return project

    def commit(self, project, changes, branch=None):
        query = {"branchId": branch["@id"]} if branch else None
        return self.call("postCommitByProject", projectId=project["@id"], query=query,
                         body={"change": changes})

    def branch(self, project, commit):
        return self.call("postBranchByProject", projectId=project["@id"],
                         body={"name": f"branch-{uid()}", "head": ref(commit)})
