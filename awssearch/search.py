"""Classes that repressent groups of AWS instances.
"""

from __future__ import print_function
import abc
import json

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
        self.instances = self._get_all_instances()

    @staticmethod
    def _init_aws_session(account, region):
        return boto3.Session(profile_name=account, region_name=region)

    @abc.abstractmethod
    def _get_instances(account, region):
        """ Return instances of a given type in the given account and region"""
        pass

    def _get_all_instances(self):
        """ Return all instances of a given tyoe in a list of instance objects """
        all_instances = [self._get_instances(account, region)
                         for account in self.aws_accounts
                         for region in self.aws_regions]
        # all_instances is a list of lists so we need to break those out into one list
        return [instance for inst_list in all_instances for instance in inst_list]

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


    def _print_long_format(self, verbose):
        """Print instances in long format.

        To be implemented
        """
        raise NotImplementedError('This method has not been implemented.')

    @abc.abstractmethod
    def _get_printable_fields(verbose):
        pass

    @abc.abstractmethod
    def _get_field_printable_value(instance, name, print_format):
        pass

    def _get_instance_data(self, instance, verbose, print_format):
        return [self._get_field_printable_value(instance, attribute, print_format) for attribute in self._get_attributes(verbose)]

    def _print_json_format(self, verbose):
        """Print instanecs in json format.

        Args:
          - verbose: Print extra details or not. Boolean value.
        """
        attribute_names = list(self._get_printable_attribute_names(verbose))
        output = []
        for instance in self.instances:
            output.append(dict(zip(attribute_names, self._get_instance_data(instance, verbose, print_format='json'))))
        json_output = { 'instances': output }
        print(json.dumps(json_output, indent=4))



    def _print_table_format(self, verbose):
        """Print ec2info in a table.

        Print the information contained in ec2info in a tabular format.

        Args:
          - verbose: Print extra details or not. Boolean value.
        """
        # Add the headers to the table
        table_data = [list(self._get_printable_attribute_names(verbose))]
        # Gather the data for each instance
        [table_data.append(self._get_instance_data(instance, verbose, print_format='table')) for instance in self.instances]
        table = AsciiTable(table_data)
        table.inner_row_border = True
        print(table.table)

    def print_instances(self, print_format='table', verbose=False):
        """Print instances in format specified by format

        Args:
        - print_format: How each entry should be printed. Either `table` or
        `json` format. Defaults to 'table'.
        - verbose: Print extra details or not. Defaults to 'False'.
        """
        print_functions = {
                'table': self._print_table_format, 
                'json': self._print_json_format, 
                }
        print_functions[print_format](verbose)


class SearchEc2Instances(SearchAWSResources):
    """Retrieve and operate on a set of EC2 instances.

    The public methods are available in the super class, SearchAWSResources.
    """

    @staticmethod
    def _get_instances(account, region):
         session = SearchAWSResources._init_aws_session(account, region)
         client = session.client('ec2', region_name=region)
         return  [Ec2Instance(instance, account)
                  for reservations in client.describe_instances()['Reservations']
                  for instance in reservations['Instances']]

    @staticmethod
    def _get_attributes(verbose):
        return Ec2Instance.get_attributes(verbose)

    @staticmethod
    def _get_printable_attribute_names(verbose):
        return Ec2Instance.get_printable_attribute_names(verbose)

    @staticmethod
    def _get_field_printable_value(instance, name, print_format):
        return Ec2Instance.get_field_printable_value(instance, name, print_format)


class SearchElbInstances(SearchAWSResources):
    """Retrieve and operate on a set of ELB instances.

    The public methods are available in the super class, SearchAWSResources.
    """

    @staticmethod
    def _get_instances(account, region):
         session = SearchAWSResources._init_aws_session(account, region)
         client = session.client('elb', region_name=region)
         return   [ElbInstance(instance, account)
                   for instance in client.describe_load_balancers()['LoadBalancerDescriptions']]

    @staticmethod
    def _get_attributes(verbose):
        return ElbInstance.get_attributes(verbose)

    @staticmethod
    def _get_printable_attribute_names(verbose):
        return ElbInstance.get_printable_attribute_names(verbose)

    @staticmethod
    def _get_field_printable_value(instance, name, print_format):
        return ElbInstance.get_field_printable_value(instance, name, print_format)


