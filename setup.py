from setuptools import setup, find_packages


def get_requirements(source):
    with open(source, "r") as f:
        requirements = f.read().splitlines()
    return requirements


setup(packages=find_packages(), install_requires=get_requirements("requirements/requirements.txt"))
