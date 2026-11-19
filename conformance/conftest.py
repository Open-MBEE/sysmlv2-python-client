import os

import pytest

from .provider import Provider

ANNEX_GROUPS = {
    "test_project_service": ("PS", 4),
    "test_element_navigation": ("EN", 5),
    "test_versioning": ("PCB", 15),
    "test_queries": ("QS", 2),
    "test_external_relationship": ("ER", 3),
}


def pytest_generate_tests(metafunc):
    if metafunc.function.__name__ in ANNEX_GROUPS:
        prefix, count = ANNEX_GROUPS[metafunc.function.__name__]
        metafunc.parametrize("annex", [
            pytest.param(number, id=f"PIM-{prefix}-{number:03}")
            for number in range(1, count + 1)
        ])


def pytest_addoption(parser):
    parser.addoption("--live", action="store_true", help="Run live provider and client tests")
    parser.addoption("--provider-build", help="Provider build identifier for test evidence")


def pytest_configure(config):
    if config.getoption("--live") and (
        not os.getenv("SYSML_CONFORMANCE_URL") or not config.getoption("--provider-build")
    ):
        raise pytest.UsageError("--live requires SYSML_CONFORMANCE_URL and --provider-build")


@pytest.fixture
def api(pytestconfig, record_property):
    if not pytestconfig.getoption("--live"):
        pytest.skip("Live provider run requires --live")
    record_property("provider_build", pytestconfig.getoption("--provider-build"))
    server = Provider(os.environ["SYSML_CONFORMANCE_URL"], os.getenv("SYSML_CONFORMANCE_TOKEN"))
    try:
        yield server
    finally:
        errors = []
        try:
            for project in reversed(server.projects):
                try:
                    server.call("deleteProjectById", projectId=project, status=(200, 204, 404))
                except AssertionError as error:
                    errors.append(str(error))
        finally:
            record_property("http_evidence", "; ".join(server.evidence))
            server.session.close()
        if errors:
            pytest.fail("Project cleanup: " + "; ".join(errors))
