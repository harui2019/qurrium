"""
================================================================
AerProvider, IBMProvider/IBMQProvider Import Point
(:mod:`qurry.tools.backend.import_manage`)
================================================================

For qiskit-aer has been divided into two packages since qiskit some version,
So it needs to be imported differently by trying to import qiskit-aer first.

And qiskit-ibmq-provider has been deprecated, 
but for some user may still need to use it,
so it needs to be imported also differently by trying to import qiskit-ibm-provider first.

So this file is used to unify the import point of AerProvider, IBMProvider/IBMQProvider.
Avoiding the import error occurs on different parts of Qurry.

"""

from typing import Union, Callable, Literal, Optional, overload, Type
import warnings
from importlib.metadata import distributions
import requests

from qiskit import __qiskit_version__
from qiskit.providers import BackendV1, BackendV2, Backend, Provider
from qiskit.providers.fake_provider import (
    FakeProvider,
    FakeProviderForBackendV2,
    FakeBackend,
    FakeBackendV2,
)

from ..command import pytorch_cuda_check
from ...exceptions import QurryExtraPackageRequired
from ...capsule.hoshi import Hoshi

# pylint: disable=ungrouped-imports
AerImportPointType = Literal[
    "qiskit_aer", "qiskit.providers.aer", "qiskit.providers.basicaer"
]
AER_SIMULATOR_SOURCE: dict[AerImportPointType, Type[Backend]] = {}
AER_BACKEND_SOURCE: dict[AerImportPointType, Type[Backend]] = {}
AER_PROVIDER_SOURCE: dict[AerImportPointType, Type[Provider]] = {}
try:
    try:
        from qiskit_aer import (
            AerProvider as AerProviderIndep,
            AerSimulator as AerSimulatorIndep,
        )
        from qiskit_aer.backends.aerbackend import AerBackend as AerBackendIndep
        from qiskit_aer.version import get_version_info as get_version_info_aer

        AER_VERSION_INFO = get_version_info_aer()
        AER_IMPORT_POINT: AerImportPointType = "qiskit_aer"
        IS_FROM_INDEPENDENT_AER_PACKAGE = True

        AER_SIMULATOR_SOURCE["qiskit_aer"] = AerSimulatorIndep
        AER_BACKEND_SOURCE["qiskit_aer"] = AerBackendIndep
        AER_PROVIDER_SOURCE["qiskit_aer"] = AerProviderIndep

    except ImportError:
        from qiskit.providers.aer import (  # type: ignore
            AerProvider as AerProviderDep,  # type: ignore
            AerSimulator as AerSimulatorDep,  # type: ignore
        )
        from qiskit.providers.aer.backends.aerbackend import (  # type: ignore
            AerBackend as AerBackendDep,
        )  # type: ignore
        from qiskit.providers.aer.version import VERSION  # type: ignore

        AER_VERSION_INFO: str = VERSION
        AER_IMPORT_POINT: AerImportPointType = "qiskit.providers.aer"
        IS_FROM_INDEPENDENT_AER_PACKAGE = False

        AER_SIMULATOR_SOURCE["qiskit.providers.aer"] = AerSimulatorDep
        AER_BACKEND_SOURCE["qiskit.providers.aer"] = AerBackendDep
        AER_PROVIDER_SOURCE["qiskit.providers.aer"] = AerProviderDep

except ImportError as err:
    AER_VERSION_INFO = ""
    AER_IMPORT_POINT: AerImportPointType = "qiskit.providers.basicaer"
    IS_FROM_INDEPENDENT_AER_PACKAGE = False
    from qiskit.providers.backend import BackendV1 as BackendV1Dep
    from qiskit.providers.basicaer.basicaerprovider import (
        BasicAerProvider,
        QasmSimulatorPy,
    )

    AER_SIMULATOR_SOURCE["qiskit.providers.basicaer"] = QasmSimulatorPy
    AER_BACKEND_SOURCE["qiskit.providers.basicaer"] = BackendV1Dep
    AER_PROVIDER_SOURCE["qiskit.providers.basicaer"] = BasicAerProvider

assert AER_IMPORT_POINT in AER_SIMULATOR_SOURCE, "AER_SIMULATOR_SOURCE not found"
assert AER_IMPORT_POINT in AER_BACKEND_SOURCE, "AER_BACKEND_SOURCE not found"
assert AER_IMPORT_POINT in AER_PROVIDER_SOURCE, "AER_PROVIDER_SOURCE not found"


class GeneralAerSimulator(AER_SIMULATOR_SOURCE[AER_IMPORT_POINT]):
    """AerSimulator from qiskit-aer package."""

    def __init__(self):
        if AER_IMPORT_POINT == "qiskit.providers.basicaer":
            warnings.warn(
                "Qurry uses QasmSimulatorPy as default simulator, consider to install 'qiskit-aer'."
            )
        super().__init__()

    def __repr__(self):
        if AER_IMPORT_POINT == "qiskit.providers.basicaer":
            return f"<QasmSimulatorPy({self.configuration().backend_name})>"
        return super().__repr__()


class GeneralAerBackend(AER_BACKEND_SOURCE[AER_IMPORT_POINT]):
    """AerBackend from qiskit-aer package."""


class GeneralAerProvider(AER_PROVIDER_SOURCE[AER_IMPORT_POINT]):
    """AerProvider from qiskit-aer package."""

    def __init__(self):
        if AER_IMPORT_POINT == "qiskit.providers.basicaer":
            warnings.warn(
                "Qurry uses BasicAerProvider as default provider, consider to install 'qiskit-aer'."
            )
        super().__init__()

    def __str__(self):
        if AER_IMPORT_POINT == "qiskit.providers.basicaer":
            return "BasicAerProvider"
        return super().__str__()


# pylint: enable=ungrouped-imports, too-few-public-methods


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


try:
    from qiskit_ibm_provider import IBMProvider as IBMProviderIndep
    from qiskit_ibm_provider.version import get_version_info as get_version_info_ibm

    IBMProvider = IBMProviderIndep
    IBM_AVAILABLE = True
except ImportError:
    IBMProvider = DummyProvider

    def get_version_info_ibm() -> str:
        """A dummy method for :class:`qurry.tools.backend.backendWrapper`
        to use when the real provider is not available,
        And it will print a warning message when you try to use it.
        Also it is a cheatsheet for type checking in this scenario.

        """
        return "Not available, please install it first."

    IBM_AVAILABLE = False

# pylint: disable=ungrouped-imports
try:
    from qiskit import IBMQ as IBMQ_OLD

    IBMQ = IBMQ_OLD
    IBMQ_AVAILABLE = True
except ImportError:
    IBMQ = DummyProvider
    IBM_AVAILABLE = False
# pylint: enable=ungrouped-imports

backendName: Callable[[Union[BackendV1, BackendV2, Backend]], str] = lambda back: (
    back.name
    if isinstance(back, BackendV2)
    else (back.name() if isinstance(back, BackendV1) else "unknown_backend")
)


def shorten_name(
    name: str,
    drop: Optional[list[str]] = None,
    exclude: Optional[list[str]] = None,
) -> str:
    """Shorten the name of backend.

    Args:
        name (str): The name of backend.
        drop (list[str], optional): The strings to drop from the name. Defaults to [].
        exclude (list[str], optional): The strings to exclude from the name. Defaults to [].

    Returns:
        str: The shortened name of backend.
    """
    if drop is None:
        drop = []
    if exclude is None:
        exclude = []

    if name in exclude:
        return name

    drop = sorted(drop, key=len, reverse=True)
    for _s in drop:
        if _s in name:
            return name.replace(_s, "")

    return name


def _local_version() -> dict[str, dict[str, any]]:
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

    for k, v in __qiskit_version__.items():
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
    if IBM_AVAILABLE:
        check_msg.newline(
            {
                "type": "itemize",
                "description": "qiskit-ibm-provider",
                "value": get_version_info_ibm(),
            }
        )
    else:
        check_msg.newline(
            {
                "type": "itemize",
                "description": "qiskit-ibm-provider",
                "value": "Not available, please install it first.",
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
                "value": f"{AER_VERSION_INFO}, imported from {AER_IMPORT_POINT}",
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


def _real_backend_loader(
    real_provider=None,
) -> tuple[dict[str, str], dict[str, Backend], None]:
    backend_ibmq_callsign = {}
    if not real_provider is None:
        _real_provider = real_provider
        backend_ibmq = {backendName(b): b for b in real_provider.backends()}
        backend_ibmq_callsign = {
            shorten_name(bn, ["ibm_", "ibmq_"], ["ibmq_qasm_simulator"]): bn
            for bn in [backs for backs in backend_ibmq if "ibm" in backs]
        }
        backend_ibmq_callsign["ibmq_qasm"] = "ibmq_qasm_simulator"
        return backend_ibmq_callsign, backend_ibmq, _real_provider

    return backend_ibmq_callsign, {}, None


@overload
def fack_backend_loader(
    version: Union[Literal["v2"], str]
) -> tuple[dict[str, str], dict[str, FakeBackendV2], FakeProviderForBackendV2]: ...


@overload
def fack_backend_loader(
    version: Literal["v1"],
) -> tuple[dict[str, str], dict[str, FakeBackend], FakeProvider]: ...


@overload
def fack_backend_loader(
    version: None,
) -> tuple[dict[str, str], dict[str, any], None]: ...


def fack_backend_loader(version=None):
    """Load the fake backend.

    Args:
        version (str, optional): The version of fake backend. Defaults to None.
        "v1" for FakeProvider, "v2" for FakeProviderForBackendV2.

    Returns:
        tuple[dict[str, str], dict[str, FakeBackendV2], FakeProviderForBackendV2]:
            The callsign of fake backend,
            the fake backend dict,
            the fake provider.
    """
    if version is None:
        return {}, {}, None

    _fake_provider = FakeProvider() if version == "v1" else FakeProviderForBackendV2()
    backend_fake = {backendName(b): b for b in _fake_provider.backends()}
    backend_fake_callsign = {shorten_name(bn, ["_v2"]): bn for bn in backend_fake}
    backend_fake_callsign["fake_qasm"] = "fake_qasm_simulator"
    return backend_fake_callsign, backend_fake, _fake_provider
