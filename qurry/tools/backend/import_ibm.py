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

from qiskit import __qiskit_version__
from qiskit.providers import Backend, Provider

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
]
ImportPointOrder = [
    "qiskit_ibm_provider",
    "qiskit_ibmq_provider",
]
BACKEND_SOURCES: dict[ImportPointType, Optional[Type[Backend]]] = {}
RealProviderType = Union[Provider, "IBMQWrapper"]
PROVIDER_SOURCES: dict[
    ImportPointType, Optional[Union[Type[Provider], "IBMQWrapper"]]
] = {}
VERSION_INFOS: dict[ImportPointType, Optional[str]] = {}
IMPORT_ERROR_INFOS: dict[ImportPointType, ImportError] = {}

try:
    from qiskit_ibm_provider import IBMProvider
    from qiskit_ibm_provider import IBMBackend
    from qiskit_ibm_provider.version import get_version_info

    PROVIDER_SOURCES["qiskit_ibm_provider"] = IBMProvider
    VERSION_INFOS["qiskit_ibm_provider"] = get_version_info()
    BACKEND_SOURCES["qiskit_ibm_provider"] = IBMBackend
except ImportError as err:
    PROVIDER_SOURCES["qiskit_ibm_provider"] = None
    VERSION_INFOS["qiskit_ibm_provider"] = None
    BACKEND_SOURCES["qiskit_ibm_provider"] = None
    IMPORT_ERROR_INFOS["qiskit_ibm_provider"] = err

try:
    from qiskit import IBMQ, IBMQWrapper
    from qiskit.providers.ibmq import IBMQBackend  # type: ignore

    PROVIDER_SOURCES["qiskit_ibmq_provider"] = IBMQ
    VERSION_INFOS["qiskit_ibmq_provider"] = __qiskit_version__.get(
        "qiskit_ibmq_provider"
    )
    BACKEND_SOURCES["qiskit_ibmq_provider"] = IBMQBackend
except ImportError as err:
    PROVIDER_SOURCES["qiskit_ibmq_provider"] = None
    VERSION_INFOS["qiskit_ibmq_provider"] = None
    BACKEND_SOURCES["qiskit_ibmq_provider"] = None
    IMPORT_ERROR_INFOS["qiskit_ibmq_provider"] = err


IBM_AVAILABLE = "qiskit_ibm_provider" in PROVIDER_SOURCES
IBMQ_AVAILABLE = "qiskit_ibmq_provider" in PROVIDER_SOURCES


def get_default_real_source() -> Optional[ImportPointType]:
    """Get the default source for the simulator.

    Returns:
        ImportPointType: The default source for the simulator.

    """

    if IBM_AVAILABLE:
        return "qiskit_ibm_provider"
    if IBMQ_AVAILABLE:
        return "qiskit_ibmq_provider"
    return None


DEFAULT_SOURCE: Optional[ImportPointType] = get_default_real_source()
