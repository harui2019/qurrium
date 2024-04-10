"""
================================================================
Import IBM (:mod:`qurry.tools.backend.import_ibm`)
================================================================

For qiskit-aer has been divided into two packages since qiskit some version,
So it needs to be imported differently by trying to import qiskit-aer first.

And qiskit-ibmq-provider has been deprecated, 
but for some user may still need to use it,
so it needs to be imported also differently by trying to import qiskit-ibm-provider first.

So this file is used to unify the import point of AerProvider, IBMProvider/IBMQProvider.
Avoiding the import error occurs on different parts of Qurry.
"""

from typing import Union, Literal, Optional, Type
from qiskit.providers import Backend, Provider

from ..qiskit_version import QISKIT_VERSION
from ...exceptions import QurryExtraPackageRequired


class DummyProvider(Provider):
    """A dummy provider for :class:`qurry.tools.backend.backendWrapper`
    to use when the real provider is not available,
    And it will print a warning message when you try to use it.
    Also it is a cheatsheet for type checking in this scenario.

    """

    @staticmethod
    def save_account():
        """A dummy method for :class:`qurry.tools.backend.backendWrapper`
        to use when the real provider is not available,
        And it will print a warning message when you try to use it.
        Also it is a cheatsheet for type checking in this scenario.

        """
        raise QurryExtraPackageRequired(
            "The real provider is not available, please check your installation"
        )

    @staticmethod
    def load_account():
        """A dummy method for :class:`qurry.tools.backend.backendWrapper`
        to use when the real provider is not available,
        And it will print a warning message when you try to use it.
        Also it is a cheatsheet for type checking in this scenario.

        """

        raise QurryExtraPackageRequired(
            "The real provider is not available, please check your installation"
        )

    @staticmethod
    def get_provider():
        """A dummy method for :class:`qurry.tools.backend.backendWrapper`
        to use when the real provider is not available,
        And it will print a warning message when you try to use it.
        Also it is a cheatsheet for type checking in this scenario.

        """
        raise QurryExtraPackageRequired(
            "The real provider is not available, please check your installation"
        )


# pylint: disable=ungrouped-imports
ImportPointType = Literal[
    "qiskit_ibm_provider",
    "qiskit_ibmq_provider",
    "qiskit_ibm_runtime",
]
ImportPointOrder: list[ImportPointType] = [
    "qiskit_ibm_provider",
    "qiskit_ibmq_provider",
    "qiskit_ibm_runtime",
]
BACKEND_SOURCES: dict[ImportPointType, Optional[Type[Backend]]] = {}
PROVIDER_SOURCES: dict[ImportPointType, Optional[Type[Provider]]] = {}
VERSION_INFOS: dict[ImportPointType, Optional[str]] = {}
IMPORT_ERROR_INFOS: dict[ImportPointType, ImportError] = {}
SOURCE_AVAILABLE: dict[ImportPointType, bool] = {}

try:
    from qiskit_ibm_provider import (
        IBMProvider,
        IBMBackend as IBMProviderBackend,
        __version__ as qiskit_ibm_provider_version,
    )

    PROVIDER_SOURCES["qiskit_ibm_provider"] = IBMProvider
    VERSION_INFOS["qiskit_ibm_provider"] = qiskit_ibm_provider_version
    BACKEND_SOURCES["qiskit_ibm_provider"] = IBMProviderBackend
except ImportError as err:
    PROVIDER_SOURCES["qiskit_ibm_provider"] = None
    VERSION_INFOS["qiskit_ibm_provider"] = None
    BACKEND_SOURCES["qiskit_ibm_provider"] = None
    IMPORT_ERROR_INFOS["qiskit_ibm_provider"] = err
SOURCE_AVAILABLE["qiskit_ibm_provider"] = (
    PROVIDER_SOURCES["qiskit_ibm_provider"] is not None
)

try:
    from qiskit_ibm_runtime import (
        QiskitRuntimeService,
        __version__ as qiskit_ibm_runtime_version,
        IBMBackend as IBMRuntimeBackend,
    )

    PROVIDER_SOURCES["qiskit_ibm_runtime"] = QiskitRuntimeService
    VERSION_INFOS["qiskit_ibm_runtime"] = qiskit_ibm_runtime_version
    BACKEND_SOURCES["qiskit_ibm_runtime"] = IBMRuntimeBackend
except ImportError as err:
    PROVIDER_SOURCES["qiskit_ibm_runtime"] = None
    VERSION_INFOS["qiskit_ibm_runtime"] = None
    BACKEND_SOURCES["qiskit_ibm_runtime"] = None
    IMPORT_ERROR_INFOS["qiskit_ibm_runtime"] = err
SOURCE_AVAILABLE["qiskit_ibm_runtime"] = (
    PROVIDER_SOURCES["qiskit_ibm_runtime"] is not None
)

try:
    from qiskit.providers.ibmq import IBMQBackend, AccountProvider  # type: ignore

    PROVIDER_SOURCES["qiskit_ibmq_provider"] = AccountProvider
    VERSION_INFOS["qiskit_ibmq_provider"] = QISKIT_VERSION.get("qiskit_ibmq_provider")
    BACKEND_SOURCES["qiskit_ibmq_provider"] = IBMQBackend
except ImportError as err:
    PROVIDER_SOURCES["qiskit_ibmq_provider"] = None
    VERSION_INFOS["qiskit_ibmq_provider"] = None
    BACKEND_SOURCES["qiskit_ibmq_provider"] = None
    IMPORT_ERROR_INFOS["qiskit_ibmq_provider"] = err
SOURCE_AVAILABLE["qiskit_ibmq_provider"] = (
    PROVIDER_SOURCES["qiskit_ibmq_provider"] is not None
)


def get_default_real_source() -> Optional[ImportPointType]:
    """Get the default source for IBM Quantum devices.

    Returns:
        ImportPointType: The default source for IBM Quantum devices.

    """

    for i in ImportPointOrder:
        if SOURCE_AVAILABLE[i]:
            return i
    return None


DEFAULT_SOURCE: Optional[ImportPointType] = get_default_real_source()
