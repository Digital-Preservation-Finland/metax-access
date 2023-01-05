"""Commandline interface to Metax."""
import configparser
import json
import logging
import os

import click
from requests.exceptions import HTTPError

import metax_access


DEFAULT_CONFIG_FILES = ['/etc/metax.cfg',
                        f'{click.get_app_dir("metax-access")}/metax.cfg',
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
          "~/.metax.cfg, $XDG_CONFIG_HOME/metax-access/metax.cfg, or "
          "/etc/metax.cfg is used.")
)
@click.option('--url', help="Metax url.")
@click.option('-u', '--user', help="Metax username.")
@click.option('-p', '--password', help="Metax password.")
@click.option('-t', '--token', help="Bearer token.")
@click.option('--verify/--no-verify', help="Verify SSL certificate.",
              default=True)
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
        if value is not None:
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
    with open(filepath) as open_file:
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
    with open(filepath) as open_file:
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
              help="List content of directory instead of directory metadata.")
@click.pass_obj
def directory(metax_client, identifier, path, project, files):
    """Print directory metadata or content.

    Directory can be chosen using the directory identifier or path.
    If path is used, project must defined to identify the directory.
    """
    if identifier and path:
        raise click.UsageError('--identifier and --path can not be used '
                               'same time.')
    if path and not project:
        raise click.UsageError("--project argument is required for searching "
                               "directory by path.")
    if not identifier and not path:
        raise click.UsageError('--identifier or --path is required')
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


@cli.command('search-datasets')
@click.option(
    '--latest', is_flag=True,
    help="Only return latest versions."
)
@click.option(
    '--owner-id',
    help="Id of the person who owns the record in Metax."
)
@click.option(
    '--user-created',
    help='Id of the person who created the record in metax'
)
@click.option(
    '--curator',
    help='Curator identifier (field research_dataset-> curator-> identifier)'
)
@click.option(
    '--preferred-identifier',
    help=(
        'Use given preferred_identifier as filter. Returns a best guess of '
        'the record (always a single record!), by looking from Fairdata '
        'catalogs first, then from harvested catalogs. If the value of '
        'preferred_identifier contains special characters such as ampersands, '
        'the value has to be urlencoded.'
    )
)
@click.option(
    '--state',
    help=(
        'TPAS state (field preservation_state). Multiple states using '
        'OR-logic are queriable in the same request, e.g. state=5,6. See '
        'valid values from http://iow.csc.fi/model/mrd/CatalogRecord/ field '
        'preservation_state'
    )
)
@click.option(
    '--metadata-owner-org',
    help='Filter by dataset field metadata_owner_org'
)
@click.option(
    '--metadata-provider-user',
    help='Filter by dataset field metadata_provider_user'
)
@click.option(
    '--contract-org-identifier',
    help=(
        'Filter by dataset '
        'contract.contract_json.organization.organization_identifier. '
        'Restricted to permitted users.'
    )
)
@click.option(
    '--pas-filter',
    help=(
        "A specific filter that targets the following fields; "
        "research_dataset['title'], research_dataset['curator'][n]['name'], "
        "contract['contract_json']['title']. Restricted to permitted users."
    )
)
@click.option(
    '--data-catalog',
    help='Filter by data catalog urn identifier'
)
@click.option(
    '--offset', type=int,
    help='Offset for paging'
)
@click.option(
    '--limit', type=int,
    help='Limit for paging'
)
@click.option(
    '--ordering',
    help=(
        "Specify ordering of results by fields. Accepts a list of field names "
        "separated by a comma. Ordering can be reversed by prefixing field "
        "name with a '-' char."
    )
)
@click.option(
    '--actor-filter',
    help=(
        "Actor_filters are a collection of filter parameters for filtering "
        "according to the name or organizational/person ID of creator, "
        "curator, publisher or rights_holder actors. Actor type must be "
        "defined as a suffix in the filter name ('_person' or "
        "'_organization'). Actor type '_organization' finds matches from "
        "'is_member_of' -field if actor is a person. Multiple actor_filters "
        "can be applied simultaneously (AND) or separately (OR) by using "
        "'condition_separator'. Default separator is AND. If filtered by "
        "organizational/person ID, search needs to be made using complete "
        "IDs. Complete person IDs consist of 19 characters matching the "
        "following pattern: 0000-0002-1825-0097. Complete organizational IDs "
        "consist of at least 5 characters, the 5 first characters always "
        "being numbers (e.g. 00170 or 01901-H960). Examples: "
        "'?creator_person=person_name', "
        "'?creator_organization=organizational_id', "
        "'?publisher_organization=someorganisation&creator_person=person_name&"
        "condition_separator=or'"
    )
)
@click.option(
    '--api-version', type=int,
    help=(
        'Returns datasets that can be edited with certain api version. '
        'Possible values are 1 and 2.'
    )
)
@click.option(
    '--projects',
    help='Filter datasets with comma-separated list of IDA projects'
)
@click.option(
    '--editor-permissions-user',
    help='Filter datasets where user has editor permissions'
)
@click.option(
    '--fields',
    help=(
        'Comma separated list of fields that are returned. Note that nested '
        'fields are not supported.'
    )
)
@click.option(
    '--research-dataset-fields',
    help=(
        'Comma separated list of fields in research_dataset that are returned.'
    )
)
@click.option(
    '--include-legacy', is_flag=True,
    help=(
        'Includes legacy datasets in query. Parameter needs to be given when '
        'fetching, modifying or deleting legacy datasets.'
    )
)
@click.pass_obj
def search_datasets(metax_client, **search_filter_kwargs):
    """Search datasets using query parameters."""
    for search_filter, value in search_filter_kwargs.items():
        # Boolean values have to be converted to strings "true" and "false"
        if type(value) == bool:
            search_filter_kwargs[search_filter] = str(value).lower()

    print_response(metax_client.query_datasets(search_filter_kwargs))


def main():
    """Execute CLI and deal with HTTP errors."""
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


if __name__ == "__main__":
    main()
