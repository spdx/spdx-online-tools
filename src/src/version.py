# SPDX-FileCopyrightText: 2020-present SPDX Contributors
# SPDX-License-Identifier: Apache-2.0

"""
Version file for displaying the respective version of
the tools and online-tools repositories.
"""

from importlib.metadata import version
from os.path import abspath, dirname, join
from re import search
from subprocess import PIPE, run


def get_tools_version(jar_name: str) -> str:
    """Returns SPDX Java Tools version.

    Visit https://github.com/spdx/tools-java/releases to know about the tools releases.

    Arguments:
        jarName {string} -- Name of the SPDX Java Tools jar file

    Returns:
        string -- SPDX Java Tools version
    """
    jar_path = join(dirname(abspath(__file__)), "..", jar_name)
    output = run(["java", "-jar", jar_path, "Version"], stdout=PIPE).stdout.decode(
        "utf-8"
    )
    match = search("SPDX Tools? Version: ([^;]+);", output)
    if match:
        return match.group(1)
    return "Unknown"


spdx_online_tools_version = "1.4.0"  # Update this when releasing new version

java_tools_version = get_tools_version("tool.jar")
ntia_conformance_checker_version = version("ntia-conformance-checker")
python_tools_version = version("spdx-tools")
spdx_license_matcher_version = version("spdx-license-matcher")
spdx_python_model_version = version("spdx-python-model")
