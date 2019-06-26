"""Commandline interface to Metax."""
import argparse
import configparser
import json
import os
import sys

import metax_access


def post(metax_client, args):
    """Post file/dataset"""
    # Read metadata file
    with open(args.filepath) as open_file:
        data = json.load(open_file)

    if args.resource == 'dataset':
        response = metax_client.post_dataset(data)
        print(json.dumps(response.json(), indent=4))
    elif args.resource == 'file':
        response = metax_client.post_file(data)
        print(json.dumps(response.json(), indent=4))
    elif args.resource == 'contract':
        response = metax_client.post_contract(data)
        print(json.dumps(response.json(), indent=4))


def get(metax_client, args):
    """Get file, dataset, or contract"""
    if args.resource == 'dataset':
        print(json.dumps(metax_client.get_dataset(args.identifier), indent=4))
    elif args.resource == 'file':
        print(json.dumps(metax_client.get_file(args.identifier), indent=4))
    elif args.resource == 'contract':
        print(json.dumps(metax_client.get_contract(args.identifier), indent=4))


def delete(metax_client, args):
    """Delete file, dataset, or contract"""
    if args.resource == 'dataset':
        response = metax_client.delete_dataset(args.identifier)
        print('Status:' + str(response.status_code))
    elif args.resource == 'file':
        response = metax_client.delete_file(args.identifier)
        print('Status:' + str(response.status_code))
    elif args.resource == 'contract':
        response = metax_client.delete_contract(args.identifier)
        print('Status:' + str(response.status_code))


def patch(metax_client, args):
    """Patch file, dataset, or contract"""
    with open(args.filepath) as open_file:
        data = json.load(open_file)
    if args.resource == 'dataset':
        print(
            json.dumps(
                metax_client.patch_dataset(args.identifier, data), indent=4
            )
        )
    if args.resource == 'file':
        print(
            json.dumps(
                metax_client.patch_file(args.identifier, data), indent=4
            )
        )


def main():
    """Parse arguments, init metax client, and run command."""
    # Parser
    parser = argparse.ArgumentParser(description="Manage metadata in Metax.")
    parser.add_argument('-c', '--config',
                        metavar='config',
                        help="Configuration file")
    parser.add_argument('--host',
                        metavar='host',
                        help="Metax hostname")
    parser.add_argument('-u', '--user',
                        metavar='user',
                        help="Metax username")
    parser.add_argument('-p', '--password',
                        metavar='password',
                        help="Metax password")
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

    # Parse arguments
    args = parser.parse_args()

    # Read config file if it was defined or the default config file exists
    config = os.path.expanduser(args.config or '~/.metax.cfg')
    if args.config and not os.path.isfile(config):
        sys.exit('Configuration file {} not found.'.format(args.config))
    if os.path.isfile(config):
        configuration = configparser.ConfigParser()
        configuration.read(os.path.expanduser(config))
        if args.host:
            configuration.set('metax', 'host', args.host)
        if args.user:
            configuration.set('metax', 'user', args.user)
        if args.password:
            configuration.set('metax', 'password', args.password)

    # Init metax client
    metax_client = metax_access.Metax(
        configuration.get('metax', 'host'),
        configuration.get('metax', 'user'),
        configuration.get('metax', 'password')
    )

    # Run command
    args.func(metax_client, args)


if __name__ == "__main__":
    main()
