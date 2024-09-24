"""
================================================================
Backend Utils (:mod:`qurry.tools.backend.utils`)
================================================================

For qiskit-aer has been divided into two packages since qiskit some version,
So it needs to be imported differently by trying to import qiskit-aer first.

And qiskit-ibmq-provider has been deprecated, 
but for some user may still need to use it,
so it needs to be imported also differently by trying to import qiskit-ibm-provider first.

So this file is used to unify the import point of AerProvider, IBMProvider/IBMQProvider.
Avoiding the import error occurs on different parts of Qurry.

"""

from typing import Union, Callable, Optional

from qiskit.providers import BackendV1, BackendV2, Backend
from qiskit.providers.models.backendconfiguration import QasmBackendConfiguration


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


def backend_name_getter(back: Union[BackendV1, BackendV2, Backend, str]) -> str:
    """Get the name of backend.

    Args:
        back (Union[BackendV1, BackendV2, Backend, str]): The backend instance.

    Returns:
        str: The name of backend.
    """

    if isinstance(back, str):
        return back
    if isinstance(back, BackendV2):
        return back.name
    if isinstance(back, BackendV1):
        return back.name()
    if hasattr(back, "configuration"):
        test_call = back.configuration()  # type: ignore
        if isinstance(test_call, QasmBackendConfiguration):
            assert isinstance(
                test_call, QasmBackendConfiguration
            ), f"Invalid configuration: {test_call}"
            return test_call.backend_name
    if isinstance(back, Backend):
        return str(back)
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
