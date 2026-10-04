# Releasing sysml-api-client

The distribution includes `sysmlv2_client` and `sysml_api`. The version comes
from `src/sysmlv2_client/__init__.py` (initial release: `0.1.0`).

## One-time setup

Register a pending Trusted Publisher from your PyPI organization's **Publishing**
page to create the project under organization ownership on the first upload.
If you manually create the project first, add a normal Trusted Publisher to
that project instead.

| Publisher field | PyPI | TestPyPI |
| --- | --- | --- |
| Project name | `sysml-api-client` | `sysml-api-client` |
| GitHub owner | `Open-MBEE` | `Open-MBEE` |
| Repository | `sysmlv2-python-client` | `sysmlv2-python-client` |
| Workflow filename | `publish.yml` | `publish.yml` |
| Environment | `pypi` | `testpypi` |

TestPyPI needs its own account and publisher configuration. Create GitHub
environments `pypi` and `testpypi`; configure required reviewers for `pypi`
and restrict it to release tags as appropriate. No PyPI token secret is needed.
Check that PyPI accepts the project name; a pending publisher does not reserve it.

References: [organization pending publishers](https://blog.pypi.org/posts/2025-11-10-trusted-publishers-coming-to-orgs/),
[existing project publishers](https://docs.pypi.org/trusted-publishers/adding-a-publisher/).

## Local validation

Create and activate a virtual environment, then run:

```bash
python -m pip install -e ".[test]" build twine
python -m pytest
python -m build
python -m twine check --strict dist/*
```

Start with an empty `dist/` directory. CI also tests the installed wheel outside
the checkout, imports both packages, and builds a wheel from the source archive.

## Release

1. Update `__version__` and `CHANGELOG.md`; each upload needs a new version.
2. Push the changes and wait for the test matrix and package checks to pass.
3. Run **Publish package** manually from the desired commit to upload to TestPyPI.
   For repeated rehearsals use new versions, such as `0.1.0rc1`, `0.1.0rc2`.
4. In a clean virtual environment, verify the candidate (substitute its version):

   ```bash
   python -m pip install requests
   python -m pip install --index-url https://test.pypi.org/simple/ --no-deps sysml-api-client==0.1.0
   python -c "import sysml_api; from sysmlv2_client import SysMLV2Client"
   ```

5. Publish a GitHub release tagged `v0.1.0` at the tested commit, substituting
   the actual version. This triggers production publishing. Approve the `pypi`
   environment deployment if configured. The workflow rejects mismatched tags.
6. Verify production installation in a fresh environment:

   ```bash
   python -m pip install sysml-api-client==0.1.0
   python -c "import sysml_api; from sysmlv2_client import SysMLV2Client"
   ```

Published files cannot be replaced on PyPI or TestPyPI. Increment the version
to correct a release.
