"""
=============================================
AerProvider, IBMProvider/IBMQProvider Import Point
=============================================

For qiskit-aer has been divided into two packages since qiskit some version,
So it needs to be imported differently by trying to import qiskit-aer first.

And qiskit-ibmq-provider has been deprecated, 
but for some user may still need to use it,
so it needs to be imported also differently by trying to import qiskit-ibm-provider first.

So this file is used to unify the import point of AerProvider, IBMProvider/IBMQProvider.
Avoiding the import error occurs on different parts of Qurry.

"""
from typing import Union, Callable, Literal, Optional, overload

import warnings
import requests
import pkg_resources

try:
    from qiskit import __version__ as __qiskit_version__
except ImportError:
    from qiskit import __qiskit_version__
from qiskit.providers import BackendV1, BackendV2, Provider
from qiskit.providers.fake_provider import (
    FakeProvider, FakeProviderForBackendV2,
    FakeBackend, FakeBackendV2)

# pylint: disable=ungrouped-imports
try:
    from qiskit_aer import (
        AerProvider as AerProviderIndep,
        AerSimulator as AerSimulatorIndep
    )
    from qiskit_aer.backends.aerbackend import AerBackend as AerBackendIndep
    from qiskit_aer.version import get_version_info as get_version_info_aer
    AER_VERSION_INFO = get_version_info_aer()
    AER_IMPORT_POINT = 'qiskit_aer'
    IS_FROM_INDEPENDENT_AER_PACKAGE = True

    class AerSimulator(AerSimulatorIndep):
        """AerSimulator from qiskit-aer package.
        """
    class AerBackend(AerBackendIndep):
        """AerBackend from qiskit-aer package.
        """

    class AerProvider(AerProviderIndep):
        """AerProvider from qiskit-aer package.
        """

except ImportError:
    from qiskit.providers.aer import (  # type: ignore
        AerProvider as AerProviderDep,  # type: ignore
        AerSimulator as AerSimulatorDep  # type: ignore
    )
    from qiskit.providers.aer.backends.aerbackend import (  # type: ignore
        AerBackend as AerBackendDep)  # type: ignore
    from qiskit.providers.aer.version import VERSION  # type: ignore
    AER_VERSION_INFO: str = VERSION
    AER_IMPORT_POINT = 'qiskit.providers.aer'
    IS_FROM_INDEPENDENT_AER_PACKAGE = False

# pylint: disable=too-few-public-methods
    class AerSimulator(AerSimulatorDep):
        """AerSimulator from qiskit.provider.aer, the old import point.
        """

    class AerBackend(AerBackendDep):
        """AerBackend from qiskit.provider.aer, the old import point.
        """

    class AerProvider(AerProviderDep):
        """AerProvider from qiskit.provider.aer, the old import point.
        """

# pylint: enable=ungrouped-imports, too-few-public-methods

from ..command import pytorchCUDACheck
from ...exceptions import QurryExtraPackageRequired
from ...capsule.hoshi import Hoshi


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
        warnings.warn(
            "The real provider is not available, please check your installation" +
            QurryExtraPackageRequired
        )

    @staticmethod
    def load_account():
        """A dummy method for :class:`qurry.tools.backend.backendWrapper`
        to use when the real provider is not available,
        And it will print a warning message when you try to use it.
        Also it is a cheatsheet for type checking in this scenario.

        """

        warnings.warn(
            "The real provider is not available, please check your installation.",
            QurryExtraPackageRequired
        )

    @staticmethod
    def get_provider():
        """A dummy method for :class:`qurry.tools.backend.backendWrapper`
        to use when the real provider is not available,
        And it will print a warning message when you try to use it.
        Also it is a cheatsheet for type checking in this scenario.

        """
        warnings.warn(
            "The real provider is not available, please check your installation.",
            QurryExtraPackageRequired
        )


try:
    from qiskit_ibm_provider import IBMProvider as IBMProviderIndep
    from qiskit_ibm_provider.version import get_version_info as get_version_info_ibm
    IBMProvider = IBMProviderIndep
    IBM_AVAILABLE = True
except ImportError:
    IBMProvider = DummyProvider

    def get_version_info_ibm():
        """A dummy method for :class:`qurry.tools.backend.backendWrapper`
        to use when the real provider is not available,
        And it will print a warning message when you try to use it.
        Also it is a cheatsheet for type checking in this scenario.

        """
        return 'Not available, please install it first.'
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

backendName: Callable[[Union[BackendV1, BackendV2]], str] = \
    lambda back: back.name if isinstance(back, BackendV2) else back.name()


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
    installed_packages = dict(pkg_resources.working_set)
    local_version_dict = {}
    for i in installed_packages:
        if i == 'qiskit':
            local_version_dict[i] = {
                'dist': pkg_resources.get_distribution(i),
                'local_version': pkg_resources.get_distribution(i).version,
            }
        elif i == 'qiskit-aer-gpu':
            local_version_dict[i] = {
                'dist': pkg_resources.get_distribution(i),
                'local_version': pkg_resources.get_distribution(i).version,
            }
        else:
            continue
    return local_version_dict


def _version_check():
    """Version check to remind user to update qiskit if needed.
    """

    check_msg = Hoshi([
        ('divider', 60),
        ('h3', 'Qiskit version outdated warning'),
        ('txt', "Please keep mind on your qiskit version, a very outdated version may cause some problems.")
    ], ljust_describe_len=40)
    local_version_dict = _local_version()
    for k, v in local_version_dict.items():
        try:
            response = requests.get(
                f'https://pypi.org/pypi/{k}/json',
                timeout=5
            )
            latest_version = response.json()['info']['version']
            latest_version_tuple = tuple(map(int, latest_version.split('.')))
            local_version_tuple = tuple(
                map(int, v['local_version'].split('.')))

            if latest_version_tuple > local_version_tuple:
                check_msg.newline({
                    'type': 'itemize',
                    'description': f'{k}',
                    'value': f"{v['local_version']}/{latest_version}",
                    'hint': 'The Local version/The Latest version on PyPI.',
                })
        except requests.exceptions.RequestException as e:
            check_msg.newline({
                'type': 'itemize',
                'description': f"Request error due to '{e}'",
                'value': None,
            })

    for k, v in __qiskit_version__.items():
        check_msg.newline({
            'type': 'itemize',
            'description': f'{k}',
            'value': str(v),
            'listing_level': 2
        })
    check_msg.newline(
        ('txt', "'qiskit-ibm-provider' is the replacement of deprcated module 'qiskit-ibmq-provider'."))
    if IBM_AVAILABLE:
        check_msg.newline({
            'type': 'itemize',
            'description': 'qiskit-ibm-provider',
            'value': get_version_info_ibm(),
        })
    else:
        check_msg.newline({
            'type': 'itemize',
            'description': 'qiskit-ibm-provider',
            'value': 'Not available, please install it first.',
        })

    if 'qiskit-aer-gpu' in local_version_dict:
        check_msg.newline(
            ('txt',
             "If version of 'qiskit-aer' is not same with 'qiskit-aer-gpu', " +
             "it may cause GPU backend not working."))
        check_msg.newline({
            'type': 'itemize',
            'description': 'qiskit-aer',
            'value': f'{AER_VERSION_INFO}, imported from {AER_IMPORT_POINT}',
        })
        check_msg.newline({
            'type': 'itemize',
            'description': 'qiskit-aer-gpu',
            'value': local_version_dict['qiskit-aer-gpu']['local_version'],
        })

    pytorchCUDACheck()

    return check_msg


def version_check():
    """Version check to remind user to update qiskit if needed.
    """
    check_msg = _version_check()
    print(check_msg)
    return check_msg


async def _async_version_check():
    """Version check to remind user to update qiskit if needed.
    """
    check_msg = _version_check()
    return check_msg


@overload
def _real_backend_loader(
    realProvider: None = None
) -> tuple[dict[str, str], dict[str, any], None]:
    ...


def _real_backend_loader(
    realProvider=None
):
    backend_ibmq_callsign = {}
    if not realProvider is None:
        _RealProvider = realProvider
        backend_ibmq = {
            backendName(b): b for b in realProvider.backends()
        }
        backend_ibmq_callsign = {
            shorten_name(
                bn, ['ibm_', 'ibmq_'], ['ibmq_qasm_simulator']
            ): bn for bn in [backs for backs in backend_ibmq if 'ibm' in backs]
        }
        backend_ibmq_callsign['ibmq_qasm'] = 'ibmq_qasm_simulator'
        return backend_ibmq_callsign, backend_ibmq, _RealProvider

    return backend_ibmq_callsign, {}, None


@overload
def fack_backend_loader(
    version: Union[Literal['v2'], str]
) -> tuple[
        dict[str, str],
        dict[str, FakeBackendV2],
        FakeProviderForBackendV2]:
    ...


@overload
def fack_backend_loader(
    version: Literal['v1']
) -> tuple[
        dict[str, str],
        dict[str, FakeBackend],
        FakeProvider]:
    ...


@overload
def fack_backend_loader(
    version: None
) -> tuple[dict[str, str], dict[str, any], None]:
    ...


def fack_backend_loader(
    version=None
):
    if version is None:
        return {}, {}, None

    _FakeProvider = FakeProvider() if version == 'v1' else FakeProviderForBackendV2()
    backend_fake = {
        backendName(b): b for b in _FakeProvider.backends()
    }
    backend_fake_callsign = {
        shorten_name(
            bn, ['_v2']
        ): bn for bn in backend_fake
    }
    backend_fake_callsign['fake_qasm'] = 'fake_qasm_simulator'
    return backend_fake_callsign, backend_fake, _FakeProvider
