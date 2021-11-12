"""Tests for `metax_acces.__main__` module."""
import json

import mock
import pytest

import metax_access.__main__


@pytest.mark.parametrize(
    ('arguments', 'function'),
    [
        (['post', 'dataset', 'foo'], 'metax_access.__main__.post'),
        (['patch', 'dataset', 'foo', 'bar'], 'metax_access.__main__.patch'),
        (['delete', 'dataset', 'foo'], 'metax_access.__main__.delete')
    ]
)
def test_main(arguments, function):
    """Test that main function calls correct function.

    :param arguments: list of command line arguments
    :param function: name of function excepted to be called
    """
    with mock.patch(function) as expected_function:
        expected_function.return_value = dict()
        metax_access.__main__.main(
            ['--host', 'foo', '--token', 'bar']+arguments
        )

    # Expected function should be called once
    assert expected_function.called_once()

    # first parameter of called function should be Metax object
    metax_client = expected_function.call_args[0][0]
    assert isinstance(metax_client, metax_access.Metax)
    assert metax_client.baseurl == 'foo/rest/v2'
    assert metax_client.token == 'bar'

    # second parameter of called function should contain cli args
    args = expected_function.call_args[0][1]
    assert args.resource == 'dataset'
    assert args.host == 'foo'
    assert args.token == 'bar'


@pytest.mark.parametrize(
    ('cli_args', 'expected_output'),
    [
        (
            ['directory', '--identifier', 'foo'],
            {'identifier': 'foo'}
        ),
        (
            ['directory', '--path', 'bar', '--project', 'baz'],
            {'identifier': 'foo2'}
        ),
        (
            ['directory', '--identifier', 'foo', '--files'],
            {'foo': 'bar'}
        )
    ]
)
def test_directory_command(requests_mock, capsys, cli_args, expected_output):
    """Test directory command.

    :param requests_mock: HTTP request mocker
    :param capsys: output capturer
    :param cli_args: list of commandline arguments
    :param expected_output: expected output as dictionary
    """
    # Mock metax
    requests_mock.get(
        'https://metax-test.csc.fi/rest/v2/directories/foo',
        json={'identifier': 'foo'}
    )
    requests_mock.get(
        'https://metax-test.csc.fi/rest/v2/directories/files?path=bar'
        '&project=baz&depth=1&directories_only=true&include_parent=true',
        json={'directories': None, 'identifier': 'foo2'}
    )
    requests_mock.get(
        'https://metax-test.csc.fi/rest/v2/directories/foo/files',
        json={'foo': 'bar'}
    )

    # Run command
    metax_access.__main__.main(cli_args)

    # Check output
    output = json.loads(capsys.readouterr().out)
    assert output == expected_output


def test_file_datasets_command(requests_mock, capsys):
    """Test file-datasets command.

    The command should send a POST request to Metax and print the
    content of response. The request content should be a list that
    contains the file identifier given as argument.

    :param requests_mock: HTTP request mocker
    :param capsys: output capturer
    """
    mocked_metax = requests_mock.post(
        'https://metax-test.csc.fi/rest/v2/files/datasets',
        json={'foo': 'bar'}
    )

    # Run command
    metax_access.__main__.main(['file-datasets', 'baz'])

    # Check that senf HTTP request has expected content
    request_history = mocked_metax.request_history
    assert len(request_history) == 1
    assert request_history[0].json() == ['baz']

    # Check the output
    output = json.loads(capsys.readouterr().out)
    assert output == {'foo': 'bar'}


@pytest.mark.parametrize(
    ('arguments', 'error_message'),
    [
        (['post', 'dataset', 'foo'],
         'Metax hostname must be provided.'),
        (['--host', 'bar', 'post', 'dataset', 'foo'],
         'Username and password or access token must be provided.'),
        (['--config', '/dev/null', 'post', 'dataset', 'foo'],
         'Configuration file /dev/null not found.'),
        (['--host', 'foo', '--token', 'bar', 'directory', '--path', 'baz'],
         '--project argument is required for searching directory by path.')
    ]
)
def test_invalid_arguments(arguments, error_message, monkeypatch, capsys):
    """Test main function with invalid arguments.

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


# TODO: Replace tmpdir fixture with tmp_path fixture when pytest>=3.9.1
# is available on Centos
def test_output(tmpdir, monkeypatch):
    """Test --output parameter.

    Output should be  written to file when --output parameter is used.

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
