"""This module contains the packaging routine for the pybook package"""

from setuptools import setup, find_packages
try:
    from pip.download import PipSession
    from pip.req import parse_requirements
except ImportError:
    # It is quick hack to support pip 10 that has changed its internal
    # structure of the modules.
    # Further hack - seems like pip 20 and later does not support
    # pip._internal.download anymore. It appears as though 
    # parse_requirements (used below) does not need a valid PipSession. 
    # Any value seems to work. So hack this even more.
    try: 
        from pip._internal.download import PipSession
    except ImportError:
        PipSession = object
    from pip._internal.req.req_file import parse_requirements


def get_requirements(source):
    """Get the requirements from the given ``source``

    Parameters
    ----------
    source: str
        The filename containing the requirements

    """

    install_reqs = parse_requirements(filename=source, session=PipSession())
    # pip 20 changed ParsedRequirement.req to ParsedRequirement.requirement.
    try:
        requirements = [str(ir.req) for ir in install_reqs]
    except AttributeError:
        requirements = [str(ir.requirement) for ir in install_reqs]
    return requirements

setup(
    packages=find_packages(),
    install_requires=get_requirements('requirements/requirements.txt')
)


