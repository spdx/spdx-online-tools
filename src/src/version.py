# SPDX-License-Identifier: Apache-2.0

"""
Version file for displaying the respective version of
the tools and online-tools repositories.
"""

from importlib.metadata import version
from os.path import abspath, dirname, exists, join
from subprocess import run, PIPE
from re import search
import json

from .settings import LICENSE_ROOT


def get_tools_version(jar_name):
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


def get_spdx_license_list_version():
    """
    Determine license list version from a local copy of licenses.json if available.

    Returns:
        string -- SPDX License List version
    """
    paths = [
        join(LICENSE_ROOT, "current", "licenses.json"),
    ]
    for p in paths:
        try:
            if not exists(p):
                continue
            with open(p, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict) and "licenseListVersion" in data:
                return data["licenseListVersion"]
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue
    return "Unknown"

spdx_online_tools_version = "1.3.2"
spdx_license_list_version = get_spdx_license_list_version()
java_tools_version = get_tools_version("tool.jar")
python_tools_version = version('spdx-tools')
ntia_conformance_checker_version = version("ntia-conformance-checker")
