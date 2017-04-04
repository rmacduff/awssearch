#!/usr/bin/env python

""" A tool for searchiing for AWS resources across multiple accounts and 
regions.
"""

from __future__ import print_function
import argparse
import os
import sys

from botocore import exceptions
import yaml

from search import SearchEc2Instances, SearchElbInstances
from version import __version__

def parse_commandline_args():
    """Parse commandline arguments.
    """

    # Top-level options
    parser = argparse.ArgumentParser(description='Query EC2 instances')
    parser.add_argument('-a', '--account',
                        dest='aws_account',
                        default='all')
    parser.add_argument('-r', '--region',
                        dest='aws_regions',
                        default='all')
    parser.add_argument('-v', '--verbose',
                        action='store_true',)
    parser.add_argument('--version',
                        action='version', version='%(prog)s ' + __version__)

    subparsers = parser.add_subparsers(help='AWS resource to search for', dest='resource')

    # ec2 sub-command
    parser_ec2 = subparsers.add_parser('ec2', help='search for ec2 instances')
    parser_ec2.add_argument('-i', '--instance-id',
                            dest='instance_id')
    parser_ec2.add_argument('--ip',
                            dest='instance_ip')
    parser_ec2.add_argument('-n', '--name',
                            dest='instance_name',)
    parser_ec2.add_argument('-s', '--state',
                            dest='instance_state',
                            default='running',
                            choices=('running', 'stopped', 'terminated'))
    parser_ec2.add_argument('-t', '--tags',
                            #action='append',
                            dest='instance_tags')

    # elb sub-command
    parser_ec2 = subparsers.add_parser('elb', help='search for elb instances')
    parser_ec2.add_argument('--dns',
                            dest='instance_dns_name')
    parser_ec2.add_argument('-n', '--name',
                            dest='instance_name',)

    return parser.parse_args()

def parse_config():
    """Return a dict representing the configuration

    """
    try:
        with open(os.path.expanduser('~/.aws-search.yml')) as config_fh:
            return yaml.load(config_fh)
    except IOError:
        raise IOError("please configure ~/.aws-search.yml")

def main():
    """Main point of entry.
    """

    conf = parse_config()
    args = parse_commandline_args()

    if args.aws_account == 'all':
        aws_accounts = conf['aws_accounts']
    else:
        aws_accounts = [args.aws_account]

    if args.aws_regions == 'all':
        aws_regions = conf['aws_regions']
    else:
        aws_regions = [args.aws_regions]

    search_filter = {}

    if args.resource == 'ec2':
        aws_resource_type = SearchEc2Instances
        if args.instance_name:
            search_filter.update({'instance_name': args.instance_name})
        if args.instance_id:
            search_filter.update({'instance_id': args.instance_id})
        if args.instance_tags:
            search_filter.update({'instance_tags': args.instance_tags})
        if args.instance_ip:
            search_filter.update({'instance_ip': args.instance_ip})
        # State defaults to 'running' so always apply this filter
        search_filter.update({'instance_state': args.instance_state})

    elif args.resource == 'elb':
        aws_resource_type = SearchElbInstances
        if args.instance_name:
            search_filter.update({'instance_name': args.instance_name})
        if args.instance_dns_name:
            search_filter.update({'instance_dns_name': args.instance_dns_name})
    else:
        print("unsupported AWS resource: {}".format(args.resource))

    try:
        instances = aws_resource_type(aws_accounts, aws_regions)
    except (exceptions.ProfileNotFound, exceptions.NoCredentialsError):
        print(("There was an issue matching the accounts in "
               "~/.awssearch.yml with the account profiles in "
               "~/.aws/credentials`. "
               "\nSee the README for more details."))
        sys.exit(1)
    instances.filter(search_filter)
    instances.print_instances(
        verbose=args.verbose,
        )

if __name__ == '__main__':
    main()
