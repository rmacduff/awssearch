# Search AWS Resources

Search for AWS resources across multiple accounts and regions.

```
$ awssearch --help
usage: awssearch [-h] [-a AWS_ACCOUNT] [-r AWS_REGIONS] [-v] {ec2,elb} ...

Query EC2 instances

positional arguments:
  {ec2,elb}             AWS resource to search for
    ec2                 search for ec2 instances
    elb                 search for elb instances

optional arguments:
  -h, --help            show this help message and exit
  -a AWS_ACCOUNT, --account AWS_ACCOUNT
  -r AWS_REGIONS, --region AWS_REGIONS
  -v, --verbose

```

## Examples

Search across all accounts for EC2 instances that have the string "prod-api" in them.

```
$ awssearch ec2 --name prod-api
+-------------+---------------------+------------+------------------+-----------------+-------------------+---------+
| Name        | Instance ID         | Placement  | Private IP       | Public IP       | Tags              | Account |
+-------------+---------------------+------------+------------------+-----------------+-------------------+---------+
| prod-api-01 | i-4bda1b63157ade783 | us-east-1a | ssh://10.0.1.100 | ssh://1.2.3.4   | app:api, env:prod | myprod  |
| prod-api-02 | i-0906a7f1172a90c26 | us-east-1e | ssh://10.0.1.101 | ssh://1.2.3.5   | app:api, env:prod | myprod  |
| prod-api-03 | i-e16c4f2934bd2902a | us-west-1b | ssh://10.0.1.102 | ssh://1.2.3.6   | app:api, env:prod | myprod  |
+-------------+---------------------+------------+------------------+-----------------+-------------------+---------+
```

Search in us-west-2 for ELBs that have the string "staging" in the DNS name.

```
$ awssearch -r us-west-2 elb --dns staging
+-------------+------------------------------------------------------+-------------------------+------------+
| Name        | DNS Name                                             | Instances               | Account    |
+-------------+------------------------------------------------------+-------------------------+------------+
| api-staging | api-staging-1849381612.us-west-2.elb.amazonaws.com   | i-5411b08c, i-a6258161, | mystaging  |
| web-staging | web-staging-1824526360.us-west-2.elb.amazonaws.com   | i-049b38c3,             | mystaging  |
+-------------+------------------------------------------------------+-------------------------+------------+
```


# Installation

## Pip

Install into a virtualenv using pip.

```
pip install /path/to/aws-search
```

## Pipsi

[Pipsi](https://github.com/mitsuhiko/pipsi) makes it easy to install Python packages that have scripts. It handles the setting up of virtualenvs so you don't have to worry about that!

```
pipsi install /path/to/aws-search
```

## Configuration

Speficy the AWS accounts and regions inside `~/.aws-search.yml`.

Example:
```
aws_accounts:
    - myprod
    - mystaging

aws_regions:
    - us-east-1
    - us-west-1
    - us-west-2
```

The values for `aws_accounts` must match the AWS accounts you have configured 
in `~/.aws/config` and `~/.aws/credentials`.

