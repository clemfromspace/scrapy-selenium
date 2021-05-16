from setuptools import setup, find_packages

setup(
    packages=find_packages(),
    install_requires=[l for l in open('requirements/requirements.txt').readlines()]
)


