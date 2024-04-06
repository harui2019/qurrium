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

from qiskit import __version__

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
            "qiskit": __version__,
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
