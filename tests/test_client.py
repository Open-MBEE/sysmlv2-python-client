import pytest
import requests_mock
import requests

from src.sysmlv2_client import (
    SysMLV2Client,
    SysMLV2Error,
    SysMLV2AuthError,
    SysMLV2APIError,
    SysMLV2NotFoundError,
    SysMLV2BadRequestError,
    SysMLV2ConflictError,
)

# --- Constants for testing ---
TEST_BASE_URL = "http://test-sysml-api.com"
TEST_BEARER_TOKEN = "Bearer FAKE_TOKEN_12345"
TEST_PROJECT_ID = "test_proj_1"
TEST_COMMIT_ID = "main"
TEST_ELEMENT_ID = "elem_abc"


# --- Fixtures ---

@pytest.fixture
def client():
    """Provides a SysMLV2Client instance for testing."""
    return SysMLV2Client(base_url=TEST_BASE_URL, bearer_token=TEST_BEARER_TOKEN)

@pytest.fixture
def mock_session(client):
    """Mocks the requests session used by the client."""
    adapter = requests_mock.Adapter()
    client._session.mount('mock://', adapter)
    return adapter


# --- Test Cases ---

def test_client_initialization(client):
    """Tests successful client initialization."""
    assert client.base_url == TEST_BASE_URL
    assert client._bearer_token == TEST_BEARER_TOKEN
    assert client._headers["Authorization"] == TEST_BEARER_TOKEN
    assert "Content-Type" in client._headers
    assert "Accept" in client._headers

def test_client_initialization_invalid_token():
    """Tests client initialization failure with invalid token format."""
    with pytest.raises(ValueError, match="bearer_token must be provided and start with 'Bearer '"):
        SysMLV2Client(base_url=TEST_BASE_URL, bearer_token="INVALID_TOKEN")
    with pytest.raises(ValueError, match="bearer_token must be provided and start with 'Bearer '"):
        SysMLV2Client(base_url=TEST_BASE_URL, bearer_token="") 

def test_client_initialization_invalid_url():
    """Tests client initialization failure with invalid base URL."""
    with pytest.raises(ValueError, match="base_url cannot be empty"):
        SysMLV2Client(base_url="", bearer_token=TEST_BEARER_TOKEN)


# --- Test Get Projects ---

def test_get_projects_success(client, requests_mock):
    """Tests successfully retrieving projects."""
    mock_url = f"{TEST_BASE_URL}/projects"
    mock_response_data = {"elements": [{"id": "proj1", "name": "Project 1"}, {"id": "proj2"}]}
    requests_mock.get(mock_url, json=mock_response_data, status_code=200)

    projects = client.get_projects()

    assert projects == mock_response_data["elements"]
    assert requests_mock.last_request.url == mock_url
    assert requests_mock.last_request.method == "GET"
    assert requests_mock.last_request.headers["Authorization"] == TEST_BEARER_TOKEN

def test_get_projects_success_empty(client, requests_mock):
    """Tests successfully retrieving an empty list of projects."""
    mock_url = f"{TEST_BASE_URL}/projects"
    mock_response_data = {"elements": []} 
    requests_mock.get(mock_url, json=mock_response_data, status_code=200)

    projects = client.get_projects()

    assert projects == []

def test_get_projects_success_no_elements_key(client, requests_mock):
    """Tests retrieving projects when the response structure is unexpected."""
    mock_url = f"{TEST_BASE_URL}/projects"
    mock_response_data = [{"id": "proj1", "name": "Project 1"}] 
    requests_mock.get(mock_url, json=mock_response_data, status_code=200)

    projects = client.get_projects()

    assert projects == mock_response_data 

def test_get_projects_auth_error(client, requests_mock):
    """Tests authentication error during get_projects."""
    mock_url = f"{TEST_BASE_URL}/projects"
    requests_mock.get(mock_url, status_code=401, text="Unauthorized")

    with pytest.raises(SysMLV2AuthError, match="Authentication failed: 401"):
        client.get_projects()

def test_get_projects_api_error(client, requests_mock):
    """Tests a generic API error during get_projects."""
    mock_url = f"{TEST_BASE_URL}/projects"
    requests_mock.get(mock_url, status_code=500, text="Internal Server Error")

    with pytest.raises(SysMLV2APIError, match="Unexpected status code for GET /projects"):
        client.get_projects()

# --- Test Create Project ---

def test_create_project_success(client, requests_mock):
    """Tests successfully creating a project."""
    mock_url = f"{TEST_BASE_URL}/projects"
    request_data = {"name": "New Project", "description": "A test project"}
    response_data = {"id": "new_proj_id", **request_data}
    requests_mock.post(mock_url, json=response_data, status_code=200) 

    created_project = client.create_project(request_data)

    assert created_project == response_data
    assert requests_mock.last_request.url == mock_url
    assert requests_mock.last_request.method == "POST"
    assert requests_mock.last_request.json() == request_data
    assert requests_mock.last_request.headers["Authorization"] == TEST_BEARER_TOKEN
    assert requests_mock.last_request.headers["Content-Type"] == "application/json"

def test_create_project_bad_request(client, requests_mock):
    """Tests a 400 Bad Request error during project creation."""
    mock_url = f"{TEST_BASE_URL}/projects"
    request_data = {"name": "Missing required field"} 
    error_response = {"error": "Missing description"}
    requests_mock.post(mock_url, json=error_response, status_code=400)

    with pytest.raises(SysMLV2BadRequestError, match="Bad request for /projects"):
        client.create_project(request_data)

def test_create_project_conflict(client, requests_mock):
    """Tests a 409 Conflict error during project creation."""
    mock_url = f"{TEST_BASE_URL}/projects"
    request_data = {"name": "Existing Project"}
    requests_mock.post(mock_url, status_code=409, text="Project already exists")

    with pytest.raises(SysMLV2ConflictError, match="Conflict detected for /projects"):
        client.create_project(request_data)

def test_create_project_auth_error(client, requests_mock):
    """Tests authentication error during create_project."""
    mock_url = f"{TEST_BASE_URL}/projects"
    request_data = {"name": "New Project"}
    requests_mock.post(mock_url, status_code=403, text="Forbidden")

    with pytest.raises(SysMLV2AuthError, match="Authentication failed: 403"):
        client.create_project(request_data)

def test_create_project_api_error(client, requests_mock):
    """Tests a generic API error during create_project."""
    mock_url = f"{TEST_BASE_URL}/projects"
    request_data = {"name": "New Project"}
    requests_mock.post(mock_url, status_code=503, text="Service Unavailable")


    with pytest.raises(SysMLV2APIError, match="Unexpected status code for POST /projects"):
        client.create_project(request_data)


# --- Test Get Element ---

def test_get_element_success(client, requests_mock):
    """Tests successfully retrieving an element."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/{TEST_COMMIT_ID}/elements/{TEST_ELEMENT_ID}"
    mock_response_data = {"id": TEST_ELEMENT_ID, "name": "Test Element", "type": "Block"}
    requests_mock.get(mock_url, json=mock_response_data, status_code=200)

    element = client.get_element(TEST_PROJECT_ID, TEST_ELEMENT_ID, TEST_COMMIT_ID)

    assert element == mock_response_data
    assert requests_mock.last_request.url == mock_url
    assert requests_mock.last_request.method == "GET"

def test_get_element_not_found(client, requests_mock):
    """Tests a 404 Not Found error during get_element."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/{TEST_COMMIT_ID}/elements/not_found_id"
    requests_mock.get(mock_url, status_code=404, text="Element not found")

    with pytest.raises(SysMLV2NotFoundError, match="Resource not found"):
        client.get_element(TEST_PROJECT_ID, "not_found_id", TEST_COMMIT_ID)

def test_get_element_auth_error(client, requests_mock):
    """Tests authentication error during get_element."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/{TEST_COMMIT_ID}/elements/{TEST_ELEMENT_ID}"
    requests_mock.get(mock_url, status_code=401)

    with pytest.raises(SysMLV2AuthError):
        client.get_element(TEST_PROJECT_ID, TEST_ELEMENT_ID, TEST_COMMIT_ID)


# --- Test Get Owned Elements ---

def test_get_owned_elements_success(client, requests_mock):
    """Tests successfully retrieving owned elements."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/{TEST_COMMIT_ID}/elements/{TEST_ELEMENT_ID}/owned"
    mock_response_data = {"elements": [{"id": "owned_elem_1"}, {"id": "owned_elem_2"}]}
    requests_mock.get(mock_url, json=mock_response_data, status_code=200)

    owned_elements = client.get_owned_elements(TEST_PROJECT_ID, TEST_ELEMENT_ID, TEST_COMMIT_ID)

    assert owned_elements == mock_response_data["elements"]
    assert requests_mock.last_request.url == mock_url
    assert requests_mock.last_request.method == "GET"

def test_get_owned_elements_not_found(client, requests_mock):
    """Tests 404 when parent element not found for owned elements."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/{TEST_COMMIT_ID}/elements/not_found_parent/owned"
    requests_mock.get(mock_url, status_code=404)

    with pytest.raises(SysMLV2NotFoundError):
        client.get_owned_elements(TEST_PROJECT_ID, "not_found_parent", TEST_COMMIT_ID)

def test_get_owned_elements_empty(client, requests_mock):
    """Tests retrieving empty owned elements list."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/{TEST_COMMIT_ID}/elements/{TEST_ELEMENT_ID}/owned"
    mock_response_data = {"elements": []}
    requests_mock.get(mock_url, json=mock_response_data, status_code=200)

    owned_elements = client.get_owned_elements(TEST_PROJECT_ID, TEST_ELEMENT_ID, TEST_COMMIT_ID)

    assert owned_elements == []

# --- Test Create Commit ---

def test_create_commit_success(client, requests_mock):
    """Tests successfully creating a commit."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits"
    request_data = {"message": "Initial commit", "parentCommitId": None}
    response_data = {"id": "new_commit_id", **request_data}
    requests_mock.post(mock_url, json=response_data, status_code=200) 

    created_commit = client.create_commit(TEST_PROJECT_ID, request_data)

    assert created_commit == response_data
    assert requests_mock.last_request.url == mock_url
    assert requests_mock.last_request.method == "POST"
    assert requests_mock.last_request.json() == request_data

def test_create_commit_bad_request(client, requests_mock):
    """Tests 400 Bad Request during commit creation."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits"
    request_data = {} 
    requests_mock.post(mock_url, status_code=400, json={"error": "Missing commit message"})

    with pytest.raises(SysMLV2BadRequestError):
        client.create_commit(TEST_PROJECT_ID, request_data)

def test_create_commit_project_not_found(client, requests_mock):
    """Tests 404 when project not found during commit creation."""
    mock_url = f"{TEST_BASE_URL}/projects/invalid_project/commits"
    request_data = {"message": "Commit message"}
    requests_mock.post(mock_url, status_code=404)

    with pytest.raises(SysMLV2NotFoundError):
        client.create_commit("invalid_project", request_data)


# --- Test Get Project By ID ---

def test_get_project_by_id_success(client, requests_mock):
    """Tests successfully retrieving a specific project."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}"
    mock_response_data = {"id": TEST_PROJECT_ID, "name": "Test Project 1"}
    requests_mock.get(mock_url, json=mock_response_data, status_code=200)

    project = client.get_project_by_id(TEST_PROJECT_ID)

    assert project == mock_response_data
    assert requests_mock.last_request.url == mock_url

def test_get_project_by_id_not_found(client, requests_mock):
    """Tests 404 when getting a non-existent project."""
    mock_url = f"{TEST_BASE_URL}/projects/not_a_project"
    requests_mock.get(mock_url, status_code=404)

    with pytest.raises(SysMLV2NotFoundError):
        client.get_project_by_id("not_a_project")

# --- Test Get Commit By ID ---

def test_get_commit_by_id_success(client, requests_mock):
    """Tests successfully retrieving a specific commit."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/{TEST_COMMIT_ID}"
    mock_response_data = {"id": TEST_COMMIT_ID, "message": "Initial commit"}
    requests_mock.get(mock_url, json=mock_response_data, status_code=200)

    commit = client.get_commit_by_id(TEST_PROJECT_ID, TEST_COMMIT_ID)

    assert commit == mock_response_data
    assert requests_mock.last_request.url == mock_url

def test_get_commit_by_id_not_found(client, requests_mock):
    """Tests 404 when getting a non-existent commit."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/not_a_commit"
    requests_mock.get(mock_url, status_code=404)

    with pytest.raises(SysMLV2NotFoundError):
        client.get_commit_by_id(TEST_PROJECT_ID, "not_a_commit")

# --- Test List Commits ---

def test_list_commits_success(client, requests_mock):
    """Tests successfully listing commits."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits"
    mock_response_data = [{"id": "commit1"}, {"id": "commit2"}] 
    requests_mock.get(mock_url, json=mock_response_data, status_code=200)

    commits = client.list_commits(TEST_PROJECT_ID)

    assert commits == mock_response_data
    assert requests_mock.last_request.url == mock_url

def test_list_commits_success_dict_response(client, requests_mock):
    """Tests listing commits when API returns a dict with 'elements'."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits"
    mock_response_data = {"elements": [{"id": "commit1"}, {"id": "commit2"}]}
    requests_mock.get(mock_url, json=mock_response_data, status_code=200)

    commits = client.list_commits(TEST_PROJECT_ID)

    assert commits == mock_response_data["elements"]

def test_list_commits_project_not_found(client, requests_mock):
    """Tests 404 when listing commits for a non-existent project."""
    mock_url = f"{TEST_BASE_URL}/projects/invalid_project/commits"
    requests_mock.get(mock_url, status_code=404)

    with pytest.raises(SysMLV2NotFoundError):
        client.list_commits("invalid_project")


# --- Test Branch Management ---

TEST_BRANCH_ID = "branch_xyz"

def test_list_branches_success(client, requests_mock):
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/branches"
    mock_response = [{"id": TEST_BRANCH_ID, "name": "develop"}]
    requests_mock.get(mock_url, json=mock_response, status_code=200)
    branches = client.list_branches(TEST_PROJECT_ID)
    assert branches == mock_response

def test_create_branch_success(client, requests_mock):
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/branches"
    request_data = {"name": "feature-branch", "head": {"@id": TEST_COMMIT_ID}}
    response_data = {"id": "new_branch_id", **request_data}
    requests_mock.post(mock_url, json=response_data, status_code=200) 
    branch = client.create_branch(TEST_PROJECT_ID, request_data)
    assert branch == response_data
    assert requests_mock.last_request.json() == request_data

def test_get_branch_by_id_success(client, requests_mock):
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/branches/{TEST_BRANCH_ID}"
    response_data = {"id": TEST_BRANCH_ID, "name": "develop"}
    requests_mock.get(mock_url, json=response_data, status_code=200)
    branch = client.get_branch_by_id(TEST_PROJECT_ID, TEST_BRANCH_ID)
    assert branch == response_data

def test_delete_branch_success(client, requests_mock):
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/branches/{TEST_BRANCH_ID}"
    requests_mock.delete(mock_url, status_code=204)
    result = client.delete_branch(TEST_PROJECT_ID, TEST_BRANCH_ID)
    assert result is None

def test_delete_branch_not_found(client, requests_mock):
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/branches/not_a_branch"
    requests_mock.delete(mock_url, status_code=404)
    with pytest.raises(SysMLV2NotFoundError):
        client.delete_branch(TEST_PROJECT_ID, "not_a_branch")


# --- Test Tag Management ---

TEST_TAG_ID = "tag_v1"

def test_list_tags_success(client, requests_mock):
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/tags"
    mock_response = [{"id": TEST_TAG_ID, "name": "v1.0"}]
    requests_mock.get(mock_url, json=mock_response, status_code=200)
    tags = client.list_tags(TEST_PROJECT_ID)
    assert tags == mock_response

def test_create_tag_success(client, requests_mock):
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/tags"
    request_data = {"name": "v1.0-release", "taggedCommit": {"@id": TEST_COMMIT_ID}}
    response_data = {"id": "new_tag_id", **request_data}
    requests_mock.post(mock_url, json=response_data, status_code=200) 
    tag = client.create_tag(TEST_PROJECT_ID, request_data)
    assert tag == response_data
    assert requests_mock.last_request.json() == request_data

def test_get_tag_by_id_success(client, requests_mock):
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/tags/{TEST_TAG_ID}"
    response_data = {"id": TEST_TAG_ID, "name": "v1.0"}
    requests_mock.get(mock_url, json=response_data, status_code=200)
    tag = client.get_tag_by_id(TEST_PROJECT_ID, TEST_TAG_ID)
    assert tag == response_data

def test_delete_tag_success(client, requests_mock):
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/tags/{TEST_TAG_ID}"
    requests_mock.delete(mock_url, status_code=204)
    result = client.delete_tag(TEST_PROJECT_ID, TEST_TAG_ID)
    assert result is None

def test_delete_tag_not_found(client, requests_mock):
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/tags/not_a_tag"
    requests_mock.delete(mock_url, status_code=404)
    with pytest.raises(SysMLV2NotFoundError):
        client.delete_tag(TEST_PROJECT_ID, "not_a_tag")


# --- Test List Elements ---

def test_list_elements_success(client, requests_mock):
    """Tests successfully listing elements in a commit."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/{TEST_COMMIT_ID}/elements"
    mock_response_data = [{"id": "elem1"}, {"id": "elem2"}]
    requests_mock.get(mock_url, json=mock_response_data, status_code=200)
    elements = client.list_elements(TEST_PROJECT_ID, TEST_COMMIT_ID)
    assert elements == mock_response_data

def test_list_elements_commit_not_found(client, requests_mock):
    """Tests 404 when listing elements for non-existent commit."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/invalid_commit/elements"
    requests_mock.get(mock_url, status_code=404)
    with pytest.raises(SysMLV2NotFoundError):
        client.list_elements(TEST_PROJECT_ID, "invalid_commit")


# --- Test List Relationships ---

def test_list_relationships_success(client, requests_mock):
    """Tests successfully listing relationships for an element."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/{TEST_COMMIT_ID}/elements/{TEST_ELEMENT_ID}/relationships?direction=both"
    mock_response_data = [{"id": "rel1", "source": TEST_ELEMENT_ID}, {"id": "rel2", "target": TEST_ELEMENT_ID}]
    requests_mock.get(mock_url, json=mock_response_data, status_code=200)
    relationships = client.list_relationships(TEST_PROJECT_ID, TEST_ELEMENT_ID, TEST_COMMIT_ID)
    assert relationships == mock_response_data

def test_list_relationships_with_direction(client, requests_mock):
    """Tests listing relationships with specific direction."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/{TEST_COMMIT_ID}/elements/{TEST_ELEMENT_ID}/relationships?direction=out"
    mock_response_data = [{"id": "rel1", "source": TEST_ELEMENT_ID}]
    requests_mock.get(mock_url, json=mock_response_data, status_code=200)
    relationships = client.list_relationships(TEST_PROJECT_ID, TEST_ELEMENT_ID, TEST_COMMIT_ID, direction="out")
    assert relationships == mock_response_data
    assert requests_mock.last_request.qs == {'direction': ['out']}

def test_list_relationships_element_not_found(client, requests_mock):
    """Tests 404 when listing relationships for non-existent element."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/{TEST_COMMIT_ID}/elements/invalid_element/relationships?direction=both"
    requests_mock.get(mock_url, status_code=404)
    with pytest.raises(SysMLV2NotFoundError):
        client.list_relationships(TEST_PROJECT_ID, "invalid_element", TEST_COMMIT_ID)