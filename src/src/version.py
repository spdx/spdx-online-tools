"""
Version file for displaying the respective version of
the tools and online-tools repositories.
"""

from importlib.metadata import version
from os.path import abspath, join, dirname
from subprocess import run, PIPE
from re import search


def get_tools_version(jar_name: str) -> str:
    """Returns Java Tools version.

    Visit https://github.com/spdx/tools-java/releases to know about the tools
    releases.

    Arguments:
        jarName {string} -- Name of the JAVA Tools jar file

    Returns:
        string -- JAVA Tools version
    """
    jar_path = join(dirname(abspath(__file__)), '..', jar_name)
    output = run(['java', '-jar', jar_path, 'Version'], stdout=PIPE).stdout.decode('utf-8')
    match = search('SPDX Tool Version: ([^;]+);', output)
    if match:
        return match.group(1)
    return 'Unknown'


spdx_online_tools_version = '1.3.2'

java_tools_version = get_tools_version('tool.jar')
ntia_conformance_checker_version = version('ntia-conformance-checker')
python_tools_version = version('spdx-tools')
