"""Commandline interface to Metax."""
import configparser
import io
import json
import logging
import os

import click
from requests.exceptions import HTTPError

import metax_access

DEFAULT_CONFIG_FILES = ['/etc/metax.cfg',
                        '~/.local/etc/metax.cfg',
                        '~/.metax.cfg']


def print_response(dictionary, fpath=None):
    """Print dictionary to stdout or file.

    :param dictionary: dictionary
    :param fpath: Path to the file where output is written
    :returns: ``None``
    """
    output = json.dumps(dictionary, indent=4, ensure_ascii=False)
    if not fpath:
        print(output)
    else:
        with io.open(fpath, "wt") as _file:
            _file.write(output)


@click.group()
@click.option(
    '-c', '--config',
    metavar='config',
    default=None,
    help=("Configuration file. If not set, default config file: "
          "~/.metax.cfg, ~/.local/etc/metax.cfg, or /etc/metax.cfg is used.")
)
@click.option('--host', metavar='host', help="Metax hostname")
@click.option('-u', '--user', metavar='user', help="Metax username")
@click.option('-p', '--password', metavar='password', help="Metax password")
@click.option('-t', '--token', metavar='token', help="Bearer token")
@click.pass_context
def cli(ctx, config, **kwargs):
    """Manage metadata in Metax."""
    # Choose config file
    if config:
        config = os.path.expanduser(config)
        if not os.path.isfile(config):
            raise click.UsageError(f'Configuration file {config} not found.')
    else:
        for file_ in DEFAULT_CONFIG_FILES:
            file_ = os.path.expanduser(file_)
            if os.path.isfile(file_):
                config = file_

    # Read config file
    if config:
        configuration = configparser.ConfigParser()
        configuration.read(config)
        metax_config = dict(configuration['metax'])
    else:
        metax_config = dict()

    # Override default configuration with CLI arguments
    for key, value in kwargs.items():
        if value:
            metax_config[key] = value

    # Init metax client
    if not metax_config.get('host'):
        raise click.UsageError("Metax hostname must be provided.")
    if not metax_config.get('token') and not metax_config.get('user'):
        raise click.UsageError(
            'Username and password or access token must be provided.'
        )
    ctx.obj = metax_access.Metax(**metax_config)


@cli.command()
@click.argument('resource',
                type=click.Choice(['file', 'dataset', 'contract']))
@click.argument('filepath',
                type=click.Path(exists=True, readable=True))
@click.option('-o', '--output',
              metavar='output',
              help="Path to the file where output is written")
@click.pass_obj
def post(metax_client, resource, filepath, output):
    """Post resource metadata from FILEPATH.

    Resource can be file, dataset or contract.
    """
    # Read metadata file
    with io.open(filepath, "rt") as open_file:
        data = json.load(open_file)

    funcs = {
        "dataset": metax_client.post_dataset,
        "file": metax_client.post_file,
        "contract": metax_client.post_contract
    }
    try:
        response = funcs[resource](data)
    except metax_access.ResourceAlreadyExistsError as exception:
        response = exception.message

    print_response(response, output)


@cli.command()
@click.argument('resource',
                type=click.Choice(['file', 'dataset', 'contract', 'template']))
@click.argument('identifier')
@click.option('-o', '--output',
              metavar='output',
              help="Path to the file where output is written")
@click.pass_obj
def get(metax_client, resource, identifier, output):
    """Print resource identified by IDENTIFIER.

    The resource can be file, dataset or contract metadata, or template
    for dataset metadata.
    """
    if resource == 'template':
        if identifier == 'dataset':
            response = metax_client.get_dataset_template()
        else:
            raise ValueError("Only supported template is: 'dataset'")

    else:
        funcs = {
            "dataset": metax_client.get_dataset,
            "file": metax_client.get_file,
            "contract": metax_client.get_contract
        }
        try:
            response = funcs[resource](identifier)
        except metax_access.ResourceNotAvailableError:
            response = {"code": 404, "message": "Not found"}

    print_response(response, output)


@cli.command()
@click.argument('resource',
                type=click.Choice(['file', 'dataset', 'contract']))
@click.argument('identifier')
@click.pass_obj
def delete(metax_client, resource, identifier):
    """Delete resource identified by IDENTIER.

    Resource can be file, dataset or contract metadata.
    """
    funcs = {
        "dataset": metax_client.delete_dataset,
        "file": metax_client.delete_file,
        "contract": metax_client.delete_contract
    }
    funcs[resource](identifier)


@cli.command()
@click.argument('resource',
                type=click.Choice(['dataset', 'file', 'contract']))
@click.argument('identifier')
@click.argument('filepath', type=click.Path(exists=True, readable=True))
@click.option('-o', '--output',
              metavar='output',
              help="Path to the file where output is written")
@click.pass_obj
def patch(metax_client, resource, identifier, filepath, output):
    """Patch resource IDENTIFIER with metadata from FILEPATH.

    Resource can be file, dataset or contract metadata.
    """
    with io.open(filepath, "rt") as open_file:
        data = json.load(open_file)

    funcs = {
        "dataset": metax_client.patch_dataset,
        "file": metax_client.patch_file,
        "contract": metax_client.patch_contract
    }
    try:
        response = funcs[resource](identifier, data)
    except metax_access.ResourceNotAvailableError:
        response = {"code": 404, "message": "Not found"}

    print(response, output)


@cli.command()
@click.option('--identifier', help="Directory identifier")
@click.option('--path', help="Directory path")
@click.option('--project', help="Project identifier")
@click.option('--files',
              is_flag=True,
              default=False,
              help="List files in directory")
@click.pass_obj
def directory(metax_client, identifier, path, project, files):
    """Print directory.

    Directory can be chosen using the directory identifier or path.
    """
    if identifier and path:
        raise click.UsageError('--identifier and --path can not be used '
                               'same time.')
    if path and not project:
        raise click.UsageError("--project argument is required for searching "
                               "directory by path.")
    if identifier:
        directory_metadata = metax_client.get_directory(identifier)
    elif path:
        directory_metadata \
            = metax_client.get_project_directory(project, path)

    if files:
        print_response(
            metax_client.get_directory_files(
                directory_metadata["identifier"]
            )
        )
    else:
        print_response(directory_metadata)


@cli.command()
@click.argument('identifier')
@click.pass_obj
def file_datasets(metax_client, identifier):
    """Print datasets associated with file IDENTIFIER."""
    print_response(metax_client.get_file_datasets(identifier))


if __name__ == "__main__":
    try:
        # pylint: disable=no-value-for-parameter
        cli()
    except HTTPError as exception:
        if exception.response.status_code > 499:
            raise

        logging.error("Metax responded with HTTPError %s: %s.",
                      exception.response.status_code,
                      exception.response.reason)

        try:
            print_response(exception.response.json())
        except ValueError:
            print(exception.response.data)
