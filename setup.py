"""This module contains the packaging routine for the pybook package"""

from setuptools import setup, find_packages
try:
    from pip.download import PipSession
    from pip.req import parse_requirements
except ImportError:
    # It is quick hack to support pip 10 that has changed its internal
    # structure of the modules.
    from pip._internal.download import PipSession
    from pip._internal.req.req_file import parse_requirements


def get_requirements(source):
    """Get the requirements from the given ``source``

    Parameters
    ----------
    source: str
        The filename containing the requirements

    """

    install_reqs = parse_requirements(filename=source, session=PipSession())

    return [str(ir.req) for ir in install_reqs]


setup(
    packages=find_packages(),
    install_requires=get_requirements('requirements/requirements.txt')
)


