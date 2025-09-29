import numpy as np
from sysmlv2_client import SysMLV2Client, SysMLV2Error, SysMLV2NotFoundError
from typing import Any, Dict

minimal_payload = [
    {
        "payload": {
            "@type": "Empty",
            "@id": "8dd9e99d-ec41-44d8-bb18-a1d849d3aff5",
            "elementId": "8dd9e99d-ec41-44d8-bb18-a1d849d3aff5",
            "qualifiedName": "",
            "isImpliedIncluded": True,
            "isLibraryElement": False,
            "ownedElement": [],
            "ownedRelationship": []
        }
    }
]
def create_sysml_project(client: SysMLV2Client, name:str, description:str="project description"):
    created_project = None
    example_project_id = None
    commit_id = None
    new_project_data = {
        "@type": "Project",
        "name": name,
        "description": description
    }
    try:
        created_project = client.create_project(new_project_data)
        # Store the ID for later use
        example_project_id = created_project.get('@id')
        # if not example_project_id:
        #      print("\n*** WARNING: Could not extract project ID ('@id') from response! Subsequent steps might fail. ***")
        # else:
        #     #create empty commit so we can branch off an empty commit initially
        #     commit_response, commit_id = commit_to_project(client, example_project_id, minimal_payload)
    except SysMLV2Error as e:
        print(f"Error creating project: {e}")
    return created_project, example_project_id, commit_id


def get_project_by_name(client: SysMLV2Client, name: str):
    try:
        projects = client.get_projects()
        if projects:
            for project in projects:
                proj_id = project.get('@id', 'N/A')
                proj_name = project.get('name', 'N/A')
                if proj_name == name:
                    return project, proj_id
            # If no project matched
            return None, None
        else:
            print("  (No projects found)")
            return None, None
    except SysMLV2Error as e:
        print(f"Error getting projects: {e}")
        return None, None

def commit_to_project(client: SysMLV2Client, proj_id:str, payload:str, commit_msg:str = "default commit message"):
    commit1_data = {
        "@type": "Commit",
        "description": commit_msg,
        "change": payload
    }

    try:
        commit1_response = client.create_commit(proj_id, commit1_data)
        commit1_id = commit1_response.get('@id')
        if not commit1_id:
            print("\n*** WARNING: Could not extract commit ID ('@id') from response! ***")
            return None, None
        else:
            return commit1_response, commit1_id
    except SysMLV2Error as e:
        print(f"Error creating commit 1: {e}")
        return None, None


def _get_default_branch_id(project: Dict[str, Any]) -> str | None:
    default_branch = project.get('defaultBranch')
    if isinstance(default_branch, dict):
        return default_branch.get('@id')
    return None

def _get_referenced_commit_id(branch: Dict[str, Any]) -> str | None:
    referenced_commit = branch.get('referencedCommit')
    if isinstance(referenced_commit, dict):
        return referenced_commit.get('@id')
    return None


def get_last_commit_from_project(client: SysMLV2Client, proj_obj: Dict[str, Any]):
    default_branch_id = _get_default_branch_id(proj_obj)
    proj_id = proj_obj.get('@id')
    response_data = client._request(method="GET", endpoint=f"/projects/{proj_id}/branches/{default_branch_id}", expected_status=200)
    commit_id = _get_referenced_commit_id(response_data)
    return commit_id

def create_branch(client: SysMLV2Client, proj_id:str, commit_id:str, branch_name:str):
    #create branch from that commit
    branch_data = {
#        "@type": "Branch",
        "name": branch_name,
        "head": {"@id": commit_id}
    }
    print (branch_data)
    try:
        created_branch = client.create_branch(proj_id, branch_data)
        example_branch_id = created_branch.get('@id')
        if not example_branch_id:
            print("\n*** WARNING: Could not extract branch ID ('@id') from response! ***")
            return None, None
        else:
            return created_branch, example_branch_id
    except SysMLV2Error as e:
        print(f"Error creating branch: {e}")
        return None, None

