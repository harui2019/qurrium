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

from typing import Literal, Optional, Type, overload, Union
from qiskit.providers import Backend, Provider

from .utils import backend_name_getter, shorten_name
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
    "qiskit_ibm_runtime",
    "qiskit_ibm_provider",
    "qiskit_ibmq_provider",
]
ImportPointOrder: list[ImportPointType] = [
    "qiskit_ibm_runtime",
    "qiskit_ibm_provider",
    "qiskit_ibmq_provider",
]
REAL_BACKEND_SOURCES: dict[ImportPointType, Optional[Type[Backend]]] = {}
REAL_PROVIDER_SOURCES: dict[
    ImportPointType, Optional[Union[Type[Provider], Type["QiskitRuntimeService"]]]
] = {}
REAL_VERSION_INFOS: dict[ImportPointType, Optional[str]] = {}
REAL_IMPORT_ERROR_INFOS: dict[ImportPointType, ImportError] = {}
REAL_SOURCE_AVAILABLE: dict[ImportPointType, bool] = {}

try:
    from qiskit_ibm_runtime import (
        QiskitRuntimeService,
        __version__ as qiskit_ibm_runtime_version,
        IBMBackend as IBMRuntimeBackend,
    )

    REAL_PROVIDER_SOURCES["qiskit_ibm_runtime"] = QiskitRuntimeService
    REAL_VERSION_INFOS["qiskit_ibm_runtime"] = qiskit_ibm_runtime_version
    REAL_BACKEND_SOURCES["qiskit_ibm_runtime"] = IBMRuntimeBackend
except ImportError as err:
    REAL_PROVIDER_SOURCES["qiskit_ibm_runtime"] = None
    REAL_VERSION_INFOS["qiskit_ibm_runtime"] = None
    REAL_BACKEND_SOURCES["qiskit_ibm_runtime"] = None
    REAL_IMPORT_ERROR_INFOS["qiskit_ibm_runtime"] = err
REAL_SOURCE_AVAILABLE["qiskit_ibm_runtime"] = (
    REAL_PROVIDER_SOURCES["qiskit_ibm_runtime"] is not None
)

if len(REAL_BACKEND_SOURCES) == 0:
    try:
        from qiskit_ibm_provider import (  # type: ignore
            IBMProvider,
            IBMBackend as IBMProviderBackend,
            __version__ as qiskit_ibm_provider_version,
        )

        REAL_PROVIDER_SOURCES["qiskit_ibm_provider"] = IBMProvider
        REAL_VERSION_INFOS["qiskit_ibm_provider"] = qiskit_ibm_provider_version
        REAL_BACKEND_SOURCES["qiskit_ibm_provider"] = IBMProviderBackend
    except ImportError as err:
        REAL_PROVIDER_SOURCES["qiskit_ibm_provider"] = None
        REAL_VERSION_INFOS["qiskit_ibm_provider"] = None
        REAL_BACKEND_SOURCES["qiskit_ibm_provider"] = None
        REAL_IMPORT_ERROR_INFOS["qiskit_ibm_provider"] = err
    REAL_SOURCE_AVAILABLE["qiskit_ibm_provider"] = (
        REAL_PROVIDER_SOURCES["qiskit_ibm_provider"] is not None
    )

if len(REAL_BACKEND_SOURCES) == 0:
    try:
        from qiskit.providers.ibmq import IBMQBackend, AccountProvider  # type: ignore

        REAL_PROVIDER_SOURCES["qiskit_ibmq_provider"] = AccountProvider
        REAL_VERSION_INFOS["qiskit_ibmq_provider"] = QISKIT_VERSION.get("qiskit_ibmq_provider")
        REAL_BACKEND_SOURCES["qiskit_ibmq_provider"] = IBMQBackend
    except ImportError as err:
        REAL_PROVIDER_SOURCES["qiskit_ibmq_provider"] = None
        REAL_VERSION_INFOS["qiskit_ibmq_provider"] = None
        REAL_BACKEND_SOURCES["qiskit_ibmq_provider"] = None
        REAL_IMPORT_ERROR_INFOS["qiskit_ibmq_provider"] = err
    REAL_SOURCE_AVAILABLE["qiskit_ibmq_provider"] = (
        REAL_PROVIDER_SOURCES["qiskit_ibmq_provider"] is not None
    )


def get_default_real_source() -> Optional[ImportPointType]:
    """Get the default source for IBM Quantum devices.

    Returns:
        ImportPointType: The default source for IBM Quantum devices.

    """

    for source in ImportPointOrder:
        if source in REAL_SOURCE_AVAILABLE:
            return source
    return None


REAL_DEFAULT_SOURCE: Optional[ImportPointType] = get_default_real_source()


@overload
def real_backend_loader(
    real_provider=None,
) -> tuple[dict[str, str], dict[str, Backend], None]: ...


@overload
def real_backend_loader(
    real_provider: Provider,
) -> tuple[dict[str, str], dict[str, Backend], Provider]: ...


def real_backend_loader(real_provider=None):
    """Load the real backend.

    Args:
        real_provider (Optional[Provider], optional):
            The real provider. Defaults to None.

    Returns:
        tuple[dict[str, str], dict[str, Backend], Optional[Provider]]:
            The callsign of real backend,
            the real backend dict,
            the real provider.
    """
    if real_provider is not None:
        backend_ibmq_callsign = {}
        _real_provider = real_provider
        backend_ibmq = {backend_name_getter(b): b for b in real_provider.backends()}
        backend_ibmq_callsign = {
            shorten_name(bn, ["ibm_", "ibmq_"], ["ibmq_qasm_simulator"]): bn
            for bn in [backs for backs in backend_ibmq if "ibm" in backs]
        }
        backend_ibmq_callsign["ibmq_qasm"] = "ibmq_qasm_simulator"
        return backend_ibmq_callsign, backend_ibmq, _real_provider

    return {}, {}, None
