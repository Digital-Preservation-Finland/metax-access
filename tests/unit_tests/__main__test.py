"""Tests for `metax_acces.__main__` module"""

import metax_access
import pytest
import mock
import json


@pytest.mark.parametrize(
    ('arguments', 'function'),
    [
        (['post', 'dataset', 'foo'], 'metax_access.__main__.post'),
        (['patch', 'dataset', 'foo', 'bar'], 'metax_access.__main__.patch'),
        (['delete', 'dataset', 'foo'], 'metax_access.__main__.delete')
    ]
)
def test_main(arguments, function):
    """Test that main function calls correct function for each subcommand

    :param arguments: list of command line arguments
    :param function: name of function excepted to be called

    """
    with mock.patch(function) as expected_function:
        metax_access.__main__.main(
            ['--host', 'foo', '--token', 'bar']+arguments
        )

    # Expected function should be called once
    assert expected_function.called_once()

    # first parameter of called function should be Metax object
    metax_client = expected_function.call_args[0][0]
    assert isinstance(metax_client, metax_access.Metax)
    assert metax_client.baseurl == 'foo/rest/v1'
    assert metax_client.token == 'bar'

    # second parameter of called function should contain commandline args
    args = expected_function.call_args[0][1]
    assert args.resource == 'dataset'
    assert args.host == 'foo'
    assert args.token == 'bar'


@pytest.mark.parametrize(
    ('arguments', 'error_message'),
    [
        (['post', 'dataset', 'foo'],
         'Metax hostname must be provided.'),
        (['--host', 'bar', 'post', 'dataset', 'foo'],
         'Username and password or access token must be provided.'),
        (['--config', '/dev/null', 'post', 'dataset', 'foo'],
         'Configuration file /dev/null not found.'),
    ]
)
def test_invalid_arguments(arguments, error_message, monkeypatch, capsys):
    """Test main function with invalid arguments

    :param arguments: list of command line arguments
    :param error_message: expected error message
    :param monkeypatch: monkeypatch fixture
    :param capsys: capsys fixture
    """
    # Disable default config files
    monkeypatch.setattr('metax_access.__main__.DEFAULT_CONFIG_FILES', [])

    # Script should exit with code 2
    with pytest.raises(SystemExit) as exception:
        metax_access.__main__.main(arguments)
    assert exception.value.code == 2

    # Error message should be printed to stderr
    #
    # TODO: In pytest>=3.5, stderr is simply:
    #    capsys.readouterr().err
    # Change this when newer version of pytest is available on Centos
    _, stderr = capsys.readouterr()
    assert stderr.endswith(error_message + "\n")


# TODO: Replace tmpdir fixture with tmp_path fixture when pytest>=3.9.1 is
# available on Centos
def test_output(tmpdir, monkeypatch):
    """Test that output is written to file when --output parameter is used.

    :param tmpdir: Temporary directory for test data
    :param monkeypatch: monkeypatch fixture
    """
    # Mock get_dataset-function to always return simple dict
    monkeypatch.setattr('metax_access.Metax.get_dataset',
                        lambda *args: {'foo': 'bar'})

    # Use main function to get test data to output file
    output_file = tmpdir / 'output_file'
    arguments = ['--host', 'foo',
                 '--token', 'bar',
                 'get', 'dataset', '1',
                 '--output', str(output_file)]
    metax_access.__main__.main(arguments)

    # Check that JSON output was written to file
    assert json.loads(output_file.read())['foo'] == 'bar'
