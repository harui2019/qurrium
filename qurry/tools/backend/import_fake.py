"""
================================================================
Import Fake (:mod:`qurry.tools.backend.import_fake`)
================================================================

This file is used to unify the import point of FakeProvider, FakeBackend/FakeBackendV2
from qiskit.providers.fake_provider and qiskit_ibm_runtime.fake_provider.
Avoiding the import error occurs on different parts of Qurry.

"""

from typing import Literal, Type, Union, Optional, overload
import warnings

from qiskit.providers import BackendV2, BackendV1, Backend

from .utils import backend_name_getter, shorten_name
from ...exceptions import QurryDependenciesNotWorking, QurryDependenciesFailureError

# pylint: disable=ungrouped-imports
ImportPointType = Literal[
    "qiskit_ibm_runtime.fake_provider",
    "qiskit.providers.fake_provider",
]
ImportPointOrder: list[ImportPointType] = [
    "qiskit_ibm_runtime.fake_provider",
    "qiskit.providers.fake_provider",
]
FAKE_BACKEND_SOURCES: dict[ImportPointType, Optional[Type[BackendV1]]] = {}
FAKE_BACKENDV2_SOURCES: dict[ImportPointType, Optional[Type[BackendV2]]] = {}
FAKE_PROVIDER_SOURCES: dict[
    ImportPointType, Optional[Union[Type["FakeProviderDep"], Type["FakeProviderIndep"]]]
] = {}
FAKE_PROVIDERFORV2_SOURCES: dict[
    ImportPointType,
    Optional[Union[Type["FakeProviderForBackendV2Dep"], Type["FakeProviderForBackendV2Indep"]]],
] = {}
FAKE_VERSION_INFOS: dict[ImportPointType, Optional[str]] = {}
FAKE_IMPORT_ERROR_INFOS: dict[ImportPointType, ImportError] = {}

QISKIT_IBM_RUNTIME_ISSUE_1318 = (
    "The version of 'qiskit-ibm-runtime' is 0.18.0, "
    "FackBackend is not working in this version for this issue: "
    "https://github.com/Qiskit/qiskit-ibm-runtime/issues/1318."
    "You need to change the version of 'qiskit-ibm-runtime' to access FakeBackend"
)

try:
    from qiskit_ibm_runtime.fake_provider import (
        FakeProvider as FakeProviderIndep,  # type: ignore
        FakeProviderForBackendV2 as FakeProviderForBackendV2Indep,  # type: ignore
    )
    from qiskit_ibm_runtime.fake_provider.fake_backend import (  # type: ignore
        FakeBackend as FakeBackendIndep,  # type: ignore
        FakeBackendV2 as FakeBackendV2Indep,  # type: ignore
    )
    from qiskit_ibm_runtime import __version__ as qiskit_ibm_runtime_version

    FAKE_BACKEND_SOURCES["qiskit_ibm_runtime.fake_provider"] = FakeBackendIndep
    FAKE_BACKENDV2_SOURCES["qiskit_ibm_runtime.fake_provider"] = FakeBackendV2Indep
    FAKE_PROVIDER_SOURCES["qiskit_ibm_runtime.fake_provider"] = FakeProviderIndep
    FAKE_PROVIDERFORV2_SOURCES["qiskit_ibm_runtime.fake_provider"] = FakeProviderForBackendV2Indep
    FAKE_VERSION_INFOS["qiskit_ibm_runtime.fake_provider"] = qiskit_ibm_runtime_version
    if all(
        [
            qiskit_ibm_runtime_version.split(".")[1] == "18",
            qiskit_ibm_runtime_version.split(".")[2] == "0",
        ]
    ):
        warnings.warn(
            QISKIT_IBM_RUNTIME_ISSUE_1318,
            category=QurryDependenciesNotWorking,
        )

except ImportError as err:
    FAKE_IMPORT_ERROR_INFOS["qiskit_ibm_runtime.fake_provider"] = err

if len(FAKE_BACKEND_SOURCES) == 0:
    try:
        from qiskit.providers.fake_provider import (
            FakeProvider as FakeProviderDep,  # type: ignore
            FakeProviderForBackendV2 as FakeProviderForBackendV2Dep,  # type: ignore
            FakeBackend as FakeBackendDep,  # type: ignore
            FakeBackendV2 as FakeBackendV2Dep,  # type: ignore
        )
        from qiskit import __version__ as qiskit_version

        FAKE_BACKEND_SOURCES["qiskit.providers.fake_provider"] = FakeBackendDep
        FAKE_BACKENDV2_SOURCES["qiskit.providers.fake_provider"] = FakeBackendV2Dep
        FAKE_PROVIDER_SOURCES["qiskit.providers.fake_provider"] = FakeProviderDep
        FAKE_PROVIDERFORV2_SOURCES["qiskit.providers.fake_provider"] = FakeProviderForBackendV2Dep
        FAKE_VERSION_INFOS["qiskit.providers.fake_provider"] = qiskit_version

    except ImportError as err:
        FAKE_IMPORT_ERROR_INFOS["qiskit.providers.fake_provider"] = err

        FAKE_BACKEND_SOURCES["qiskit.providers.fake_provider"] = None
        FAKE_BACKENDV2_SOURCES["qiskit.providers.fake_provider"] = None
        FAKE_PROVIDER_SOURCES["qiskit.providers.fake_provider"] = None
        FAKE_PROVIDERFORV2_SOURCES["qiskit.providers.fake_provider"] = None


def get_default_fake_provider() -> Optional[ImportPointType]:
    """Get the default fake provider.

    Returns:
        ImportPointType: The default fake provider.
    """
    for source in ImportPointOrder:
        if source in FAKE_PROVIDER_SOURCES:
            return source
    return None


FAKE_DEFAULT_SOURCE: Optional[ImportPointType] = get_default_fake_provider()


LUCKY_MSG = """
No fake provider available for version conflict.
For qiskit<1.0.0 please install qiskit-ibm-runtime<0.21.0 by
'pip install qiskit-ibm-runtime<0.21.0'.
More infomation can be found in https://github.com/harui2019/qurry/wiki/Qiskit-Version-Choosing.
If you are still using qiskit 0.46.X and lower originally,
then install newer qiskit-ibm-runtime at same time,
please check whether the version of qiskit
has been updated to 1.0 by the installation
because since qiskit-ibm-runtime 0.21.0+
has been updated its dependency to qiskit 1.0.
If you already have qiskit-ibm-runtimes installed and lower than 0.21.0,
it is only available to use qiskit 0.46.X as dependency
for the migration of fake_provider is not completed around this version.
Many of the fake backends are not available in qiskit-ibm-runtime.
(This made me a lot problem to handle the fake backends in Qurry.)
(If you see this error raised, good luck to you to fix environment. :smile:.)
""".replace(
    "\n", ""
).strip()


@overload
def fack_backend_loader(
    version: Literal["v1"],
) -> tuple[
    dict[str, str],
    dict[str, Backend],
    Union["FakeProviderDep", "FakeProviderIndep"],
]: ...


@overload
def fack_backend_loader(
    version: Union[Literal["v2"], str],
) -> tuple[
    dict[str, str],
    dict[str, Backend],
    Union["FakeProviderForBackendV2Dep", "FakeProviderForBackendV2Indep"],
]: ...


@overload
def fack_backend_loader(
    version: None,
) -> tuple[dict[str, str], dict[str, Backend], None]: ...


def fack_backend_loader(version=None):
    """Load the fake backend.

    Args:
        version (str, optional): The version of fake backend. Defaults to None.
        "v1" for FakeProvider, "v2" for FakeProviderForBackendV2.

    Returns:
        tuple[dict[str, str], dict[str, Backend], Optional[Provider]]:
            The callsign of fake backend,
            the fake backend dict,
            the fake provider.
    """
    if version is None:
        return {}, {}, None

    if FAKE_DEFAULT_SOURCE is None:
        raise ImportError(LUCKY_MSG)
    _fake_provider_v1_becalled = FAKE_PROVIDER_SOURCES[FAKE_DEFAULT_SOURCE]
    _fake_provider_v2_becalled = FAKE_PROVIDERFORV2_SOURCES[FAKE_DEFAULT_SOURCE]
    assert _fake_provider_v1_becalled is not None, LUCKY_MSG
    assert _fake_provider_v2_becalled is not None, LUCKY_MSG

    try:
        _fake_provider = (
            _fake_provider_v1_becalled() if version == "v1" else _fake_provider_v2_becalled()
        )
    except FileNotFoundError as err1318:
        raise QurryDependenciesFailureError(QISKIT_IBM_RUNTIME_ISSUE_1318) from err1318

    backend_fake: dict[str, Backend] = {
        backend_name_getter(b): b for b in _fake_provider.backends()
    }
    backend_fake_callsign = {shorten_name(bn, ["_v2"]): bn for bn in backend_fake}
    backend_fake_callsign["fake_qasm"] = "fake_qasm_simulator"
    return backend_fake_callsign, backend_fake, _fake_provider
