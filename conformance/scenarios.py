"""Deterministic model and query inputs for the Beta 1 REST binding."""

from .provider import ids, ref, uid


def change(payload, identity=None):
    version = {"@type": "DataVersion", "payload": payload}
    if identity is not None:
        version["identity"] = ref(identity)
    return version


def package(name, **properties):
    return {"@type": "Package", "@id": uid(), "declaredName": name, **properties}


def model(api, project):
    parent = package("Parent")
    child = package("Child", owner=ref(parent))
    membership = {
        "@type": "OwningMembership", "@id": uid(), "owner": ref(parent),
        "owningNamespace": ref(parent), "ownedMemberElement": ref(child),
        "memberElement": ref(child), "source": [ref(parent)], "target": [ref(child)],
        "ownedRelatedElement": [ref(child)], "relatedElement": [ref(parent), ref(child)],
    }
    child.update(owningMembership=ref(membership), owningRelationship=ref(membership))
    parent.update(ownedElement=[ref(child)], ownedRelationship=[ref(membership)])
    dependency = {
        "@type": "Dependency", "@id": uid(), "client": [ref(child)], "supplier": [ref(parent)],
        "source": [ref(child)], "target": [ref(parent)], "relatedElement": [ref(child), ref(parent)],
    }
    commit = api.commit(project, [change(item) for item in (parent, child, membership, dependency)])
    return commit, parent, child, membership, dependency


def primitive(prop, value):
    return {"@type": "PrimitiveConstraint", "property": prop, "value": value,
            "operator": "=", "inverse": False}


def query_for(kind, **constraints):
    predicates = [primitive("@type", kind), *(
        primitive(prop, value) for prop, value in constraints.items()
    )]
    where = predicates[0] if len(predicates) == 1 else {
        "@type": "CompositeConstraint", "operator": "and", "constraint": predicates,
    }
    return {"@type": "Query", "where": where}


def query_results(api, project, commit, body):
    project_key = {"projectId": project["@id"]}
    saved = api.call("postQueryByProject", **project_key, body=body)
    assert saved["owningProject"] == ref(project)
    return api.collection("getQueryResultsByProjectIdQueryId", **project_key,
                          queryId=saved["@id"], query={"commitId": commit["@id"]})


def expect_ids(records, *expected):
    assert ids(records) == {item["@id"] for item in expected}
