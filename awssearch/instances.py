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
        elif attribute == 'instance_state':
            running_state = self.__getattr__('state')['Name']
            if value == running_state:
                return True
        else:
            field_value = self.__getattr__(attribute)
            if value.lower() in field_value.lower():
                return True


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
