"""
A tool for retrieving basic information from the running EC2 instances.
"""

from __future__ import print_function
from collections import namedtuple
import abc
import argparse

from terminaltables import AsciiTable
import boto3

class AWSInstance(object):
    """Represent a single AWS resource instance.

    Gets passed in a boto3 EC2 resource from a session.

    https://boto3.readthedocs.io/en/latest/guide/resources.html#resources
    https://boto3.readthedocs.io/en/latest/guide/session.html

    """

    def __init__(self, instance, aws_account):
        self.instance = instance
        self.aws_account = aws_account

    def __repr__(self):
        output = []
        for attr in dir(self.instance):
            if not attr.startswith('__'):
                output.append("{}: {}".format(attr, getattr(self.instance, attr)))
        return "\n".join(output)

    @abc.abstractmethod
    def __getattr__(self, attribute):
        pass

    def _get_attribute(self, attribute):
        if isinstance(self.instance, dict):
            return self.instance.__getitem__(attribute)
        else:
            return self.instance.__getattribute__(attribute)

    @abc.abstractmethod
    def match(self, attribute, value):
        pass


class Ec2Instance(AWSInstance):
    """Represent a single EC2 Instance.

    Gets passed in a boto3 EC2 resource from a session.

    https://boto3.readthedocs.io/en/latest/guide/resources.html#resources
    https://boto3.readthedocs.io/en/latest/guide/session.html

    """

    def __getattr__(self, attribute):
        if attribute == 'aws_account':
            return self.aws_account
        elif attribute == 'instance_name':
            return self._get_name()
        elif attribute == 'instance_placement':
            return self._get_attribute('placement')['AvailabilityZone']
        else:
            return self._get_attribute(attribute)

    def _get_name(self):
        for tag in self.instance.tags:
            if tag['Key'] == 'Name':
                return tag['Value']

    def match(self, attribute, value):
        if attribute == 'instance_tags':
            for tags in self._get_attribute('tags'):
                if tags['Key'] != 'Name':
                    tag_value = "{}:{}".format(tags['Key'], tags['Value'])
                    if value.lower() in tag_value.lower():
                        return True
        elif attribute == 'instance_ip':
            public_ip = self.__getattr__('public_ip_address')
            private_ip = self.__getattr__('private_ip_address')
            if (private_ip and value in private_ip) or \
                (public_ip  and value in public_ip):
                return True
        else:
            field_value = self.__getattr__(attribute)
            if value.lower() in field_value.lower():
                return True


class ElbInstance(AWSInstance):
    """Represent a single ELB Instance.

    Gets passed in a boto3 EC2 resource from a session.

    https://boto3.readthedocs.io/en/latest/guide/resources.html#resources
    https://boto3.readthedocs.io/en/latest/guide/session.html

    """

    def __getattr__(self, attribute):
        if attribute == 'aws_account':
            return self.aws_account
        elif attribute == 'instance_name':
            return self._get_name()
        elif attribute == 'instance_placement':
            return self._get_attribute('placement')['AvailabilityZone']
        else:
            return self._get_attribute(attribute)

    def _get_name(self):
        return self._get_attribute('LoadBalancerName')

    def match(self, attribute, value):
        if attribute == 'instance_dns_name':
            real_attribute = 'DNSName'
        else:
            real_attribute = attribute
        field_value = self.__getattr__(real_attribute)
        if value.lower() in field_value.lower():
            return True


class SearchAWSResources(object):
    """Retrieve and operate on a set of AWS resources.

    methods:
     - filter: Apply a search filter to the curent set of EC2 instances.
     - print_ec2_data: Display the current set of EC2 instances.
    """

    def __init__(self, aws_accounts, aws_regions):
        """Contructor for Ec2Instances class.

        Args:
          - aws_accounts: A list of the AWS accounts to be queried. This name
          must match the name used in your local `~/.aws/confg`.
          - aws_regions: A list of AWS regions to search through.
        """
        self.aws_regions = aws_regions
        self.aws_accounts = aws_accounts
        self.instances = self._get_instances()

    @abc.abstractmethod
    def _get_instances(self):
        """ Return all instances of a given type"""
        pass

    def filter(self, search_params):
        """ Apply a filter to EC2 instances stored in instances. search_params is a dictionary

        Args:
          - search_params: A dictionary containing where each key-value pair
            is a field and its respective value to match on. Example:
              {
               "instance_name": "web",
               "instance_tags": "env:prd",
              }
        """
        if len(search_params) == 0:
            return

        final_results = []
        for field, value in search_params.items():
            results = [inst for inst in self.instances if inst.match(field, value)]

            if len(final_results) != 0:
                # This is not the first set of results
                final_results_new = []
                for instance in final_results:
                    if instance in results:
                        final_results_new.append(instance)
                final_results = final_results_new
            else:
                # This is the first set of search results
                final_results = results
        self.instances = final_results

    @classmethod
    def _get_printable_fields(cls, verbose):
        """Return a list of the printable fields.

        Args:
          - verbose: Include all fields or not. (boolean)
        """
        fields = []
        for field in cls.display_fields:
            field_name = field['name']
            field_printable_name = field['printable_name']
            field_verbose = field['verbose_display']
            if verbose and field_verbose:
                fields.append((field_name, field_printable_name))
            elif not field_verbose:
                fields.append((field_name, field_printable_name))
        return fields

    def _print_long_format(self, verbose):
        """Print instances in long format.

        To be implemented
        """
        raise NotImplementedError('This method has not been implemented.')

    def _print_table_format(self, verbose):
        """Print ec2info in a table.

        Print the information contained in ec2info in a tabular format.

        Args:
          - verbose: Print extra details or not. Boolean value.
        """
        table_data = []
        printable_fields = self._get_printable_fields(verbose)
        print(printable_fields)
        table_data.append([name_tuple[1] for name_tuple in  printable_fields])
        for instance in self.instances:
            instance_data = []
            for name, _ in printable_fields:
                instance_data.append(self._get_field_printable_value(instance, name))
            table_data.append(instance_data)
        table = AsciiTable(table_data)
        print(table.table)

    def print_instances(self, print_format='table', verbose=False):
        """Print ec2data in format specified by format

        Args:
        - print_format: How each entry should be printed. Either `table` or
        `long` format. Defaults to 'table'.
        - verbose: Print extra details or not. Defaults to 'False'.
        """
        print_functions = {'table': self._print_table_format, 'long': self._print_long_format}
        print_functions[print_format](verbose)


class SearchEc2Instances(SearchAWSResources):
    """Retrieve and operate on a set of EC2 instances.

    methods:
     - filter: Apply a search filter to the curent set of EC2 instances.
     - print_ec2_data: Display the current set of EC2 instances.
    """

    display_fields = [
            {
                'name': 'instance_name',
                'printable_name': 'Name',
                'verbose_display': False,
            },
            {
                'name': 'instance_id',
                'printable_name': "Instance ID",
                'verbose_display': False,
            },
            {
                'name': 'instance_type',
                'printable_name': "Type",
                'verbose_display': True,
            },
            {
                'name': 'state',
                'printable_name': "State",
                'verbose_display': True,
            },
            {
                'name': 'instance_placement',
                'printable_name': "Placement",
                'verbose_display': False,
            },
            {
                'name': 'private_ip_address',
                'printable_name': "Private IP",
                'verbose_display': False,
            },
            {
                'name': 'public_ip_address',
                'printable_name': "Public IP",
                'verbose_display': False,
            },
            {
                'name': 'tags',
                'printable_name': "Tags",
                'verbose_display': False,
            },
            {
                'name': 'launch_time',
                'printable_name': "Launce Time",
                'verbose_display': True,
            },
            {
                'name': 'aws_account',
                'printable_name': "Account",
                'verbose_display': False,
            },
    ]
 
    def _get_instances(self):
        """ Return all ec2 instances in a list of Ec2Instance objects """
        all_instances = []
        for account in self.aws_accounts:
            for region in self.aws_regions:
                session = boto3.Session(profile_name=account, region_name=region)
                ec2 = session.resource('ec2')

                ec2_state = 'running'
                ec2_filter = [
                    {
                        'Name': 'instance-state-name',
                        'Values': [ec2_state],
                    },
                    {
                        'Name': 'tag:Name',
                        'Values': ['*'],
                    }]

                running_instances = ec2.instances.filter(Filters=ec2_filter)
                all_instances += [Ec2Instance(instance, account) for instance in running_instances]
        return all_instances

    def _get_tag_printable_value(self, tag_data):
        """Return the printable value for a tag.

        Args:
          - tag_data: The tag to be printed. (string)
        """
        printable_tag_data = []
        for tags in tag_data:
            if tags['Key'] != 'Name':
                printable_tag_data.append("{}:{}".format(tags['Key'], tags['Value']))
            printable_tag_data.sort()
        return ", ".join(printable_tag_data)

    def _get_ip_printable_value(self, ip_data):
        """Return the printable value for an IP.

        Args:
          - ip_data: The IP to be printed. (string)
        """
        return "ssh://{}".format(ip_data) if ip_data else "n/a"

    def _get_field_printable_value(self, instance, field_name):
        """Return a printable value for a given field.

        Args:
          - ec2_instance: The EC2 instance that is being printed. (Ec2Instance)
          - field_name: The field that is to be printed. (string)
        """
        field_format_functions = {
            'tags': self._get_tag_printable_value,
            'private_ip_address': self._get_ip_printable_value,
            'public_ip_address': self._get_ip_printable_value,
            }
        field_data = getattr(instance, field_name)
        try:
            printable_data = field_format_functions[field_name](field_data)
        except KeyError:
            printable_data = field_data

        return printable_data


class SearchElbInstances(SearchAWSResources):
    """Retrieve and operate on a set of ELB instances.

    methods:
     - filter: Apply a search filter to the curent set of EC2 instances.
     - print_ec2_data: Display the current set of EC2 instances.
    """

    display_fields = [
            {
                'name': 'instance_name',
                'printable_name': 'Name',
                'verbose_display': False,
            },
            {
                'name': 'DNSName',
                'printable_name': "DNS Name",
                'verbose_display': False,
            },
            {
                'name': 'Instances',
                'printable_name': "Instances",
                'verbose_display': False,
            },
            {
                'name': 'CreatedTime',
                'printable_name': "Created Time",
                'verbose_display': True,
            },
            {
                'name': 'aws_account',
                'printable_name': "Account",
                'verbose_display': False,
            },
    ]

    def _get_instances(self):
        """ Return all ELB instances in a list of ElbInstance objects """
        all_instances = []
        for account in self.aws_accounts:
            for region in self.aws_regions:
                session = boto3.Session(profile_name=account, region_name=region)
                client = session.client('elb', region_name=region)
                elb_instances = client.describe_load_balancers()
                all_instances += [ElbInstance(instance, account)
                                  for instance in elb_instances['LoadBalancerDescriptions']]
        return all_instances


    ###########################################################################
    # Print related methods
    ###########################################################################
    
    def _get_instances_printable_value(self, instances):
        """Return the printable value for a tag.

        Args:
          - tag_data: The tag to be printed. (string)
        """
        printable_instance_data = []
        for instance in instances:
            printable_instance_data.append("{}".format(instance['InstanceId']))
        return ", ".join(printable_instance_data)

    def _get_field_printable_value(self, instance, field_name):
        """Return a printable value for a given field.

        Args:
          - instance: The AWS resource instance that is being printed. (AwsInstance)
          - field_name: The field that is to be printed. (string)
        """
        field_format_functions = {}
        field_format_functions = {
            'Instances': self._get_instances_printable_value,
            }
        field_data = getattr(instance, field_name)
        try:
            printable_data = field_format_functions[field_name](field_data)
        except KeyError:
            printable_data = field_data

        return printable_data

def parse_commandline_args():
    """Parse commandline arguments.
    """

    # Top-level options
    parser = argparse.ArgumentParser(description='Query EC2 instances')
    parser.add_argument('-a', '--account',
                        dest='aws_account',
                        default='all')
    parser.add_argument('-v', '--verbose',
                        action='store_true',)

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
                            dest='ec2_instance_state',
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

def main():
    """Main point of entry.
    """
    # move these variables into a config file
    AWS_ACCOUNTS = ['mctprod', 'mctqa']
    AWS_REGIONS = ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2']

    args = parse_commandline_args()

    if args.aws_account == 'all':
        aws_accounts = AWS_ACCOUNTS
    else:
        aws_accounts = []
        aws_accounts.append(args.aws_account)

    search_filter = {}

    if args.resource == 'ec2':
        instances = SearchEc2Instances(aws_accounts, AWS_REGIONS)

        if args.instance_name:
            search_filter.update({'instance_name': args.instance_name})
        if args.instance_id:
            search_filter.update({'instance_id': args.instance_id})
        if args.instance_tags:
            search_filter.update({'instance_tags': args.instance_tags})
        if args.instance_ip:
            search_filter.update({'instance_ip': args.instance_ip})

    elif args.resource == 'elb':
        instances = SearchElbInstances(aws_accounts, AWS_REGIONS)

        if args.instance_name:
            search_filter.update({'instance_name': args.instance_name})
        if args.instance_dns_name:
            search_filter.update({'instance_dns_name': args.instance_dns_name})
    else:
        print("unsupported AWS resource: {}".format(args.resource))

    instances.filter(search_filter)
    instances.print_instances(
        verbose=args.verbose,
        )

if __name__ == '__main__':
    main()
