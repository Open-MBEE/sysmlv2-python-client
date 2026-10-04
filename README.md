# sysml-api-client

A Python client for the [OMG Systems Modeling API and Services](https://www.omg.org/spec/SystemsModelingAPI), specifically tested against the OpenMBEE Flexo implementation. The PyPI name is `sysml-api-client`; Python imports remain `sysmlv2_client` and `sysml_api`.

## Installation

Requires Python 3.10 or newer. Once published on PyPI:

```bash
python -m pip install sysml-api-client
```

```python
from sysmlv2_client import SysMLV2Client
```

See [RELEASING.md](RELEASING.md) for build validation and publisher setup.

## Features

*   Provides methods for core SysML v2 operations:
    *   **Projects:** Get List, Create, Get by ID
    *   **Commits:** Create (handles element create/update/delete), Get by ID, List
    *   **Branches:** List, Create, Get by ID, Delete
    *   **Tags:** List, Create, Get by ID, Delete
    *   **Elements:** Get by ID, List All in Commit, Get Owned by Element
    *   **Relationships:** List for Element
*   Handles authentication using Bearer tokens.
*   Includes basic error handling and custom exceptions.

## Setup
### 1. Run Flexo SysMLv2 Service Locally
Follow instructions [here](https://github.com/Open-MBEE/flexo-mms-sysmlv2.git)

### 2. Install Client (Development)

```bash
python -m pip install -e ".[test]"
```

## Basic Usage
```python
from sysmlv2_client import SysMLV2Client, SysMLV2Error
from pprint import pprint
import uuid # For element IDs

BASE_URL = "http://localhost:8083"
# Replace with the actual token from flexo-setup/docker-compose/env/flexo-sysmlv2.env
BEARER_TOKEN = "Bearer YOUR_TOKEN_HERE"

try:
    client = SysMLV2Client(base_url=BASE_URL, bearer_token=BEARER_TOKEN)
    print("Client initialized.")

    # Get projects
    print("\\n--- Getting Projects ---")
    projects = client.get_projects()
    print(f"Found {len(projects)} projects.")
    for project in projects:
        print(f"  - Name: {project.get('name', 'N/A')}, ID: {project.get('@id', 'N/A')}")

    # Create a project (example data)
    print("\\n--- Creating Project ---")
    new_proj_data = {"@type": "Project", "name": "Client README Example"}
    created_proj = client.create_project(new_proj_data)
    print(f"Created project:")
    pprint(created_proj)
    project_id = created_proj.get('@id')

    if project_id:
        # Create a commit that also creates an element
        print(f"\\n--- Creating Commit with Element in Project {project_id} ---")
        element_id = str(uuid.uuid4())
        commit_data = {
            "@type": "Commit",
            "description": "Add initial block",
            "change": [{
                "@type": "DataVersion",
                "payload": {
                    "@id": element_id,
                    "@type": "PartDefinition", # Example type
                    "name": "MyExamplePartDefinition"
                }
            }]
        }
        created_commit = client.create_commit(project_id, commit_data)
        print("Commit created:")
        pprint(created_commit)
        commit_id = created_commit.get('@id')

        if commit_id:
            # List elements in the new commit
            print(f"\\n--- Listing Elements in Commit {commit_id} ---")
            elements = client.list_elements(project_id, commit_id)
            print(f"Found {len(elements)} elements:")
            pprint(elements)

except SysMLV2Error as e:
    print(f"An API error occurred: {e}")
except ValueError as e:
    print(f"Initialization error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

```


## Running Tests

Unit tests are implemented using `pytest` and `requests-mock`.

1.  **Install Dependencies:**
    ```bash
    python -m pip install -e ".[test]"
    ```
2.  **Run Tests:** Navigate to the project root directory in your terminal and run:
    ```bash
    pytest
    ```

## API
### Basic v2 API
* get_projects
* create_project
* delete_project
* get_project_by_id
* get_element
* get_owned_elements
* create_commit
* get_commit_by_id
* list_commits
* list_branches
* create_branch
* get_branch_by_id
* list_tags
* create_tag
* get_tag_by_id
* list_elements
* list_relationships

### Convenience functions
* create_sysml_project
* get_project_by_name
* commit_to_project
* get_last_commit_from_project
* create_branch
 
