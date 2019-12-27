"""Tests for `metax_acces.__main__` module"""

import metax_access.__main__
import pytest


@pytest.mark.parametrize(
    ('arguments', 'function'),
    [
        (['post', 'dataset', 'foo'], 'metax_access.__main__.post'),
        (['patch', 'dataset', 'foo', 'bar'], 'metax_access.__main__.patch'),
        (['delete', 'dataset', 'foo'], 'metax_access.__main__.delete')
    ]
)
def test_main(arguments, function, mocker):
    """Test that main function calls correct function for each subcommand

    :param arguments: list of command line arguments
    :param function: name of function excepted to be called
    :param mocker: mocker fixture

    """
    # Mock function that should be called in main
    mocked_function = mocker.patch(function)

    # Run main
    metax_access.__main__.main(['--host', 'foo', '--token', 'bar']+arguments)

    # Expected function should be called once
    assert mocked_function.called_once()


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
