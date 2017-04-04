"""Classes that repressent groups of AWS instances.
"""

from __future__ import print_function
import abc

from terminaltables import AsciiTable
import boto3

from instances import Ec2Instance, ElbInstance

class SearchAWSResources(object):
    """Retrieve and operate on a set of AWS resources.

    methods:
     - filter: Apply a search filter to the curent set of EC2 instances.
     - print_instances: Display the current set of AWS instances.
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
        """ Apply a filter to the AWS instances stored in instances.

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

        intermed_results = []
        for field, value in search_params.items():
            results = [inst for inst in self.instances if inst.match(field, value)]

            # Since we're effectively ANDing each set of results with each
            # iteration, any empty list forces the results to be empty
            if len(results) == 0:
                self.instances = []

            if len(intermed_results) == 0:
                intermed_results = results
            else:
                intermed_results = [inst for inst in results if inst in intermed_results]

        self.instances = intermed_results

    @staticmethod
    def _init_aws_session(account, region):
        return boto3.Session(profile_name=account, region_name=region)

    @classmethod
    def _get_printable_fields(cls, verbose):
        """Return a list of the printable fields.

        Args:
          - verbose: Include all fields or not. (boolean)
        """
        fields = []
        for field in cls._get_instance_fields():
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

    The public methods are available in the super class, SearchAWSResources.
    """

    @staticmethod
    def _get_instance_fields():
        """Return the instance_field strucuture from Ec2Instance.
        """
        return Ec2Instance.instance_fields

    def _get_instances(self):
        """ Return all ec2 instances in a list of Ec2Instance objects """
        all_instances = []
        for account in self.aws_accounts:
            for region in self.aws_regions:
                session = SearchAWSResources._init_aws_session(account, region)
                client = session.client('ec2', region_name=region)
                ec2_instances = client.describe_instances()['Reservations']
                all_instances += [Ec2Instance(instance['Instances'][0], account)
                                  for instance in ec2_instances if len(instance) != 0]
        return all_instances

    def _get_tag_printable_value(self, tag_data):
        """Return the printable value for a tag.

        Args:
          - tag_data: The tag to be printed. (string)
        """
        printable_tag_data = []
        for tags in tag_data:
            if tags['Key'] != 'Name':
                printable_tag_data.append("{}={}".format(tags['Key'], tags['Value']))
            printable_tag_data.sort()
        return ",".join(printable_tag_data)

    def _get_ip_printable_value(self, ip_data):
        """Return the printable value for an IP.

        Args:
          - ip_data: The IP to be printed. (string)
        """
        return "ssh://{}".format(ip_data) if ip_data else "n/a"

    def _get_state_printable_value(self, state_data):
        """Return the printable value for state.

        Args:
          - state_data: The tag to be printed. (string)
        """
        return state_data['Name']

    def _get_field_printable_value(self, instance, field_name):
        """Return a printable value for a given field.

        Args:
          - ec2_instance: The EC2 instance that is being printed. (Ec2Instance)
          - field_name: The field that is to be printed. (string)
        """
        field_format_functions = {
            'Tags': self._get_tag_printable_value,
            'PrivateIpAddress': self._get_ip_printable_value,
            'PublicIpAddress': self._get_ip_printable_value,
            'State': self._get_state_printable_value,
            }
        field_data = instance[field_name]
        try:
            printable_data = field_format_functions[field_name](field_data)
        except KeyError:
            printable_data = field_data

        return printable_data


class SearchElbInstances(SearchAWSResources):
    """Retrieve and operate on a set of ELB instances.

    The public methods are available in the super class, SearchAWSResources.
    """

    @staticmethod
    def _get_instance_fields():
        """Return the instance_field strucuture from ElbInstance.
        """
        return ElbInstance.instance_fields

    def _get_instances(self):
        """ Return all ELB instances in a list of ElbInstance objects """
        all_instances = []
        for account in self.aws_accounts:
            for region in self.aws_regions:
                session = SearchAWSResources._init_aws_session(account, region)
                client = session.client('elb', region_name=region)
                elb_instances = client.describe_load_balancers()
                all_instances += [ElbInstance(instance, account)
                                  for instance in elb_instances['LoadBalancerDescriptions']]
        return all_instances

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
        field_data = instance[field_name]
        try:
            printable_data = field_format_functions[field_name](field_data)
        except KeyError:
            printable_data = field_data

        return printable_data
