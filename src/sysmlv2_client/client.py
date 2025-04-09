import requests
import json
from typing import Optional, Dict, Any, List

from .exceptions import (
    SysMLV2Error,
    SysMLV2AuthError,
    SysMLV2APIError,
    SysMLV2NotFoundError,
    SysMLV2BadRequestError,
    SysMLV2ConflictError,
)

class SysMLV2Client:
    def __init__(self, base_url: str, bearer_token: str):
        if not base_url:
            raise ValueError("base_url cannot be empty.")
        if not bearer_token or not bearer_token.lower().startswith("bearer "):
            raise ValueError("bearer_token must be provided and start with 'Bearer '.")

        self.base_url = base_url.rstrip('/')
        self._bearer_token = bearer_token
        self._headers = {
            "Authorization": self._bearer_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._session = requests.Session()
        self._session.headers.update(self._headers)

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        expected_status: int = 200,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        json_data = json.dumps(data) if data else None

        try:
            response = self._session.request(
                method=method,
                url=url,
                params=params,
                data=json_data,
            )

            # Check for specific error codes first
            if response.status_code == 401 or response.status_code == 403:
                raise SysMLV2AuthError(f"Authentication failed: {response.status_code} - {response.text}")
            if response.status_code == 404:
                raise SysMLV2NotFoundError(f"Resource not found at {endpoint}: {response.text}")
            if response.status_code == 400:
                try:
                    error_details = response.json()
                except json.JSONDecodeError:
                    error_details = response.text
                raise SysMLV2BadRequestError(f"Bad request for {endpoint}: {error_details}")
            if response.status_code == 409:
                raise SysMLV2ConflictError(f"Conflict detected for {endpoint}: {response.text}")

            # Check if the status code matches the expected one
            if response.status_code != expected_status:
                raise SysMLV2APIError(
                    status_code=response.status_code,
                    message=f"Unexpected status code for {method} {endpoint}. Response: {response.text}"
                )

            # Handle successful responses with no content (e.g., DELETE)
            if response.status_code == 204 or not response.content:
                return {}

            # Parse successful JSON response
            return response.json()

        except requests.exceptions.RequestException as e:
            raise SysMLV2Error(f"Network error during request to {url}: {e}") from e
        except json.JSONDecodeError as e:
             raise SysMLV2Error(f"Failed to decode JSON response from {url}: {e}. Response text: {response.text}") from e

    # --- Core API Methods ---

    def get_projects(self) -> List[Dict[str, Any]]:

        response_data = self._request(method="GET", endpoint="/projects", expected_status=200)
        if isinstance(response_data, list):
            return response_data 
        elif isinstance(response_data, dict):
            return response_data.get('elements', []) 
        else:
            return []

    def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._request(
            method="POST",
            endpoint="/projects",
            data=project_data,
            expected_status=200  
        )
    def get_project_by_id(self, project_id: str) -> Dict[str, Any]:
        endpoint = f"/projects/{project_id}"
        return self._request(method="GET", endpoint=endpoint, expected_status=200)
    
    def get_element(self, project_id: str, element_id: str, commit_id: str = "main") -> Dict[str, Any]:
        endpoint = f"/projects/{project_id}/commits/{commit_id}/elements/{element_id}"
        return self._request(method="GET", endpoint=endpoint, expected_status=200)

    def get_owned_elements(self, project_id: str, element_id: str, commit_id: str = "main") -> List[Dict[str, Any]]:

        endpoint = f"/projects/{project_id}/commits/{commit_id}/elements/{element_id}/owned"
        response_data = self._request(method="GET", endpoint=endpoint, expected_status=200)
        if isinstance(response_data, list):
            return response_data 
        elif isinstance(response_data, dict):
            return response_data.get('elements', [])
        else:
            return []

    def create_commit(self, project_id: str, commit_data: Dict[str, Any]) -> Dict[str, Any]:
        endpoint = f"/projects/{project_id}/commits"
        return self._request(
            method="POST",
            endpoint=endpoint,
            data=commit_data,
            expected_status=200 
        )
    def get_commit_by_id(self, project_id: str, commit_id: str) -> Dict[str, Any]:
        endpoint = f"/projects/{project_id}/commits/{commit_id}"
        return self._request(method="GET", endpoint=endpoint, expected_status=200)

    def list_commits(self, project_id: str) -> List[Dict[str, Any]]:
        endpoint = f"/projects/{project_id}/commits"
        response_data = self._request(method="GET", endpoint=endpoint, expected_status=200)
        if isinstance(response_data, list):
            return response_data
        elif isinstance(response_data, dict):
            return response_data.get('elements', [])
        else:
            return []

    # --- Branch Management ---

    def list_branches(self, project_id: str) -> List[Dict[str, Any]]:
        endpoint = f"/projects/{project_id}/branches"
        response_data = self._request(method="GET", endpoint=endpoint, expected_status=200)
        if isinstance(response_data, list):
            return response_data
        elif isinstance(response_data, dict):
            return response_data.get('elements', [])
        else:
            return []

    def create_branch(self, project_id: str, branch_data: Dict[str, Any]) -> Dict[str, Any]:
        endpoint = f"/projects/{project_id}/branches"
        return self._request(
            method="POST",
            endpoint=endpoint,
            data=branch_data,
            expected_status=200 
        )

    def get_branch_by_id(self, project_id: str, branch_id: str) -> Dict[str, Any]:
        endpoint = f"/projects/{project_id}/branches/{branch_id}"
        return self._request(method="GET", endpoint=endpoint, expected_status=200)

    def delete_branch(self, project_id: str, branch_id: str) -> None:
        endpoint = f"/projects/{project_id}/branches/{branch_id}"
        self._request(method="DELETE", endpoint=endpoint, expected_status=204)
        return None

    # --- Tag Management ---

    def list_tags(self, project_id: str) -> List[Dict[str, Any]]:
        endpoint = f"/projects/{project_id}/tags"
        response_data = self._request(method="GET", endpoint=endpoint, expected_status=200)
        if isinstance(response_data, list):
            return response_data
        elif isinstance(response_data, dict):
            return response_data.get('elements', [])
        else:
            return []

    def create_tag(self, project_id: str, tag_data: Dict[str, Any]) -> Dict[str, Any]:
        endpoint = f"/projects/{project_id}/tags"
        return self._request(
            method="POST",
            endpoint=endpoint,
            data=tag_data,
            expected_status=200 
        )

    def get_tag_by_id(self, project_id: str, tag_id: str) -> Dict[str, Any]:
        endpoint = f"/projects/{project_id}/tags/{tag_id}"
        return self._request(method="GET", endpoint=endpoint, expected_status=200)

    def delete_tag(self, project_id: str, tag_id: str) -> None:
        endpoint = f"/projects/{project_id}/tags/{tag_id}"
        self._request(method="DELETE", endpoint=endpoint, expected_status=204)
        return None

    # --- Element/Relationship Listing ---

    def list_elements(self, project_id: str, commit_id: str = "main") -> List[Dict[str, Any]]:
        endpoint = f"/projects/{project_id}/commits/{commit_id}/elements"
        response_data = self._request(method="GET", endpoint=endpoint, expected_status=200)
        if isinstance(response_data, list):
            return response_data
        elif isinstance(response_data, dict):
            return response_data.get('elements', [])
        else:
            return []

    def list_relationships(
        self,
        project_id: str,
        related_element_id: str,
        commit_id: str = "main",
        direction: str = "both"
    ) -> List[Dict[str, Any]]:
        endpoint = f"/projects/{project_id}/commits/{commit_id}/elements/{related_element_id}/relationships"
        params = {'direction': direction}
        response_data = self._request(method="GET", endpoint=endpoint, params=params, expected_status=200)
        if isinstance(response_data, list):
            return response_data
        elif isinstance(response_data, dict):
            return response_data.get('elements', [])
        else:
            return []