"""Classes that represent individual AWS resources
"""

from __future__ import print_function
from datetime import date, datetime
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

    @classmethod
    def _get_printable_fields(cls, verbose):
        """Return a list of the printable fields.

        Args:
          - verbose: Include all fields or not. (boolean)
        """
        fields = []
        for field in cls.instance_fields:
            field_name = field['name']
            field_printable_name = field['printable_name']
            field_verbose = field['verbose_display']
            if verbose and field_verbose:
                fields.append((field_name, field_printable_name))
            elif not field_verbose:
                fields.append((field_name, field_printable_name))
        return fields

    @classmethod
    def get_printable_attribute_names(cls, verbose):
        return [name_tuple[1] for name_tuple in cls._get_printable_fields(verbose)]

    @classmethod
    def get_attributes(cls, verbose):
        return [name_tuple[0] for name_tuple in cls._get_printable_fields(verbose)]

    @staticmethod
    def json_serial(obj):
        """JSON serializer for objects not serializable by default json code

        Source: https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable
        """

        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError ("Type %s not serializable" % type(obj))

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
                'name': 'SecurityGroups',
                'printable_name': "Security Groups",
                'verbose_display': True,
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

    # Static helper methods
    @staticmethod
    def _sg_format(sg_name, sg_id):
        return "{} - {}".format(sg_name, sg_id)

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

    def _match_tags(self, match_tags):
        """Returns true if each of the tags in match_tags matches a tag in self

        Args:
          - match_tags: A list of strings to match against

        Returns:
          - True if each tag in match_tags matches a tag in self.
        """
        instance_tags = ["{}={}".format(tag['Key'].lower(), tag['Value'].lower()) for tag in self['Tags'] if tag['Key'] != 'Name']
        matches = {mtag:itag for mtag in match_tags for itag in instance_tags if mtag.lower() in itag}
        if len(matches) == len(match_tags):
            return True

    def _match_securitygroups(self, match_sgs):
        """Returns true if each of the strings in match_sgs matches a security group in self

        Args:
          - match_sgs: A list of strings representing partial security group names or IDs to match against

        Returns:
          - True if each string in match_sgs matches a security group in self.
        """
        sg_tags = [self._sg_format(sg['GroupName'].lower(), sg['GroupId'].lower()) for sg in self['SecurityGroups']]
        matches = {msg:isg for msg in match_sgs for isg in sg_tags if msg.lower() in isg}
        if len(matches) == len(match_sgs):
            return True

    def _match_ip(self, match_ip):
        """Returns true if match_ip matches either the private or public IP of self

        Args:
          - match_ip: A string representing a partial or full IP address

        Returns:
          - True if match_ip partially matches either the public or private IP of self
        """
        public_ip = self['PublicIpAddress']
        private_ip = self['PrivateIpAddress']
        if (private_ip and match_ip in private_ip) or \
            (public_ip  and match_ip in public_ip):
            return True

    def _match_state(self, match_state):
        """Returns true if match_state matches the running state of self

        Args:
          - match_state: A string representing the state of an EC2 instance

        Returns:
          - True if match_state matches the running state of self
        """
        running_state = self['State']['Name']
        if match_state == running_state:
            return True

    def _match_name(self, match_name):
        """Returns true if match_name matches the name of self

        Args:
          - match_name: A string representing the name of an EC2 instance

        Returns:
          - True if match_name partially (or completely)  matches the name of self
        """
        name = self['Name']
        if name and match_name.lower() in name.lower():
            return True

    def _match_id(self, match_instance_id):
        """Returns true if match_instance_id matches the instance ID of self

        Args:
          - match_instance_id: A string representing a full or partial instance ID of an EC2 instance

        Returns:
          - True if match_instance_id partially (or completely)  matches the instance ID of self
        """
        name = self['InstanceId']
        if name and match_instance_id.lower() in name.lower():
            return True

    def _match_generic(self, value, attribute):
        """Returns true if value matches the attribute of self

        Args:
          - value: A string to match against the attribute of an EC2 instance
          - attribute: A string representing an attribute of an EC2 instance

        Returns:
          - True if value partially (or completely) matches the attribute of self
        """
        field_value = self[attribute]
        try:
            if value.lower() in field_value.lower():
                return True
        except AttributeError:
            return False

    def match(self, attribute, value):
        """Returns true if value matches the attribute of self

        Args:
          - value: A string to match against the attribute of an EC2 instance
          - attribute: A string representing an attribute of an EC2 instance

        Returns:
          - True if value partially (or completely) matches the attribute of self
        """
        match_methods = {
                'instance_tags': self._match_tags,
                'instance_ip': self._match_ip,
                'instance_state': self._match_state,
                'instance_name': self._match_name,
                'instance_id': self._match_id,
                'instance_sg': self._match_securitygroups,
                }
        try:
            return match_methods[attribute](value)
        except KeyError:
            return self._match_generic(value, attribute)

    @staticmethod
    def _get_tag_printable_value(tag_data, print_format):
        """Return the printable value for a tag.

        Args:
          - tag_data: The tag to be printed. (string)
        """
        print_formats = {
                'table': "\n".join(["{}={}".format(tags['Key'], tags['Value'])
                                   for tags in tag_data if tags['Key'] != 'None']),
                'json': ",".join(["{}={}".format(tags['Key'], tags['Value'])
                                   for tags in tag_data if tags['Key'] != 'None']),
                }
        return print_formats[print_format]

    @staticmethod
    def _get_ip_printable_value(ip_data, print_format):
        """Return the printable value for an IP.

        Args:
          - ip_data: The IP to be printed. (string)
        """
        print_formats = {
                'table': "ssh://{}".format(ip_data) if ip_data else "n/a",
                'json': "{}".format(ip_data) if ip_data else "n/a",
                }
        return print_formats[print_format]

    @staticmethod
    def _get_state_printable_value(state_data, print_format):
        """Return the printable value for state.

        Args:
          - state_data: The tag to be printed. (string)
        """
        return state_data['Name']

    @staticmethod
    def _get_securitygroups_printable_value(sg_data, print_format):
        """Return the printable value for security groups.

        Args:
          - sg_data: The security groups to be printed. (string)
        """
        print_formats = {
                'table': "\n".join(Ec2Instance._sg_format(sg['GroupName'], sg['GroupId']) for sg in sg_data),
                'json': ",".join(Ec2Instance._sg_format(sg['GroupName'], sg['GroupId']) for sg in sg_data),
                }
        return print_formats[print_format]

    @staticmethod
    def _get_launchtime_printable_value(lt_data, print_format):
        """Return the printable value for launch time.

        Args:
          - lt_data: The launch time to be printed. (string)
        """
        print_formats = {
                'table': lt_data,
                'json': AWSInstance.json_serial(lt_data),
                }
        return print_formats[print_format]


    @staticmethod
    def get_field_printable_value(instance, field_name, print_format):
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
            'SecurityGroups': Ec2Instance._get_securitygroups_printable_value,
            'LaunchTime': Ec2Instance._get_launchtime_printable_value,
            }
        field_data = instance[field_name]
        try:
            printable_data = field_format_functions[field_name](field_data, print_format)
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
                'name': 'SecurityGroups',
                'printable_name': "Security Groups",
                'verbose_display': True,
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

    @staticmethod
    def _get_instances_printable_value(instances, print_format):
        """Return the printable value thss set of ELBs.
        """
        print_formats = {
                'table': "\n".join([instance['InstanceId'] for instance in instances]),
                'json': ",".join([instance['InstanceId'] for instance in instances]),
                }
        return print_formats[print_format]

    @staticmethod
    def _get_securitygroups_printable_value(sg_data, print_format):
        """Return the printable value for security groups.

        Args:
          - sg_data: The security groups to be printed. (string)
        """
        print_formats = {
                'table': "\n".join([sg for sg in sg_data]),
                'json': ",".join([sg for sg in sg_data]),
                }
        return print_formats[print_format]

    @staticmethod
    def _get_createdtime_printable_value(ct_data, print_format):
        """Return the printable value for create time.

        Args:
          - ct_data: The launch time to be printed. (string)
        """
        print_formats = {
                'table': ct_data,
                'json': AWSInstance.json_serial(ct_data),
                }
        return print_formats[print_format]

    @staticmethod
    def get_field_printable_value(instance, field_name, print_format):
        """Return a printable value for a given field.

        Args:
          - instance: The AWS resource instance that is being printed. (AwsInstance)
          - field_name: The field that is to be printed. (string)
        """
        field_format_functions = {
            'Instances': ElbInstance._get_instances_printable_value,
            'SecurityGroups': ElbInstance._get_securitygroups_printable_value,
            'CreatedTime': ElbInstance._get_createdtime_printable_value,
            }
        field_data = instance[field_name]
        try:
            printable_data = field_format_functions[field_name](field_data, print_format)
        except KeyError:
            printable_data = field_data

        return printable_data
