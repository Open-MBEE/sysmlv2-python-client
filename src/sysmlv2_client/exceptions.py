# src/sysmlv2_client/exceptions.py

"""
Custom exceptions for the SysML v2 Python Client.
"""

class SysMLV2Error(Exception):
    """Base class for exceptions in this module."""
    pass

class SysMLV2AuthError(SysMLV2Error):
    """Exception raised for authentication errors."""
    pass

class SysMLV2APIError(SysMLV2Error):
    """Exception raised for errors returned by the SysML v2 API."""
    def __init__(self, status_code, message="API request failed"):
        self.status_code = status_code
        self.message = f"{message} (Status code: {status_code})"
        super().__init__(self.message)

class SysMLV2NotFoundError(SysMLV2APIError):
    """Exception raised when a requested resource is not found (404)."""
    def __init__(self, message="Resource not found"):
        super().__init__(status_code=404, message=message)

class SysMLV2BadRequestError(SysMLV2APIError):
    """Exception raised for bad requests (400)."""
    def __init__(self, message="Bad request"):
        super().__init__(status_code=400, message=message)

class SysMLV2ConflictError(SysMLV2APIError):
    """Exception raised for conflicts (409)."""
    def __init__(self, message="Conflict detected"):
        super().__init__(status_code=409, message=message)