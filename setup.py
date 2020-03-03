"""This module contains the packaging routine for the pybook package"""

from setuptools import setup, find_packages

requirements = [
    "scrapy>=1.0.0",
    "selenium>=3.9.0",
]

test_requirements = [
    "pytest==3.4.0",
    "coverage<4.4",
    "pytest-cov==2.4.0",
    "codeclimate-test-reporter==0.2.3",
    "attrs>=17.4.0",
]

setup(
    packages=find_packages(),
    install_requires=requirements,
)
