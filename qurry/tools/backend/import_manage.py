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

from typing import Union, Callable, Literal, Optional, overload
from importlib.metadata import distributions
import requests

from qiskit import __qiskit_version__
from qiskit.providers import BackendV1, BackendV2, Backend
from qiskit.providers.fake_provider import (
    FakeProvider,
    FakeProviderForBackendV2,
    FakeBackend,
    FakeBackendV2,
)
from qiskit.providers.models import QasmBackendConfiguration

from .import_ibm import (
    VERSION_INFOS as real_version_infos,
    DEFAULT_SOURCE as real_default_source,
    RealProviderType,
)
from .import_simulator import (
    VERSION_INFOS as sim_version_infos,
    DEFAULT_SOURCE as sim_default_source,
)
from ..command import pytorch_cuda_check
from ...capsule.hoshi import Hoshi


backendName: Callable[[Union[BackendV1, BackendV2, Backend]], str] = lambda back: (
    back.name
    if isinstance(back, BackendV2)
    else (back.name() if isinstance(back, BackendV1) else "unknown_backend")
)
"""Get the name of backend.

Args:
    back (Union[BackendV1, BackendV2, Backend]): The backend instance.
    
Returns:
    str: The name of backend.
"""


def backend_name_getter(back: Union[BackendV1, BackendV2, Backend]) -> str:
    """Get the name of backend.

    Args:
        back (Union[BackendV1, BackendV2, Backend]): The backend instance.

    Returns:
        str: The name of backend.
    """
    if hasattr(back, "configuration"):
        config: QasmBackendConfiguration = back.configuration()  # type: ignore
        assert isinstance(config, QasmBackendConfiguration), "Invalid configuration"
        return config.backend_name
    if isinstance(back, BackendV2):
        return back.name
    if isinstance(back, BackendV1):
        return back.name()
    return "unknown_backend"


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
    check_msg.newline(
        {
            "type": "itemize",
            "description": (
                real_default_source if real_default_source else "qiskit_ibm_provider"
            ),
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
                "value": f"{sim_version_infos[sim_default_source]}, imported from '{sim_default_source}'",
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


@overload
def real_backend_loader(
    real_provider=None,
) -> tuple[dict[str, str], dict[str, Backend], None]: ...


@overload
def real_backend_loader(
    real_provider: RealProviderType,
) -> tuple[dict[str, str], dict[str, Backend], RealProviderType]: ...


def real_backend_loader(real_provider=None):
    """Load the real backend.

    Args:
        real_provider (Optional[RealProviderType], optional):
            The real provider. Defaults to None.

    Returns:
        tuple[dict[str, str], dict[str, Backend], Optional[RealProviderType]]:
            The callsign of real backend,
            the real backend dict,
            the real provider.
    """
    if not real_provider is None:
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
