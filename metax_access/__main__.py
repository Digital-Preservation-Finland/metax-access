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
import metax_access

DEFAULT_CONFIG_FILES = ['/etc/metax.cfg',
                        '~/.local/etc/metax.cfg',
                        '~/.metax.cfg']


def post(metax_client, args):
    """Post file/dataset to Metax and print the result

    :param metax_client: `metax_access.Metax` instance
    :param args: Named tuple of parsed arguments from
                 :func:`__main__.parse_args()`

    """
    # Read metadata file
    with io.open(args.filepath, "rt") as open_file:
        data = json.load(open_file)

    if args.resource == 'dataset':
        _pprint(metax_client.post_dataset(data))
    elif args.resource == 'file':
        _pprint(metax_client.post_file(data))
    elif args.resource == 'contract':
        _pprint(metax_client.post_contract(data))


def get(metax_client, args):
    """Get file, dataset, or contract

    :param metax_client: `metax_access.Metax` instance
    :param args: Named tuple of parsed arguments from
                 :func:`__main__.parse_args()`
    """

    if args.resource == 'dataset':
        if args.identifier == 'template':
            with open("dataset_template.json", "wb") as _file:
                dataset_template = metax_client.get_dataset_template()
                _file.write(json.dumps(
                    dataset_template,
                    indent=4,
                    ensure_ascii=False
                ))
                print("Created dataset_template.json")
        else:
            _pprint(metax_client.get_dataset(args.identifier))

    elif args.resource == 'file':
        _pprint(metax_client.get_file(args.identifier))

    elif args.resource == 'contract':
        _pprint(metax_client.get_contract(args.identifier))


def delete(metax_client, args):
    """Delete file, dataset, or contract

    :param metax_client: `metax_access.Metax` instance
    :param args: Named tuple of parsed arguments from
                 :func:`__main__.parse_args()`
    """
    if args.resource == 'dataset':
        metax_client.delete_dataset(args.identifier)
    elif args.resource == 'file':
        metax_client.delete_file(args.identifier)
    elif args.resource == 'contract':
        metax_client.delete_contract(args.identifier)


def patch(metax_client, args):
    """Patch file, dataset, or contract

    :param metax_client: `metax_access.Metax` instance
    :param args: Named tuple of parsed arguments from
                 :func:`__main__.parse_args()`
    """
    with io.open(args.filepath, "rt") as open_file:
        data = json.load(open_file)

    if args.resource == 'dataset':
        _pprint(metax_client.patch_dataset(args.identifier, data))
    elif args.resource == 'file':
        _pprint(metax_client.patch_file(args.identifier, data))
    elif args.resource == 'contract':
        _pprint(metax_client.patch_contract(args.identifier, data))


def _pprint(dictionary):
    """Pretty print dictionary to stdout

    :param dictionary: dictionary
    :returns: ``None``
    """
    print(json.dumps(dictionary, indent=4, ensure_ascii=False))


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
    get_parser.add_argument('resource',
                            choices=('file', 'dataset', 'contract'),
                            help="Resource type")
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
