"""Qiskit Version (:mod:`qurry.tools.qiskit_version`)

- This module is for checking the version of qiskit and its packages.
- For remaking the deprecated `QiskitVersion` in :mod:`qiskit.version` since 1.0.0.

"""

import warnings
from importlib.metadata import distributions
import requests

from qiskit import __version__ as qiskit_version

from ..version import __version__
from ..capsule.hoshi import Hoshi


def local_qiskit_version_info():
    """Get the local version of qiskit and its miscellaneous packages,
    basically the package with 'qiskit' in its name. And sort the package by its name.

    Return:
        The local version of qiskit and its miscellaneous packages.
    """
    qiskit_distro_list = [
        (
            distro.metadata["Name"],
            {
                "dist": distro.locate_file(distro.metadata["Name"]),
                "local_version": distro.version,
            },
        )
        for distro in distributions()
        if "qiskit" in distro.metadata["Name"].lower()
    ]
    qiskit_distro_list.sort(key=lambda x: x[0])

    return dict(qiskit_distro_list)


def qiskit_version_info():
    """Get the local version of qiskit and its miscellaneous packages,
    basically the package with 'qiskit' in its name. And sort the package by its name.
    And also get the latest version of each package from PyPI.

    Return:
        The local version of qiskit and its miscellaneous packages, and the latest version of each
        package from PyPI.
    """

    local_version_dict = local_qiskit_version_info()
    for k in list(local_version_dict.keys()):
        try:
            response = requests.get(f"https://pypi.org/pypi/{k}/json", timeout=5)
            latest_version = response.json()["info"]["version"]
        except requests.exceptions.RequestException as e:
            warnings.warn(f"Failed to get latest version of {k} from PyPI: {e}")
            latest_version = None
        local_version_dict[k]["latest_version"] = latest_version

    return local_version_dict


def get_qiskit_version_statesheet() -> Hoshi:
    """Get the version of qiskit and its packages as a statesheet.

    Returns:
        The statesheet of the version of qiskit and its packages.
    """

    check_msg = Hoshi(
        [
            ("txt", f"| Qurrium version: {__version__}"),
            ("divider", 80),
            ("h3", "Qiskit version"),
        ],
        ljust_description_len=40,
    )
    version_dict = qiskit_version_info()

    check_msg.newline(
        {
            "type": "itemize",
            "description": "package name",
            "value": "Local version / Latest version on PyPI.",
            "ljust_description_filler": ".",
        }
    )
    for k, v in version_dict.items():
        check_msg.newline(
            {
                "type": "itemize",
                "description": f"{k}",
                "value": f"{v['local_version']}"
                + (f" / {v['latest_version']}" if v["latest_version"] else " / N/A"),
                "ljust_description_filler": ".",
                "listing_level": 2,
            }
        )
    check_msg.divider(80)
    check_msg.newline(
        {
            "type": "itemize",
            "description": (
                "Please keep mind on your qiskit version, "
                + "a very outdated version may cause some problems."
            ),
            "listing_itemize": "+",
        }
    )
    if any("aer-gpu" in k for k in version_dict):
        check_msg.newline(
            {
                "type": "itemize",
                "description": (
                    "If you are using qiskit-aer-gpu, suggest to use the version "
                    + "same with qiskit-aer."
                ),
                "listing_itemize": "+",
            }
        )
    check_msg.divider(80)

    return check_msg


def qiskit_version_v0_check():
    """Check the version of qiskit and its packages.

    This function checks the version of qiskit and its packages,
    and raises a warning if the version is lower than 1.0.0.
    It is recommended to use the latest version of qiskit for compatibility with Qurrium.
    """
    qiskit_version_tuple = tuple(map(int, qiskit_version.split(".")))

    if qiskit_version_tuple < (1, 0, 0):
        warnings.warn(
            "Qiskit version is lower than 1.0.0. "
            "Qiskit v0 is deprecated since the end of 2023. "
            "Qurrium is not garanteed to work with this version of Qiskit. "
            "And it may not be compatible with the latest features of Qurrium. "
            "Please update Qiskit to the latest version.",
        )
