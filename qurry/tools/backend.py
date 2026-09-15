"""Backend Utilities and Simulator (:mod:`qurry.tools.backend`)

This module provides the default simulator for Qurrium.
For the simulator, the following sources are considered:

- qiskit_aer
- qiskit.providers.aer
- qiskit.providers.basicaer
- qiskit.providers.basic_provider

which are used in different qiskit, qiskit-aer version,
and ordered by priority.
"""

from typing import Literal, Any
from collections.abc import Callable

from qiskit.providers import BackendV2, Backend


# pylint: disable=ungrouped-imports
ImportPointType = Literal[
    "qiskit_aer",
    "qiskit.providers.aer",
    "qiskit.providers.basicaer",
    "qiskit.providers.basic_provider",
]
IMPORT_POINT_ORDER = [
    "qiskit_aer",
    "qiskit.providers.basic_provider",
    "qiskit.providers.basicaer",
    "qiskit.providers.aer",
]
SIMULATOR_SOURCES: dict[ImportPointType, type[Backend]] = {}
SIM_BACKEND_SOURCES: dict[ImportPointType, type[Backend]] = {}
SIM_PROVIDER_SOURCES: dict[ImportPointType, type[Any]] = {}
SIM_VERSION_INFOS: dict[ImportPointType, str | None] = {}
SIM_IMPORT_ERROR_INFOS: dict[ImportPointType, ImportError] = {}

try:
    from qiskit_aer import AerProvider, AerSimulator  # type: ignore
    from qiskit_aer.backends.aerbackend import AerBackend  # type: ignore
    from qiskit_aer.version import get_version_info as get_version_info_aer  # type: ignore

    SIM_VERSION_INFOS["qiskit_aer"] = get_version_info_aer()
    SIMULATOR_SOURCES["qiskit_aer"] = AerSimulator
    SIM_BACKEND_SOURCES["qiskit_aer"] = AerBackend
    SIM_PROVIDER_SOURCES["qiskit_aer"] = AerProvider  # type: ignore
    # wtf, AerProvider is not inherited from Provider for qiskit-aer 0.15.0
except ImportError as err:
    SIM_IMPORT_ERROR_INFOS["qiskit_aer"] = err

try:
    from qiskit.providers.basic_provider import BasicSimulator, BasicProvider  # type: ignore
    from qiskit import __version__ as qiskit_version  # type: ignore

    SIM_VERSION_INFOS["qiskit.providers.basic_provider"] = qiskit_version
    SIMULATOR_SOURCES["qiskit.providers.basic_provider"] = BasicSimulator
    SIM_BACKEND_SOURCES["qiskit.providers.basic_provider"] = BackendV2
    SIM_PROVIDER_SOURCES["qiskit.providers.basic_provider"] = BasicProvider
except ImportError as err:
    SIM_IMPORT_ERROR_INFOS["qiskit.providers.basic_provider"] = err

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
    from qiskit.providers.basicaer.basicaerprovider import (  # type: ignore
        BasicAerProvider,
        QasmSimulatorPy,
    )
    from qiskit import __version__ as qiskit_version  # type: ignore

    SIM_VERSION_INFOS["qiskit.providers.basicaer"] = qiskit_version
    SIMULATOR_SOURCES["qiskit.providers.basicaer"] = QasmSimulatorPy
    SIM_BACKEND_SOURCES["qiskit.providers.basicaer"] = Backend
    SIM_PROVIDER_SOURCES["qiskit.providers.basicaer"] = BasicAerProvider
except ImportError as err:
    SIM_IMPORT_ERROR_INFOS["qiskit.providers.basicaer"] = err


def backend_name_getter(back: BackendV2 | Backend | str) -> str:
    """Get the name of backend.

    Args:
        back (BackendV2 | Backend | str): The backend instance.
    Returns:
        str: The name of backend.
    """

    if isinstance(back, str):
        return back
    if isinstance(back, BackendV2):
        return back.name
    if isinstance(back, Callable):
        return back.name()  # type: ignore
    if isinstance(back, Backend):
        return str(back)
    return "unknown_backend"


def get_default_sim_source() -> ImportPointType:
    """Get the default source for the simulator.

    Returns:
        ImportPointType: The default source for the simulator.

    Raises:
        ImportError: If no available simulator source is found.
    """

    for source in IMPORT_POINT_ORDER:
        if source in SIMULATOR_SOURCES:
            return source
    raise ImportError("No available simulator source, please check the installation of qiskit.")


SIM_DEFAULT_SOURCE: ImportPointType = get_default_sim_source()


# pylint: disable=too-few-public-methods
class GeneralSimulator(SIMULATOR_SOURCES[SIM_DEFAULT_SOURCE]):
    """Default simulator."""

    def __repr__(self):
        if SIM_DEFAULT_SOURCE == "qiskit.providers.basicaer":
            return f"<QasmSimulatorPy('{backend_name_getter(self)}')>"
        if SIM_DEFAULT_SOURCE == "qiskit.providers.basic_provider":
            return f"<BasicSimulator('{backend_name_getter(self)}')>"
        if SIM_DEFAULT_SOURCE == "qiskit_aer":
            return f"<AerSimulator('{backend_name_getter(self)}')>"
        return f"<UnknownSimulator('{backend_name_getter(self)}')>"


class GeneralBackend(SIM_BACKEND_SOURCES[SIM_DEFAULT_SOURCE]):
    """The abstract class of default simulator."""
