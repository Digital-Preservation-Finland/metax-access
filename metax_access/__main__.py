"""Commandline interface to Metax."""
import configparser
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
        click.echo(output)
    else:
        with open(fpath, 'wt') as file:
            click.echo(output, file=file)


@click.group(context_settings={"help_option_names": ['-h', '--help']})
@click.option(
    '-c', '--config',
    default=None,
    help=("Configuration file. If not set, default config file: "
          "~/.metax.cfg, ~/.local/etc/metax.cfg, or /etc/metax.cfg is used.")
)
@click.option('--url', help="Metax url.")
@click.option('-u', '--user', help="Metax username.")
@click.option('-p', '--password', help="Metax password.")
@click.option('-t', '--token', help="Bearer token.")
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
    if not metax_config.get('url'):
        try:
            # Accept also 'host' parameter for backward compatibility
            metax_config['url'] = metax_config['host']
        except KeyError:
            raise click.UsageError("Metax URL must be provided.")
    if not metax_config.get('token') and not metax_config.get('user'):
        raise click.UsageError(
            'Username and password or access token must be provided.'
        )
    if metax_config.get('host'):
        del metax_config['host']
    ctx.obj = metax_access.Metax(**metax_config)


@cli.command()
@click.argument('resource', type=click.Choice(['file', 'dataset', 'contract']))
@click.argument('filepath', type=click.Path(exists=True, readable=True))
@click.option('-o', '--output',
              help="Path to the file where output is written.")
@click.pass_obj
def post(metax_client, resource, filepath, output):
    """Post resource metadata to Metax.

    Resource can be file, dataset or contract. The metadata is read from
    FILEPATH.
    """
    # Read metadata file
    with open(filepath, "rt") as open_file:
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
              help="Path to the file where output is written.")
@click.pass_obj
def get(metax_client, resource, identifier, output):
    """Print resource metadata.

    The resource type can be file, dataset or contract metadata, or
    template for dataset metadata. The resource is identified by
    IDENTIFIER.
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
@click.argument('resource', type=click.Choice(['file', 'dataset', 'contract']))
@click.argument('identifier')
@click.pass_obj
def delete(metax_client, resource, identifier):
    """Delete resource metadata.

    Resource can be file, dataset or contract metadata. The resource is
    identified by IDENTIFIER.
    """
    funcs = {
        "dataset": metax_client.delete_dataset,
        "file": metax_client.delete_file,
        "contract": metax_client.delete_contract
    }
    funcs[resource](identifier)


@cli.command()
@click.argument('resource', type=click.Choice(['dataset', 'file', 'contract']))
@click.argument('identifier')
@click.argument('filepath', type=click.Path(exists=True, readable=True))
@click.option('-o', '--output',
              help="Path to the file where output is written.")
@click.pass_obj
def patch(metax_client, resource, identifier, filepath, output):
    """Patch resource metadata.

    The metadata patch is read from FILEPATH. Resource can be file,
    dataset or contract metadata. The resource is identified by
    IDENTIFIER.
    """
    with open(filepath, "rt") as open_file:
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

    print_response(response, output)


@cli.command()
@click.option('--identifier', help="Directory identifier.")
@click.option('--path', help="Directory path.")
@click.option('--project', help="Project identifier.")
@click.option('--files',
              is_flag=True,
              default=False,
              help="List files in directory.")
@click.pass_obj
def directory(metax_client, identifier, path, project, files):
    """Print directory metadata or content.

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


@cli.command('file-datasets')
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
            click.echo(exception.response.data)
