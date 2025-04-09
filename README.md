# SysML v2 Python Client

A basic Python client library for interacting with a SysML v2 API server, specifically tested against the OpenMBEE Flexo implementation.

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

This client is designed to work with a running instance of the OpenMBEE Flexo SysMLv2 service.

*   **Prerequisites:** Docker and Docker Compose installed.
*   **Get Setup Files:** The necessary `docker-compose.yml` and configuration files are located in the `flexo-setup/docker-compose/` directory within this project (downloaded from `Open-MBEE/flexo-mms-sysmlv2`).
*   **Start Services:** Navigate to the `flexo-setup/docker-compose/` directory in your terminal and run:
    ```bash
    docker compose up -d
    ```
*   **Initial Org Setup (Potential Manual Step):** For a fresh database, you may need to perform an initial organization setup using Postman as described in `flexo-setup/docker-compose/README.md`.
*   **Authentication Token:** The required Bearer token for the client is found in `flexo-setup/docker-compose/env/flexo-sysmlv2.env` under the `FLEXO_AUTH` variable. Copy this entire value (including `Bearer `).

### 2. Install Client (Development)


```python
# Example: Add src to path if running scripts/notebooks from project root
import sys
import os
sys.path.insert(0, os.path.abspath('./src'))

from sysmlv2_client import SysMLV2Client
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
                    "@type": "BlockDefinition", # Example type
                    "name": "MyExampleBlock"
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

See the [examples/basic_usage.ipynb](examples/basic_usage.ipynb) Jupyter Notebook for more detailed examples covering commits, branches, tags, and element retrieval/modification via commits.

## Running Tests

Unit tests are implemented using `pytest` and `requests-mock`.

1.  **Install Dependencies:**
    ```bash
    pip install pytest requests requests-mock
    ```
2.  **Run Tests:** Navigate to the project root directory in your terminal and run:
    ```bash
    pytest
    ```
