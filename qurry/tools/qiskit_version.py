"""
================================================================
Qiskit Version (:mod:`qurry.tools.qiskit_version`)
================================================================

- This module is for checking the version of qiskit and its packages.
- For remaking the deprecated :cls:`QiskitVersion` in :mod:`qiskit.version`
since 1.0.0.

"""

from collections.abc import Mapping
from importlib.metadata import distributions

from qiskit import __version__ as qiskit_version
from ..version import __version__

from ..capsule.hoshi import Hoshi

KNOWN_CORE_PACKAGE = {
    "main": [
        "qiskit-aer",
        "qiskit-aer-gpu",
        "qiskit-aer-gpu-cu11",  # Extra package for CUDA 11
        "qiskit-ibm-provider",
        "qiskit-ibm-runtime",
    ],
    "deprecated": [
        "qiskit-ibmq-provider",
        "qiskit-terra",
        "qiskit-ignis",  # This has been deprecated in very early, even before I first knew qiskit.
    ],
    "into-community": [
        "qiskit-nature",
        "qiskit-finance",
        "qiskit-optimization",
        "qiskit-machine-learning",
    ],
}


class QiskitVersion(Mapping):
    """Get the version of qiskit and its packages.

    The replacement of deprecated :cls:`QiskitVersion` in :mod:`qiskit.version`.
    """

    __slots__ = ["_version_dict", "_loaded"]

    def __init__(self):
        self._version_dict = {
            "qiskit": qiskit_version,
        }
        self._loaded = False

    def _load_versions(self):
        for i in distributions():
            if (
                i.metadata["Name"]
                in KNOWN_CORE_PACKAGE["main"]
                + KNOWN_CORE_PACKAGE["deprecated"]
                + KNOWN_CORE_PACKAGE["into-community"]
            ):
                self._version_dict[i.metadata["Name"]] = i.version

    def __repr__(self):
        if not self._loaded:
            self._load_versions()
        return repr(self._version_dict)

    def __str__(self):
        if not self._loaded:
            self._load_versions()
        return str(self._version_dict)

    def __getitem__(self, key):
        if not self._loaded:
            self._load_versions()
        return self._version_dict[key]

    def __iter__(self):
        if not self._loaded:
            self._load_versions()
        return iter(self._version_dict)

    def __len__(self):
        return len(self._version_dict)


QISKIT_VERSION = QiskitVersion()


def qiskit_version_statesheet() -> Hoshi:
    """Get the version of qiskit and its packages as a statesheet.

    Returns:
        Hoshi: The statesheet of the version of qiskit and its packages.
    """
    item = [
        ("txt", f"| Qurry version: {__version__}"),
        ("divider", 44),
        ("h3", "Qiskit version"),
    ]
    for package_type, package_list in KNOWN_CORE_PACKAGE.items():
        item.append(
            {
                "type": "itemize",
                "description": package_type,
            }
        )
        for package in package_list:
            pkg_version = QISKIT_VERSION.get(package)
            if pkg_version:
                item.append(
                    {
                        "type": "itemize",
                        "description": package,
                        "value": pkg_version,
                        "listing_level": 2,
                        "ljust_description_filler": ".",
                    }
                )
    item.append(("divider", 44))

    if "qiskit-aer-gpu" in QISKIT_VERSION:
        item.append(
            {
                "type": "itemize",
                "description": "qiskit-aer-gpu"
                + (" and qiskit-aer-gpu-cu11" if "qiskit-aer-gpu-cu11" in QISKIT_VERSION else "")
                + " should have the same version as qiskit-aer.",
                "listing_itemize": "+",
                "ljust_description_filler": ".",
            }
        )
        item.append(("divider", 44))

    return Hoshi(item, ljust_description_filler=".")


QISKIT_VERSION_STATESHEET = qiskit_version_statesheet()
