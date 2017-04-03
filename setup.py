# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='awssearch',

    version='0.3.0',

    description='Search AWS inventory across accounts and regions',
    long_description=long_description,

    url='https://gitlab.com/rmacduff/aws-search',

    author='Ross Macduff',
    author_email='ross@macduff.ca',

    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: System Administrators',
        'Topic :: Infrastructure Tools',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],

    keywords='aws infrastructure',

    install_requires=['terminaltables', 'boto3', 'pyyaml'],

    entry_points={
        'console_scripts': [
            'awssearch = awssearch.cli:main',
        ],
    },
    packages=find_packages(),
)