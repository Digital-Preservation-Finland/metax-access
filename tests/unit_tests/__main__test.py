"""Tests for `metax_acces.__main__` module."""
import json
import shutil

import pytest
from click.testing import CliRunner

import metax_access.__main__


@pytest.fixture(autouse=True)
def mock_default_config(tmpdir, monkeypatch):
    """Use temporary configuration file by default.

    Copy include/etc/metax.cfg to a temporary directory, and mock CLI to
    use that file as a default configuration file.
    """
    tmp_configuration_file = tmpdir / 'metax.cfg'
    shutil.copy('include/etc/metax.cfg', tmp_configuration_file)

    monkeypatch.setattr('metax_access.__main__.DEFAULT_CONFIG_FILES',
                        [tmp_configuration_file])


@pytest.mark.parametrize(
    ('arguments', 'expected_requests'),
    [
        (
            ['post', 'dataset', 'test_file.json'],
            [
                {
                    'method': 'POST',
                    'url': 'https://metax.localhost/rest/v2/datasets/'
                }
            ],
        ),
        (
            ['patch', 'dataset', 'foo', 'test_file.json'],
            [
                {
                    'method': 'GET',
                    'url': 'https://metax.localhost/rest/v2/datasets/foo'
                    '?include_user_metadata=true'
                },
                {
                    'method': 'PATCH',
                    'url': 'https://metax.localhost/rest/v2/datasets/foo'
                }
            ]
         ),
        (
            ['delete', 'dataset', 'foo'],
            [
                {
                    'method': 'DELETE',
                    'url': 'https://metax.localhost/rest/v2/datasets/foo'
                }
            ]
        )

    ]
)
def test_main(requests_mock, tmpdir, arguments, expected_requests):
    """Test that cli sends HTTP requests to correct url.

    :param requests_mock: HTTP request mocker
    :param tmpdir: Temporary directory for metadata files
    :param arguments: list of command line arguments
    :param expected_requests: list of HTTP requests expected to be sent
                              to Metax. A request is dictionary that
                              contains two values: "method" and "url".
    """
    # Mock Metax
    mocked_metax_responses = [
        requests_mock.register_uri(
            request['method'], request['url'], json={'foo2': 'bar2'}
        ) for request in expected_requests
    ]

    # Create a test_file
    test_file = tmpdir / 'test_file.json'
    test_file.write('{"foo1": "bar1"}')

    # Run CLI in directory that contains test_file.json
    runner = CliRunner()
    with tmpdir.as_cwd():
        result = runner.invoke(metax_access.__main__.cli,
                               arguments,
                               catch_exceptions=False)
    assert result.exit_code == 0

    # Each expected request should be sent once
    for response in mocked_metax_responses:
        assert response.called_once


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
def test_directory_command(requests_mock, cli_args, expected_output):
    """Test directory command.

    :param requests_mock: HTTP request mocker
    :param cli_args: list of commandline arguments
    :param expected_output: expected output as dictionary
    """
    # Mock metax
    requests_mock.get(
        'https://metax.localhost/rest/v2/directories/foo',
        json={'identifier': 'foo'}
    )
    requests_mock.get(
        'https://metax.localhost/rest/v2/directories/files?path=bar'
        '&project=baz&depth=1&directories_only=true&include_parent=true',
        json={'directories': None, 'identifier': 'foo2'}
    )
    requests_mock.get(
        'https://metax.localhost/rest/v2/directories/foo/files',
        json={'foo': 'bar'}
    )

    # Run command and check that it produces expceted output
    runner = CliRunner()
    result = runner.invoke(metax_access.__main__.cli,
                           cli_args,
                           catch_exceptions=False)
    assert json.loads(result.output) == expected_output


def test_file_datasets_command(requests_mock):
    """Test file-datasets command.

    The command should send a POST request to Metax and print the
    content of response. The request content should be a list that
    contains the file identifier given as argument.

    :param requests_mock: HTTP request mocker
    """
    mocked_metax = requests_mock.post(
        'https://metax.localhost/rest/v2/files/datasets',
        json={'foo': 'bar'}
    )

    # Run command. Command should output JSON from Metax response.
    runner = CliRunner()
    result = runner.invoke(metax_access.__main__.cli,
                           ['file-datasets', 'baz'],
                           catch_exceptions=False)
    assert json.loads(result.output) == {'foo': 'bar'}

    # Check that sent HTTP request has expected content
    request_history = mocked_metax.request_history
    assert len(request_history) == 1
    assert request_history[0].json() == ['baz']


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
def test_invalid_arguments(arguments, error_message, monkeypatch):
    """Test main function with invalid arguments.

    :param arguments: list of command line arguments
    :param error_message: expected error message
    :param monkeypatch: monkeypatch fixture
    """
    # Disable default config files
    monkeypatch.setattr('metax_access.__main__.DEFAULT_CONFIG_FILES', [])

    # Run command
    runner = CliRunner()
    result = runner.invoke(metax_access.__main__.cli, arguments)

    # Script should exit with code 2
    assert result.exit_code == 2

    # Error message should be printed to stdout
    assert result.output.endswith(error_message + '\n')


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
    runner = CliRunner()
    result = runner.invoke(metax_access.__main__.cli, arguments)

    # Nothing should be printed to stdout
    assert result.output == ''

    # Check that JSON output was written to file
    assert json.loads(output_file.read())['foo'] == 'bar'
