"""Classes that represent individual AWS resources
"""

from __future__ import print_function
import abc

class AWSInstance(object):
    """Represent a single AWS resource instance.

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

    def __getitem__(self, item):
        try:
            return self.instance[item]
        except KeyError:
            return []

    @abc.abstractmethod
    def match(self, attribute, value):
        pass


class Ec2Instance(AWSInstance):
    """Represent a single EC2 Instance.

    Gets passed in a boto3 EC2 resource from a session.

    https://boto3.readthedocs.io/en/latest/guide/resources.html#resources
    https://boto3.readthedocs.io/en/latest/guide/session.html

    """

    instance_fields = [
            {
                'name': 'instance_name',
                'printable_name': 'Name',
                'verbose_display': False,
            },
            {
                'name': 'InstanceId',
                'printable_name': "Instance ID",
                'verbose_display': False,
            },
            {
                'name': 'InstanceType',
                'printable_name': "Type",
                'verbose_display': True,
            },
            {
                'name': 'State',
                'printable_name': "State",
                'verbose_display': True,
            },
            {
                'name': 'instance_placement',
                'printable_name': "Placement",
                'verbose_display': False,
            },
            {
                'name': 'PrivateIpAddress',
                'printable_name': "Private IP",
                'verbose_display': False,
            },
            {
                'name': 'PublicIpAddress',
                'printable_name': "Public IP",
                'verbose_display': False,
            },
            {
                'name': 'Tags',
                'printable_name': "Tags",
                'verbose_display': False,
            },
            {
                'name': 'LaunchTime',
                'printable_name': "Launch Time",
                'verbose_display': True,
            },
            {
                'name': 'aws_account',
                'printable_name': "Account",
                'verbose_display': False,
            },
    ]

    def __getitem__(self, item):
        if item == 'aws_account':
            return self.aws_account
        elif item == 'Name' or item == 'instance_name':
            return self._get_name()
        elif item == 'instance_placement':
            return super(Ec2Instance, self).__getitem__('Placement')['AvailabilityZone']
        else:
            return super(Ec2Instance, self).__getitem__(item)

    def _get_name(self):
        for tag in self['Tags']:
            if tag['Key'] == 'Name':
                return tag['Value']

    def match(self, attribute, value):
        if attribute == 'instance_tags':
            for tags in self['Tags']:
                if tags['Key'] != 'Name':
                    tag_value = "{}={}".format(tags['Key'], tags['Value'])
                    if value.lower() in tag_value.lower():
                        return True
        elif attribute == 'instance_ip':
            public_ip = self['PublicIpAddress']
            private_ip = self['PrivateIpAddress']
            if (private_ip and value in private_ip) or \
                (public_ip  and value in public_ip):
                return True
        elif attribute == 'instance_state':
            running_state = self['State']['Name']
            if value == running_state:
                return True
        elif attribute == 'instance_name':
            name = self['Name']
            if name and value.lower() in name.lower():
                return True
        else:
            field_value = self[attribute]
            try:
                if value.lower() in field_value.lower():
                    return True
            except AttributeError:
                return False

    @staticmethod
    def get_printable_fields(verbose):
        """Return a list of the printable fields.

        Args:
          - verbose: Include all fields or not. (boolean)
        """
        fields = []
        for field in Ec2Instance.instance_fields:
            field_name = field['name']
            field_printable_name = field['printable_name']
            field_verbose = field['verbose_display']
            if verbose and field_verbose:
                fields.append((field_name, field_printable_name))
            elif not field_verbose:
                fields.append((field_name, field_printable_name))
        return fields

    @staticmethod
    def _get_tag_printable_value(tag_data):
        """Return the printable value for a tag.

        Args:
          - tag_data: The tag to be printed. (string)
        """
        printable_tag_data = []
        for tags in tag_data:
            if tags['Key'] != 'Name':
                printable_tag_data.append("{}={}".format(tags['Key'], tags['Value']))
            printable_tag_data.sort()
        return "; ".join(printable_tag_data)

    @staticmethod
    def _get_ip_printable_value(ip_data):
        """Return the printable value for an IP.

        Args:
          - ip_data: The IP to be printed. (string)
        """
        return "ssh://{}".format(ip_data) if ip_data else "n/a"

    @staticmethod
    def _get_state_printable_value(state_data):
        """Return the printable value for state.

        Args:
          - state_data: The tag to be printed. (string)
        """
        return state_data['Name']

    @staticmethod
    def get_field_printable_value(instance, field_name):
        """Return a printable value for a given field.

        Args:
          - ec2_instance: The EC2 instance that is being printed. (Ec2Instance)
          - field_name: The field that is to be printed. (string)
        """
        field_format_functions = {
            'Tags': Ec2Instance._get_tag_printable_value,
            'PrivateIpAddress': Ec2Instance._get_ip_printable_value,
            'PublicIpAddress': Ec2Instance._get_ip_printable_value,
            'State': Ec2Instance._get_state_printable_value,
            }
        field_data = instance[field_name]
        try:
            printable_data = field_format_functions[field_name](field_data)
        except KeyError:
            printable_data = field_data

        return printable_data


class ElbInstance(AWSInstance):
    """Represent a single ELB Instance.

    Gets passed in an instance in the form of a 'LoadBalancerDescriptions'
    dictionary as from an elb client session call to `describe_load_balancers`.

    E.g.

    session = boto3.Session(profile_name=account, region_name=region)
    client = session.client('elb', region_name=region)
    elb_instances = client.describe_load_balancers()
    all_instances += [ElbInstance(instance, account)
                      for instance in elb_instances['LoadBalancerDescriptions']]

    """

    instance_fields = [
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
                'printable_name': "EC2 Instances",
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

    def __getitem__(self, item):
        if item == 'aws_account':
            return self.aws_account
        elif item == 'Name' or item == 'instance_name':
            return self._get_name()
        elif item == 'instance_placement':
            return super(ElbInstance, self).__getitem__('Placement')['AvailabilityZone']
        else:
            return super(ElbInstance, self).__getitem__(item)

    def _get_name(self):
        return self['LoadBalancerName']

    def match(self, attribute, value):
        if attribute == 'instance_dns_name':
            real_attribute = 'DNSName'
        else:
            real_attribute = attribute
        field_value = self[real_attribute]
        if value.lower() in field_value.lower():
            return True

    #@classmethod
    @staticmethod
    def get_printable_fields(verbose):
        """Return a list of the printable fields.

        Args:
          - verbose: Include all fields or not. (boolean)
        """
        fields = []
        for field in ElbInstance.instance_fields:
            field_name = field['name']
            field_printable_name = field['printable_name']
            field_verbose = field['verbose_display']
            if verbose and field_verbose:
                fields.append((field_name, field_printable_name))
            elif not field_verbose:
                fields.append((field_name, field_printable_name))
        return fields

    @staticmethod
    def _get_instances_printable_value(instances):
        """Return the printable value ths set of EC2 instances for .

        Args:
          - tag_data: The tag to be printed. (string)
        """
        printable_instance_data = []
        for instance in instances:
            printable_instance_data.append("{}".format(instance['InstanceId']))
        return ", ".join(printable_instance_data)

    @staticmethod
    def get_field_printable_value(instance, field_name):
        """Return a printable value for a given field.

        Args:
          - instance: The AWS resource instance that is being printed. (AwsInstance)
          - field_name: The field that is to be printed. (string)
        """
        field_format_functions = {}
        field_format_functions = {
            'Instances': ElbInstance._get_instances_printable_value,
            }
        field_data = instance[field_name]
        try:
            printable_data = field_format_functions[field_name](field_data)
        except KeyError:
            printable_data = field_data

        return printable_data
