# PYTHON_ARGCOMPLETE_OK
"""Commandline interface to Metax."""
from __future__ import unicode_literals
from __future__ import print_function

import argparse
import configparser
import io
import json
import logging
import os

import argcomplete
from requests.exceptions import HTTPError
import six

import metax_access

DEFAULT_CONFIG_FILES = ['/etc/metax.cfg',
                        '~/.local/etc/metax.cfg',
                        '~/.metax.cfg']


def post(metax_client, args):
    """Post file/dataset to Metax and print the result.

    :param metax_client: `metax_access.Metax` instance
    :param args: Named tuple of parsed arguments from
                 :func:`__main__.parse_args()`
    """
    # Read metadata file
    with io.open(args.filepath, "rt") as open_file:
        data = json.load(open_file)

    funcs = {
        "dataset": metax_client.post_dataset,
        "file": metax_client.post_file,
        "contract": metax_client.post_contract
    }
    try:
        response = funcs[args.resource](data)
    except metax_access.ResourceAlreadyExistsError as exception:
        response = exception.message

    _pprint(response, args.output)


def get(metax_client, args):
    """Get file, dataset, or contract.

    :param metax_client: `metax_access.Metax` instance
    :param args: Named tuple of parsed arguments from
                 :func:`__main__.parse_args()`
    """
    if args.resource == 'template':
        if args.identifier == 'dataset':
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
            response = funcs[args.resource](args.identifier)
        except metax_access.ResourceNotAvailableError:
            response = {"code": 404, "message": "Not found"}

    _pprint(response, args.output)


def delete(metax_client, args):
    """Delete file, dataset, or contract.

    :param metax_client: `metax_access.Metax` instance
    :param args: Named tuple of parsed arguments from
                 :func:`__main__.parse_args()`
    """
    funcs = {
        "dataset": metax_client.delete_dataset,
        "file": metax_client.delete_file,
        "contract": metax_client.delete_contract
    }
    funcs[args.resource](args.identifier)


def patch(metax_client, args):
    """Patch file, dataset, or contract.

    :param metax_client: `metax_access.Metax` instance
    :param args: Named tuple of parsed arguments from
                 :func:`__main__.parse_args()`
    """
    with io.open(args.filepath, "rt") as open_file:
        data = json.load(open_file)

    funcs = {
        "dataset": metax_client.patch_dataset,
        "file": metax_client.patch_file,
        "contract": metax_client.patch_contract
    }
    try:
        response = funcs[args.resource](args.identifier, data)
    except metax_access.ResourceNotAvailableError:
        response = {"code": 404, "message": "Not found"}

    _pprint(response, args.output)


def _pprint(dictionary, fpath=None):
    """Pretty print dictionary to stdout.

    :param dictionary: dictionary
    :param fpath: Path to the file where output is written
    :returns: ``None``
    """
    output = json.dumps(dictionary, indent=4, ensure_ascii=False)
    if not fpath:
        print(output)
    else:
        with io.open(fpath, "wt") as _file:
            _file.write(six.text_type(output))


def main(arguments=None):
    """Run command defined by commandline arguments.

    :param arguments: list of commandline arguments
    """
    # Parser
    parser = argparse.ArgumentParser(description="Manage metadata in Metax.")
    parser.add_argument('-c', '--config',
                        metavar='config',
                        default=None,
                        help="Configuration file. If not set, default config "
                             "file: ~/.metax.cfg, ~/.local/etc/metax.cfg, "
                             "or /etc/metax.cfg is used.")
    parser.add_argument('--host',
                        metavar='host',
                        help="Metax hostname")
    parser.add_argument('-u', '--user',
                        metavar='user',
                        help="Metax username")
    parser.add_argument('-p', '--password',
                        metavar='password',
                        help="Metax password")
    parser.add_argument('-t', '--token',
                        metavar='token',
                        help="Bearer token")
    subparsers = parser.add_subparsers(title='command')

    # Post command parser
    post_parser = subparsers.add_parser(
        'post',
        help='Post file, dataset or contract metadata.'
    )
    post_parser.add_argument('resource',
                             choices=('file', 'dataset', 'contract'),
                             help="Resource type")
    post_parser.add_argument('filepath',
                             help="Path to metadata file")
    post_parser.set_defaults(func=post)
    post_parser.add_argument('-o', '--output',
                             metavar='output',
                             help="Path to the file where output is written")

    # Get command parser
    get_parser = subparsers.add_parser(
        'get',
        help=('Print file, dataset or contract metadata, or template for '
              'dataset metadata.')
    )
    get_parser.add_argument(
        'resource',
        choices=('file', 'dataset', 'contract', 'template'),
        help="Resource type"
    )
    get_parser.add_argument('identifier',
                            help="Resource identifier")
    get_parser.set_defaults(func=get)
    get_parser.add_argument('-o', '--output',
                            metavar='output',
                            help="Path to the file where output is written")

    # Delete command parser
    delete_parser = subparsers.add_parser(
        'delete',
        help='Delete file, dataset or contract metadata'
    )
    delete_parser.add_argument('resource',
                               choices=('file', 'dataset', 'contract'),
                               help="Resource type")
    delete_parser.add_argument('identifier',
                               help="Resource identifier")
    delete_parser.set_defaults(func=delete)

    # Patch command parser
    patch_parser = subparsers.add_parser(
        'patch',
        help='Patch file, dataset or contract metadata'
    )
    patch_parser.add_argument('resource',
                              choices=('dataset', 'file', 'contract'),
                              help="Resource type")
    patch_parser.add_argument('identifier', help="Resource identifier")
    patch_parser.add_argument('filepath',
                              help="Path to metadata patch file")
    patch_parser.set_defaults(func=patch)
    patch_parser.add_argument('-o', '--output',
                              metavar='output',
                              help="Path to the file where output is written")

    # Bash tab completion
    argcomplete.autocomplete(parser)

    # Choose config file
    config = parser.parse_args(arguments).config
    if config:
        config = os.path.expanduser(config)
        if not os.path.isfile(config):
            # Explicitly set config file does not exist
            parser.error('Configuration file {} not found.'.format(config))
    else:
        for file_ in DEFAULT_CONFIG_FILES:
            file_ = os.path.expanduser(file_)
            if os.path.isfile(file_):
                config = file_

    # Read config file and use options as defaults when parsing command
    # line arguments
    if config:
        configuration = configparser.ConfigParser()
        configuration.read(config)
        parser.set_defaults(**configuration['metax'])

    # Parse arguments
    args = parser.parse_args(arguments)

    # Init metax client
    if not args.host:
        parser.error("Metax hostname must be provided.")
    if args.token:
        credentials = {'token': args.token}
    elif args.user:
        credentials = {'user': args.user, 'password': args.password}
    else:
        parser.error('Username and password or access token must be provided.')
    metax_client = metax_access.Metax(args.host, **credentials)

    # Run command
    try:
        args.func(metax_client, args)
    except HTTPError as exception:
        if exception.response.status_code > 499:
            raise

        logging.error("Metax responded with HTTPError %s: %s.",
                      exception.response.status_code,
                      exception.response.reason)

        try:
            _pprint(exception.response.json())
        except ValueError:
            print(exception.response.data)


if __name__ == "__main__":
    main()
