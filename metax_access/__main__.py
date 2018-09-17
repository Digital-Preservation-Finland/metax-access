"""Commandline interface to Metax."""
import json
import argparse
import metax_access

def post(metax_client, args):
    """Post file/dataset"""
    # Read metadata file
    with open(args.filepath) as open_file:
        data = json.load(open_file)

    if args.resource == 'dataset':
        response = metax_client.post_dataset(data)
        print json.dumps(response.json(), indent=4)
    elif args.resource == 'file':
        response = metax_client.post_file(data)
        print json.dumps(response.json(), indent=4)

def get(metax_client, args):
    """Get file/dataset"""
    if args.resource == 'dataset':
        print json.dumps(metax_client.get_dataset(args.identifier), indent=4)
    elif args.resource == 'file':
        print json.dumps(metax_client.get_file(args.identifier), indent=4)

def delete(metax_client, args):
    """Delete file/dataset"""
    if args.resource == 'dataset':
        response = metax_client.delete_dataset(args.identifier)
        print json.dumps(response.json(), indent=4)
    elif args.resource == 'file':
        response = metax_client.delete_file(args.identifier)
        print json.dumps(response.json(), indent=4)


def main():
    """Parse arguments, init metax client, and run command."""
    # Parser
    parser = argparse.ArgumentParser(description="Manage metadata in Metax.")
    parser.add_argument('--host', metavar='host',
                        help="Metax hostname")
    parser.add_argument('-u', '--user', metavar='user',
                        help="Metax username")
    parser.add_argument('-p', '--password', metavar='password',
                        help="Metax password")
    subparsers = parser.add_subparsers(title='command')

    # Post command parser
    post_parser = subparsers.add_parser('post')
    post_parser.add_argument('resource',
                             choices=('file', 'dataset', 'contract'),
                             help="Resource type")
    post_parser.add_argument('filepath', help="Path to metadata file")
    post_parser.set_defaults(func=post)

    # Get command parser
    get_parser = subparsers.add_parser('get')
    get_parser.add_argument('resource',
                            choices=('file', 'dataset', 'contract'),
                            help="Resource type")
    get_parser.add_argument('identifier', help="Resource identifier")
    get_parser.set_defaults(func=get)

    # Delete command parser
    delete_parser = subparsers.add_parser('delete')
    delete_parser.add_argument('resource',
                               choices=('file', 'dataset', 'contract'),
                               help="Resource type")
    delete_parser.add_argument('identifier', help="Resource identifier")
    delete_parser.set_defaults(func=delete)

    # Parse arguments
    args = parser.parse_args()

    # Init metax client
    metax_client = metax_access.Metax(args.host, args.user, args.password)

    # Run command
    args.func(metax_client, args)


main()
