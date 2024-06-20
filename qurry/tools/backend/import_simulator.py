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

from qiskit.providers import BackendV1, BackendV2, Backend, Provider

from ..qiskit_version import QISKIT_VERSION

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
SIM_BACKEND_SOURCES: dict[ImportPointType, Type[Backend]] = {}
SIM_PROVIDER_SOURCES: dict[ImportPointType, Type[Provider]] = {}
SIM_VERSION_INFOS: dict[ImportPointType, Optional[str]] = {}
SIM_IMPORT_ERROR_INFOS: dict[ImportPointType, ImportError] = {}

try:
    from qiskit_aer import AerProvider, AerSimulator
    from qiskit_aer.backends.aerbackend import AerBackend
    from qiskit_aer.version import get_version_info as get_version_info_aer

    SIM_VERSION_INFOS["qiskit_aer"] = get_version_info_aer()
    SIMULATOR_SOURCES["qiskit_aer"] = AerSimulator
    SIM_BACKEND_SOURCES["qiskit_aer"] = AerBackend
    SIM_PROVIDER_SOURCES["qiskit_aer"] = AerProvider
except ImportError as err:
    SIM_IMPORT_ERROR_INFOS["qiskit_aer"] = err

try:
    from qiskit.providers.aer import (  # type: ignore
        AerProvider as AerProviderDep,  # type: ignore
        AerSimulator as AerSimulatorDep,  # type: ignore
    )
    from qiskit.providers.aer.backends.aerbackend import (  # type: ignore
        AerBackend as AerBackendDep,
    )  # type: ignore
    from qiskit.providers.aer.version import VERSION  # type: ignore

    SIM_VERSION_INFOS["qiskit.providers.aer"] = VERSION
    SIMULATOR_SOURCES["qiskit.providers.aer"] = AerSimulatorDep
    SIM_BACKEND_SOURCES["qiskit.providers.aer"] = AerBackendDep
    SIM_PROVIDER_SOURCES["qiskit.providers.aer"] = AerProviderDep
except ImportError as err:
    SIM_IMPORT_ERROR_INFOS["qiskit.providers.aer"] = err

try:
    from qiskit.providers.basicaer.basicaerprovider import (
        BasicAerProvider,
        QasmSimulatorPy,
    )

    SIM_VERSION_INFOS["qiskit.providers.basicaer"] = QISKIT_VERSION.get("qiskit")
    SIMULATOR_SOURCES["qiskit.providers.basicaer"] = QasmSimulatorPy
    SIM_BACKEND_SOURCES["qiskit.providers.basicaer"] = BackendV1
    SIM_PROVIDER_SOURCES["qiskit.providers.basicaer"] = BasicAerProvider
except ImportError as err:
    SIM_IMPORT_ERROR_INFOS["qiskit.providers.basicaer"] = err

try:
    from qiskit.providers.basic_provider import BasicSimulator, BasicProvider  # type: ignore

    SIM_VERSION_INFOS["qiskit.providers.basic_provider"] = QISKIT_VERSION.get("qiskit")
    SIMULATOR_SOURCES["qiskit.providers.basic_provider"] = BasicSimulator
    SIM_BACKEND_SOURCES["qiskit.providers.basic_provider"] = BackendV2
    SIM_PROVIDER_SOURCES["qiskit.providers.basic_provider"] = BasicProvider
except ImportError as err:
    SIM_IMPORT_ERROR_INFOS["qiskit.providers.basic_provider"] = err


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
    raise ImportError("No available simulator source, please check the installation of qiskit.")


SIM_DEFAULT_SOURCE: ImportPointType = get_default_sim_source()


# pylint: disable=too-few-public-methods
class GeneralSimulator(SIMULATOR_SOURCES[SIM_DEFAULT_SOURCE]):
    """Default simulator."""

    def __repr__(self):
        if SIM_DEFAULT_SOURCE == "qiskit.providers.basicaer":
            return f"<QasmSimulatorPy('{self.name()}')>"
        if SIM_DEFAULT_SOURCE == "qiskit.providers.basic_provider":
            return f"<BasicSimulator('{self.name}')>"
        if isinstance(self, BackendV1):
            return f"<AerSimulator('{self.name()}')>"
        return f"<AerSimulator('{self.name}')>"


class GeneralBackend(SIM_BACKEND_SOURCES[SIM_DEFAULT_SOURCE]):
    """The abstract class of default simulator."""


class GeneralProvider(SIM_PROVIDER_SOURCES[SIM_DEFAULT_SOURCE]):
    """Provider of default backend."""

    def __repr__(self):
        if SIM_DEFAULT_SOURCE == "qiskit.providers.basicaer":
            return "<BasicAerProvider>"
        if SIM_DEFAULT_SOURCE == "qiskit.providers.basic_provider":
            return "<BasicProvider>"
        if SIM_DEFAULT_SOURCE == "qiskit_aer":
            return "<AerProvider>"
        if SIM_DEFAULT_SOURCE == "qiskit.providers.aer":
            return "<AerProviderDep>"
        return super().__repr__()