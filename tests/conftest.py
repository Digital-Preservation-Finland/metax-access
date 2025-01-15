"""Configure py.test default values and functionality."""
import logging
import os
import shutil
import sys
import tempfile

import pytest
from click.testing import CliRunner

import metax_access.__main__
from metax_access import Metax

# Print debug messages to stdout
logging.basicConfig(level=logging.DEBUG)


# Prefer modules from source directory rather than from site-python
PROJECT_ROOT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')
)
sys.path.insert(0, PROJECT_ROOT_PATH)

def pytest_addoption(parser):
    """Add --v3 option."""
    parser.addoption('--v3', action='store_const', const=True)


@pytest.fixture(scope="function")
def testpath(request):
    """Create and cleanup a temporary directory.

    :request: Pytest request fixture
    """
    temp_path = tempfile.mkdtemp()

    def fin():
        """Remove temporary path."""
        shutil.rmtree(temp_path)
    request.addfinalizer(fin)

    return temp_path


@pytest.fixture(scope="function")
def cli_invoke():
    """Create a wrapper for CliRunner.invoke."""

    def wrapper(args, **kwargs):
        """Invoke a metax-access CLI command in an isolated environment."""
        runner = CliRunner()
        result = runner.invoke(metax_access.__main__.cli,
                               args,
                               catch_exceptions=False,
                               **kwargs)
        return result

    return wrapper


@pytest.fixture(scope="function")
def metax_v3():
    """Return Metax client configured for Metax V3"""
    return Metax(
        "https://foobar",
        user="tpas", password="password",
        api_version="v3",
        verify=False
    )
