"""Configure py.test default values and functionality."""
import logging
import os
import shutil
import sys
import tempfile

from click.testing import CliRunner
import pytest

import metax_access.__main__

# Print debug messages to stdout
logging.basicConfig(level=logging.DEBUG)


# Prefer modules from source directory rather than from site-python
PROJECT_ROOT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')
)
sys.path.insert(0, PROJECT_ROOT_PATH)


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
