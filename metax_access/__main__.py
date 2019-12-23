# PYTHON_ARGCOMPLETE_OK
"""Commandline interface to Metax."""
from __future__ import unicode_literals
from __future__ import print_function

import argparse
import configparser
import io
import json
import os
import sys

import argcomplete
from requests.exceptions import HTTPError

import metax_access

DEFAULT_CONFIG_FILES = ['/etc/metax.cfg',
                        '~/.local/etc/metax.cfg',
                        '~/.metax.cfg']


def _get_metax_error(error):
    """Return Metax error message"""
    try:
        response = error.response.json()
    except ValueError:
        response = {
            "code": error.response.status_code,
            "message": "Metax did not return a json response"
        }

    return response


def post(metax_client, args):
    """Post file/dataset to Metax and print the result

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
    except HTTPError as error:
        if error.response.status_code > 499:
            raise
        response = _get_metax_error(error)

    _pprint(response, args.output)


def get(metax_client, args):
    """Get file, dataset, or contract

    :param metax_client: `metax_access.Metax` instance
    :param args: Named tuple of parsed arguments from
                 :func:`__main__.parse_args()`
    """
    if args.resource == 'template':
        if args.identifier == 'dataset':
            try:
                response = metax_client.get_dataset_template()
            except HTTPError as error:
                if error.response.status_code > 499:
                    raise
                response = _get_metax_error(error)
        else:
            raise ValueError("Only supported template is: 'dataset'")

    else:
        funcs = {
            "dataset": metax_client.get_dataset,
            "file": metax_client.get_file,
            "contract": metax_client.get_contract
        }
        try:
            response = funcs[args.resource](
                args.identifier,
                custom_errors=False
            )
        except HTTPError as error:
            if error.response.status_code > 499:
                raise
            response = _get_metax_error(error)

    _pprint(response, args.output)


def delete(metax_client, args):
    """Delete file, dataset, or contract

    :param metax_client: `metax_access.Metax` instance
    :param args: Named tuple of parsed arguments from
                 :func:`__main__.parse_args()`
    """
    funcs = {
        "dataset": metax_client.delete_dataset,
        "file": metax_client.delete_file,
        "contract": metax_client.delete_contract
    }
    try:
        funcs[args.resource](args.identifier)
    except HTTPError as error:
        if error.response.status_code > 499:
            raise
        _pprint(_get_metax_error(error), args.output)


def patch(metax_client, args):
    """Patch file, dataset, or contract

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
        response = funcs[args.resource](
            args.identifier, data,
            custom_errors=False
        )
    except HTTPError as error:
        if error.response.status_code > 499:
            raise
        response = _get_metax_error(error)

    _pprint(response, args.output)


def _pprint(dictionary, fpath=None):
    """Pretty print dictionary to stdout

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


def main():
    """
    Parse arguments, init metax client, and run correct command depending
    on the action (post, get or delete).
    """
    # Parser
    parser = argparse.ArgumentParser(description="Manage metadata in Metax.")
    parser.add_argument('-c', '--config',
                        metavar='config',
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
    parser.add_argument('-o', '--output',
                        metavar='output',
                        help="Path to the file where output is written")
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

    # Get command parser
    get_parser = subparsers.add_parser(
        'get',
        help='Print file, dataset or contract metadata.'
    )
    get_parser.add_argument(
        'resource',
        choices=('file', 'dataset', 'contract', 'template'),
        help="Resource type"
    )
    get_parser.add_argument('identifier',
                            help="Resource identifier")
    get_parser.set_defaults(func=get)

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

    # Bash tab completion
    argcomplete.autocomplete(parser)

    # Parse arguments
    args = parser.parse_args()

    # Choose config file
    config = None
    if args.config:
        config = os.path.expanduser(args.config)
        if not os.path.isfile(config):
            # Explicitly set config file does not exist
            sys.exit('Configuration file {} not found.'.format(config))
    else:
        for file_ in DEFAULT_CONFIG_FILES:
            path = os.path.expanduser(file_)
            if os.path.isfile(path):
                config = path

    # Read config file
    configuration = configparser.ConfigParser()
    configuration.add_section('metax')
    if config:
        configuration.read(os.path.expanduser(config))

    # Override configuration file with commandline options
    for option in ['host', 'user', 'password', 'token']:
        if vars(args)[option]:
            configuration.set('metax', option)
        if not configuration.has_option('metax', option):
            sys.exit("Option '{}' is required".format(option))

    # Init metax client
    metax_client = metax_access.Metax(
        configuration.get('metax', 'host'),
        configuration.get('metax', 'user'),
        configuration.get('metax', 'password'),
        token=configuration.get('metax', 'token')
    )

    # Run command
    args.func(metax_client, args)


if __name__ == "__main__":
    main()
