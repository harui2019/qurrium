"""
================================================================
Backend Environment Check 
(:mod:`qurry.tools.backend.env_check`)
================================================================

For qiskit-aer has been divided into two packages since qiskit some version,
So it needs to be imported differently by trying to import qiskit-aer first.

And qiskit-ibmq-provider has been deprecated, 
but for some user may still need to use it,
so it needs to be imported also differently by trying to import qiskit-ibm-provider first.

So this file is used to unify the import point of AerProvider, IBMProvider/IBMQProvider.
Avoiding the import error occurs on different parts of Qurry.

"""

from typing import Any
from importlib.metadata import distributions
import requests

from .import_ibm import (
    REAL_VERSION_INFOS as real_version_infos,
    REAL_DEFAULT_SOURCE as real_default_source,
)
from .import_simulator import (
    SIM_VERSION_INFOS as sim_version_infos,
    SIM_DEFAULT_SOURCE as sim_default_source,
)
from ..qiskit_version import QISKIT_VERSION
from ..command import pytorch_cuda_check
from ...capsule.hoshi import Hoshi


def _local_version() -> dict[str, dict[str, Any]]:
    """Get the local version of qiskit and qiskit-aer-gpu."""
    # pylint: disable=protected-access
    basic = {}
    for i in distributions():
        if i.metadata["Name"] == "qiskit-aer-gpu":
            basic["qiskit-aer-gpu"] = {
                "dist": i.locate_file(i.metadata["Name"]),
                "local_version": i.version,
            }
        elif i.metadata["Name"] == "qiskit":
            basic["qiskit"] = {
                "dist": i.locate_file(i.metadata["Name"]),
                "local_version": i.version,
            }
    # pylint: enable=protected-access
    return basic


def _version_check():
    """Version check to remind user to update qiskit if needed."""

    check_msg = Hoshi(
        [
            ("divider", 60),
            ("h3", "Qiskit version outdated warning"),
            (
                "txt",
                (
                    "Please keep mind on your qiskit version, "
                    + "a very outdated version may cause some problems."
                ),
            ),
        ],
        ljust_describe_len=40,
    )
    local_version_dict = _local_version()
    for k, v in local_version_dict.items():
        try:
            response = requests.get(f"https://pypi.org/pypi/{k}/json", timeout=5)
            latest_version = response.json()["info"]["version"]
            latest_version_tuple = tuple(map(int, latest_version.split(".")))
            local_version_tuple = tuple(map(int, v["local_version"].split(".")))

            if latest_version_tuple > local_version_tuple:
                check_msg.newline(
                    {
                        "type": "itemize",
                        "description": f"{k}",
                        "value": f"{v['local_version']}/{latest_version}",
                        "hint": "The Local version/The Latest version on PyPI.",
                    }
                )
        except requests.exceptions.RequestException as e:
            check_msg.newline(
                {
                    "type": "itemize",
                    "description": f"Request error due to '{e}'",
                    "value": None,
                }
            )

    for k, v in QISKIT_VERSION.items():
        check_msg.newline(
            {
                "type": "itemize",
                "description": f"{k}",
                "value": str(v),
                "listing_level": 2,
            }
        )
    check_msg.newline(
        (
            "txt",
            (
                "'qiskit-ibm-provider' is the replacement of "
                + "deprcated module 'qiskit-ibmq-provider'."
            ),
        )
    )
    check_msg.newline(
        {
            "type": "itemize",
            "description": (real_default_source if real_default_source else "qiskit_ibm_provider"),
            "value": (
                real_version_infos[real_default_source]
                if real_default_source
                else "Not available, please install it first."
            ),
        }
    )

    if "qiskit-aer-gpu" in local_version_dict:
        check_msg.newline(
            (
                "txt",
                "If version of 'qiskit-aer' is not same with 'qiskit-aer-gpu', "
                + "it may cause GPU backend not working.",
            )
        )
        check_msg.newline(
            {
                "type": "itemize",
                "description": "qiskit-aer",
                "value": f"{sim_version_infos[sim_default_source]}, "
                + f"imported from '{sim_default_source}'",
            }
        )
        check_msg.newline(
            {
                "type": "itemize",
                "description": "qiskit-aer-gpu",
                "value": local_version_dict["qiskit-aer-gpu"]["local_version"],
            }
        )

    pytorch_cuda_check()

    return check_msg


def version_check():
    """Version check to remind user to update qiskit if needed."""
    check_msg = _version_check()
    print(check_msg)
    return check_msg


async def _async_version_check():
    """Version check to remind user to update qiskit if needed."""
    check_msg = _version_check()
    return check_msg
