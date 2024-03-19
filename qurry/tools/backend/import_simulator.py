"""
================================================================
Import Simulator (:mod:`qurry.tools.backend.import_simulator`)
================================================================

For qiskit-aer has been divided into two packages since qiskit some version,
So it needs to be imported differently by trying to import qiskit-aer first.

And qiskit-ibmq-provider has been deprecated, 
but for some user may still need to use it,
so it needs to be imported also differently by trying to import qiskit-ibm-provider first.

So this file is used to unify the import point of AerProvider, IBMProvider/IBMQProvider.
Avoiding the import error occurs on different parts of Qurry.
"""

from typing import Literal, Type, Optional

from qiskit import __qiskit_version__
from qiskit.providers import BackendV1, BackendV2, Backend, Provider

# pylint: disable=ungrouped-imports
ImportPointType = Literal[
    "qiskit_aer",
    "qiskit.providers.aer",
    "qiskit.providers.basicaer",
    "qiskit.providers.basic_provider",
]
ImportPointOrder = [
    "qiskit_aer",
    "qiskit.providers.basic_provider",
    "qiskit.providers.basicaer",
    "qiskit.providers.aer",
]
SIMULATOR_SOURCES: dict[ImportPointType, Type[Backend]] = {}
BACKEND_SOURCES: dict[ImportPointType, Type[Backend]] = {}
PROVIDER_SOURCES: dict[ImportPointType, Type[Provider]] = {}
VERSION_INFOS: dict[ImportPointType, Optional[str]] = {}
IMPORT_ERROR_INFOS: dict[ImportPointType, ImportError] = {}

try:
    from qiskit_aer import AerProvider, AerSimulator
    from qiskit_aer.backends.aerbackend import AerBackend
    from qiskit_aer.version import get_version_info as get_version_info_aer

    VERSION_INFOS["qiskit_aer"] = get_version_info_aer()
    SIMULATOR_SOURCES["qiskit_aer"] = AerSimulator
    BACKEND_SOURCES["qiskit_aer"] = AerBackend
    PROVIDER_SOURCES["qiskit_aer"] = AerProvider
except ImportError as err:
    IMPORT_ERROR_INFOS["qiskit_aer"] = err

try:
    from qiskit.providers.aer import (  # type: ignore
        AerProvider as AerProviderDep,  # type: ignore
        AerSimulator as AerSimulatorDep,  # type: ignore
    )
    from qiskit.providers.aer.backends.aerbackend import (  # type: ignore
        AerBackend as AerBackendDep,
    )  # type: ignore
    from qiskit.providers.aer.version import VERSION  # type: ignore

    VERSION_INFOS["qiskit.providers.aer"] = VERSION
    SIMULATOR_SOURCES["qiskit.providers.aer"] = AerSimulatorDep
    BACKEND_SOURCES["qiskit.providers.aer"] = AerBackendDep
    PROVIDER_SOURCES["qiskit.providers.aer"] = AerProviderDep
except ImportError as err:
    IMPORT_ERROR_INFOS["qiskit.providers.aer"] = err

try:
    from qiskit.providers.basicaer.basicaerprovider import (
        BasicAerProvider,
        QasmSimulatorPy,
    )

    VERSION_INFOS["qiskit.providers.basicaer"] = __qiskit_version__.get("qiskit")
    SIMULATOR_SOURCES["qiskit.providers.basicaer"] = QasmSimulatorPy
    BACKEND_SOURCES["qiskit.providers.basicaer"] = BackendV1
    PROVIDER_SOURCES["qiskit.providers.basicaer"] = BasicAerProvider
except ImportError as err:
    IMPORT_ERROR_INFOS["qiskit.providers.basicaer"] = err

try:
    from qiskit.providers.basic_provider import BasicSimulator, BasicProvider  # type: ignore

    VERSION_INFOS["qiskit.providers.basic_provider"] = __qiskit_version__.get("qiskit")
    SIMULATOR_SOURCES["qiskit.providers.basic_provider"] = BasicSimulator
    BACKEND_SOURCES["qiskit.providers.basic_provider"] = BackendV2
    PROVIDER_SOURCES["qiskit.providers.basic_provider"] = BasicProvider
except ImportError as err:
    IMPORT_ERROR_INFOS["qiskit.providers.basic_provider"] = err


def get_default_sim_source() -> ImportPointType:
    """Get the default source for the simulator.

    Returns:
        ImportPointType: The default source for the simulator.

    Raises:
        ImportError: If no available simulator source is found.
    """

    for source in ImportPointOrder:
        if source in SIMULATOR_SOURCES:
            return source
    raise ImportError(
        "No available simulator source, please check the installation of qiskit."
    )


DEFAULT_SOURCE: ImportPointType = get_default_sim_source()


# pylint: disable=too-few-public-methods
class GeneralSimulator(SIMULATOR_SOURCES[DEFAULT_SOURCE]):
    """Default simulator."""

    def __repr__(self):
        if DEFAULT_SOURCE == "qiskit.providers.basicaer":
            return f"<QasmSimulatorPy('{self.name()}')>"
        if DEFAULT_SOURCE == "qiskit.providers.basic_provider":
            return f"<BasicSimulator('{self.name}')>"
        if isinstance(self, BackendV1):
            return f"<AerSimulator('{self.name()}')>"
        return f"<AerSimulator('{self.name}')>"


class GeneralBackend(BACKEND_SOURCES[DEFAULT_SOURCE]):
    """The abstract class of default simulator."""


class GeneralProvider(PROVIDER_SOURCES[DEFAULT_SOURCE]):
    """Provider of default backend."""

    def __repr__(self):
        if DEFAULT_SOURCE == "qiskit.providers.basicaer":
            return "<BasicAerProvider>"
        if DEFAULT_SOURCE == "qiskit.providers.basic_provider":
            return "<BasicProvider>"
        if DEFAULT_SOURCE == "qiskit_aer":
            return "<AerProvider>"
        if DEFAULT_SOURCE == "qiskit.providers.aer":
            return "<AerProviderDep>"
        return super().__repr__()
