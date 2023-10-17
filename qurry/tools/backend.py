"""
=============================================
Aer Import Point
=============================================

For qiskit-aer has been divided into two packages since qiskit some version,
So it needs to be imported differently by trying to import qiskit-aer first,

"""

from qiskit import __qiskit_version__
from qiskit.providers import Backend, BackendV1, BackendV2, Provider
from qiskit.providers.fake_provider import (
    FakeProvider, FakeProviderForBackendV2,
    FakeBackend, FakeBackendV2)

try:
    from qiskit_aer import AerProvider
    from qiskit_aer.backends.aerbackend import AerBackend
    from qiskit_aer.version import get_version_info as get_version_info_aer
    aer_version_info = get_version_info_aer()
    aer_import_point = 'qiskit_aer'
except ImportError:
    from qiskit.providers.aer import AerProvider
    from qiskit.providers.aer.backends.aerbackend import AerBackend
    from qiskit.providers.aer.version import VERSION
    aer_version_info = VERSION
    aer_import_point = 'qiskit.providers.aer'

import requests
import pkg_resources
import warnings
from random import random
from typing import Optional, Hashable, Union, overload, Callable, Literal

from .command import pytorchCUDACheck
from ..exceptions import (
    QurryExtraPackageRequired,
    QurryPositionalArgumentNotSupported,
)
from ..capsule.hoshi import Hoshi


class DummyProvider(Provider):
    """A dummy provider for :class:`qurry.tools.backend.backendWrapper` to use when the real provider is not available,
    And it will print a warning message when you try to use it. 
    Also it is a cheatsheet for type checking in this scenario.

    """

    @staticmethod
    def save_account(**kwargs):
        warnings.warn(
            "The real provider is not available, please check your installation.",
            QurryExtraPackageRequired
        )

    @staticmethod
    def load_account(**kwargs):
        warnings.warn(
            "The real provider is not available, please check your installation.",
            QurryExtraPackageRequired
        )

    @staticmethod
    def get_provider():
        warnings.warn(
            "The real provider is not available, please check your installation.",
            QurryExtraPackageRequired
        )


try:
    from qiskit_ibm_provider import IBMProvider
    from qiskit_ibm_provider.version import get_version_info as get_version_info_ibm
    IBM_AVAILABLE = True
except ImportError:
    IBMProvider = DummyProvider
    def get_version_info_ibm(): return 'Not available, please install it first.'
    IBM_AVAILABLE = False

try:
    from qiskit import IBMQ
    IBMQ_AVAILABLE = True
except ImportError:
    IBMQ = DummyProvider
    IBM_AVAILABLE = False


backendName: Callable[[Union[BackendV1, BackendV2]], str] = \
    lambda back: back.name if isinstance(back, BackendV2) else back.name()


def _local_version() -> dict[str, dict[str, any]]:
    installed_packages = pkg_resources.working_set
    local_version_dict = {}
    for i in installed_packages:
        if i.key == 'qiskit':
            local_version_dict[i.key] = {
                'dist': i,
                'local_version': i.version,
            }
        elif i.key == 'qiskit-aer-gpu':
            local_version_dict[i.key] = {
                'dist': i,
                'local_version': i.version,
            }
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
            response = requests.get(f'https://pypi.org/pypi/{k}/json')
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
        except Exception as e:
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
            ('txt', "If version of 'qiskit-aer' is not same with 'qiskit-aer-gpu', it may cause GPU backend not working."))
        check_msg.newline({
            'type': 'itemize',
            'description': 'qiskit-aer',
            'value': '{}, imported from {}'.format(
                aer_version_info, aer_import_point),
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
            backendWrapper._shorten_name(
                bn, ['ibm_', 'ibmq_'], ['ibmq_qasm_simulator']
            ): bn for bn in [backs for backs in backend_ibmq if 'ibm' in backs]
        }
        backend_ibmq_callsign['ibmq_qasm'] = 'ibmq_qasm_simulator'
        return backend_ibmq_callsign, backend_ibmq, _RealProvider
    else:
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
        backendWrapper._shorten_name(
            bn, ['_v2']
        ): bn for bn in backend_fake
    }
    backend_fake_callsign['fake_qasm'] = 'fake_qasm_simulator'
    return backend_fake_callsign, backend_fake, _FakeProvider


class backendWrapper:
    """A wrapper for :class:`qiskit.providers.Backend` to provide more convenient way to use.


    :cls:`QasmSimulator('qasm_simulator')` and :cls:`AerSimulator('aer_simulator')` are using same simulating methods.
    So call 'qasm_simulator' and 'aer_simulator' used in :meth:`Aer.get_backend` are a container of multiple method of simulation
    like 'statevector', 'density_matrix', 'stabilizer' ... which is not a name of simulating method.

    - :cls:`QasmSimulator('qasm_simulator')` has:

        `('automatic', 'statevector', 'density_matrix', 'stabilizer', 'matrix_product_state', 'extended_stabilizer')`

    - :cls:`AerSimulator('aer_simulator')`  has:

        `('automatic', 'statevector', 'density_matrix', 'stabilizer', 'matrix_product_state', 'extended_stabilizer', 'unitary', 'superop')`
        Even parts of method has GPU support by :module:`qiskit-aer-gpu`

    ```txt
    +--------------------------+---------------+
    | Method                   | GPU Supported |
    +==========================+===============+
    | ``automatic``            | Sometimes     |
    +--------------------------+---------------+
    | ``statevector``          | Yes           |
    +--------------------------+---------------+
    | ``density_matrix``       | Yes           |
    +--------------------------+---------------+
    | ``stabilizer``           | No            |
    +--------------------------+---------------+
    | ``matrix_product_state`` | No            |
    +--------------------------+---------------+
    | ``extended_stabilizer``  | No            |
    +--------------------------+---------------+
    | ``unitary``              | Yes           |
    +--------------------------+---------------+
    | ``superop``              | No            |
    +--------------------------+---------------+
    ```
    (from doc of :cls:`AerSimulator`)

    So this wrapper only call :cls:`AerSimulator('aer_simulator')` as simulator backend,
    and use :meth:`set_option` to get different backends.

    """

    isAerGPU = False

    @staticmethod
    def _shorten_name(
        name: str,
        drop: list[str] = [],
        exclude: list[str] = [],
    ) -> str:
        if name in exclude:
            return name

        drop = sorted(drop, key=len, reverse=True)
        for _s in drop:
            if _s in name:
                return name.replace(_s, "")

        return name

    @staticmethod
    def _hint_ibmq_sim(name: str) -> str:
        return 'ibm'+name if not 'ibm' in name else name

    def _update_callsign(self) -> None:
        self.backend_callsign = {
            **self.backend_ibmq_callsign,
            **self.backend_aer_callsign,
            **self.backend_fake_callsign,
        }

    def _update_backend(self) -> None:
        self.backend = {
            **self.backend_ibmq,
            **self.backend_aer,
            **self.backend_fake,
        }

    def __init__(
        self,
        realProvider: Optional[Provider] = None,
        fakeVersion: Union[Literal['v1', 'v2'], None] = None,
    ) -> None:

        self._AerProvider = AerProvider()
        self._AerOwnedBackends = self._AerProvider.backends()
        if 'GPU' in self._AerOwnedBackends[0].available_devices():
            self.isAerGPU = True

        self.backend_aer_callsign = {
            'state': 'statevector',
            'aer_state': 'aer_statevector',
            'aer_density': 'aer_density_matrix',

            'aer_state_gpu': 'aer_statevector_gpu',
            'aer_density_gpu': 'aer_density_matrix_gpu',
        }
        self.backend_aer: dict[str, Union[Backend, AerBackend]] = {
            self._shorten_name(backendName(b), ['_simulator']): b for b in self._AerOwnedBackends if backendName(b) not in [
                'qasm_simulator', 'statevector_simulator', 'unitary_simulator'
            ]
        }
        if self.isAerGPU:
            self.backend_aer = {
                "aer_gpu": self._AerOwnedBackends[0],
                **self.backend_aer,
            }
            self.backend_aer["aer_gpu"].set_options(device='GPU')

        (
            self.backend_ibmq_callsign, self.backend_ibmq, self._RealProvider
        ) = _real_backend_loader(realProvider)

        (
            self.backend_fake_callsign, self.backend_fake, self._FakeProvider
        ) = fack_backend_loader(fakeVersion)

        self._update_callsign()
        self._update_backend()

    def __repr__(self):
        if self._RealProvider is None:
            return f'<BackendWrapper with AerProvider>'
        else:
            return f'<BackendWrapper with AerProvider and {self._RealProvider.__repr__()[1:-1]}>'

    def make_callsign(
        self,
        sign: Hashable = 'Galm 2',
        who: str = 'solo_wing_pixy',
    ) -> None:

        if sign == 'Galm 2' or who == 'solo_wing_pixy':
            if random() <= 0.2:
                print(
                    "Those who survive a long time on the battlefield start to think they're invincible. I bet you do, too, Buddy.")

        if who in self.backend_aer:
            self.backend_aer_callsign[sign] = who
        elif who in self.backend_ibmq:
            self.backend_ibmq_callsign[sign] = who
        elif who in self.backend_fake:
            self.backend_fake_callsign[sign] = who
        else:
            raise ValueError(f"'{who}' unknown backend.")

        self._update_callsign()

    @property
    def avavilable_backends(self) -> list[str]:
        return list(self.backend.keys())

    @property
    def avavilable_backends_callsign(self) -> list[str]:
        return list(self.backend_callsign.keys())

    @property
    def available_aer(self) -> list[str]:
        return list(self.backend_aer.keys())

    @property
    def available_aer_callsign(self) -> list[str]:
        return list(self.backend_aer_callsign.keys())

    @property
    def available_ibmq(self) -> list[str]:
        return list(self.backend_ibmq.keys())

    @property
    def available_ibmq_callsign(self) -> list[str]:
        return list(self.backend_ibmq_callsign.keys())

    @property
    def available_fake(self) -> list[str]:
        return list(self.backend_fake.keys())

    @property
    def available_fake_callsign(self) -> list[str]:
        return list(self.backend_fake_callsign.keys())

    def statesheet(self):
        check_msg = Hoshi([
            ('divider', 60),
            ('h3', 'BackendWrapper Statesheet'),
        ], ljust_describe_len=35)

        for desc, backs, backs_callsign in [
            ('Aer', self.available_aer, self.backend_aer_callsign),
            ('IBM', self.available_ibmq, self.backend_ibmq_callsign),
            ('Fake', self.available_fake, self.backend_fake_callsign),
        ]:
            check_msg.divider()
            check_msg.h4(desc)
            if 'Aer' in desc:
                check_msg.newline({
                    'type': 'itemize',
                    'description': f'Aer GPU',
                    'value': self.isAerGPU,
                })
            elif 'IBM' in desc:
                if IBM_AVAILABLE and IBMQ_AVAILABLE:
                    value_txt = (
                        '"qiskit_ibm_provider"' if isinstance(self._RealProvider, IBMProvider)
                        else 'qiskit.providers.ibmq')
                elif IBM_AVAILABLE:
                    value_txt = '"qiskit_ibm_provider"'
                elif IBMQ_AVAILABLE:
                    value_txt = 'qiskit.providers.ibmq'
                else:
                    value_txt = 'Not available, please install them first.'
                check_msg.newline({
                    'type': 'itemize',
                    'description': f'IBM Real Provider by',
                    'value': value_txt,
                })
            elif 'Fake' in desc:
                check_msg.newline({
                    'type': 'itemize',
                    'description': f'Fake Provider by',
                    'value': (
                        'FackBackendV2' if isinstance(self._FakeProvider, FakeProviderForBackendV2)
                        else 'FackBackendV1'),
                })
            check_msg.newline({
                'type': 'itemize',
                'description': f'Available {desc} Backends',
                # 'value': backs,
            })
            backs_len = len(backs)
            for i in range(0, backs_len, 3):
                tmp_backs = backs[i:i+3]
                tmp_backs_str = ', '.join(tmp_backs) + (
                    ',' if len(tmp_backs) == 3 else ''
                )
                check_msg.newline({
                    'type': 'txt',
                    'listing_level': 2,
                    'text': tmp_backs_str,
                })

            check_msg.newline({
                'type': 'itemize',
                'description': f'Available {desc} Backends Callsign',
            })
            for k, v in backs_callsign.items():
                check_msg.newline({
                    'type': 'itemize',
                    'description': f' callsign: {k}',
                    'value': f'for: {v}',
                    'listing_level': 2,
                })

        return check_msg

    def add_backend(
        self,
        name: str,
        backend: Backend,
        callsign: Hashable = None,
    ) -> None:
        self.backend_ibmq[name] = backend
        self._update_backend()
        if not callsign is None:
            self.backend_ibmq_callsign[callsign] = name
            self._update_callsign()

    def __call__(
        self,
        backend_name: str,
    ) -> Union[Backend, AerBackend]:
        # if 'qasm' in backend_name:
        #     warnings.warn(
        #         "We use 'AerSimulator' as replacement of 'QASMSimulator' "+
        #         "due to they are the same things, "+
        #         "more info checks the doc of 'backendWrapper'."
        #     )
        #     backend_name = 'aer'
        if backend_name in self.backend_callsign:
            backend_name = self.backend_callsign[backend_name]
        elif backend_name in self.backend:
            ...
        else:
            raise ValueError(
                f"'{backend_name}' unknown backend or backend callsign.")

        return self.backend[backend_name]


class backendManager(backendWrapper):
    __version__ = '0.6.2'

    """A wrapper includes accout loading and backend loading.
    And deal wtth either :module:`qiskit-ibmq-provider` or the older version `qiskit.providers.ibmq`."""

    def __init__(
        self,
        hub: Optional[str] = None,
        group: Optional[str] = None,
        project: Optional[str] = None,

        instance: Optional[str] = None,

        useIBMProvider: bool = True,
        fakeVersion: Union[Literal['v1', 'v2'], None] = None,
    ) -> None:

        if instance is not None:
            self.instance = instance
            self.hub, self.group, self.project = instance.split('/')
        else:
            for name in [hub, group, project]:
                if name is None:
                    raise ValueError(
                        "Please provide either instance or hub, group, project.")
            self.instance = f'{hub}/{group}/{project}'
            self.hub = hub
            self.group = group
            self.project = project

        if IBM_AVAILABLE and IBMQ_AVAILABLE:
            if useIBMProvider:
                print("| Provider by 'qiskit_ibm_provider'.")
                newProvider = IBMProvider(instance=self.instance)
                super().__init__(
                    realProvider=newProvider,
                    fakeVersion=fakeVersion,
                )
            else:
                print("| Provider by 'qiskit.providers.ibmq', which will be deprecated.")
                IBMQ.load_account()
                oldProvider = IBMQ.get_provider(
                    hub=self.hub, group=self.group, project=self.project)
                super().__init__(
                    realProvider=oldProvider,
                    fakeVersion=fakeVersion,
                )

        elif IBM_AVAILABLE:
            print("| Provider by 'qiskit_ibm_provider' is only available.")
            newProvider = IBMProvider(instance=self.instance)
            super().__init__(
                realProvider=newProvider,
                fakeVersion=fakeVersion,
            )

        elif IBMQ_AVAILABLE:
            print(
                "| Provider by 'qiskit.providers.ibmq' is only available, which will be deprecated.")
            IBMQ.load_account()
            oldProvider = IBMQ.get_provider(
                hub=self.hub, group=self.group, project=self.project)
            super().__init__(
                realProvider=oldProvider,
                fakeVersion=fakeVersion,
            )

        else:
            print("| No IBM or IBMQ provider available.")
            super().__init__(
                realProvider=None,
                fakeVersion=fakeVersion,
            )

    def save_account(
        self,
        token: str,
        *args,
        useIBMProvider: bool = True,
        **kwargs
    ) -> None:
        """Save account to disk.

        (The following is copied from :func:`qiskit_ibmq_provider.IBMProvider.save_account`)
        Args:
            useIBMProvider: Using provider by 'qiskit_ibm_provider' instead of 'qiskit.providers.ibmq'.
            token: IBM Quantum API token.
            url: The API URL.
                Defaults to https://auth.quantum-computing.ibm.com/api
            instance: The hub/group/project.
            name: Name of the account to save.
            proxies: Proxy configuration. Supported optional keys are
                ``urls`` (a dictionary mapping protocol or protocol and host to the URL of the proxy,
                documented at https://docs.python-requests.org/en/latest/api/#requests.Session.proxies),
                ``username_ntlm``, ``password_ntlm`` (username and password to enable NTLM user
                authentication)
            verify: Verify the server's TLS certificate.
            overwrite: ``True`` if the existing account is to be overwritten.

        """
        if len(args) > 0:
            raise QurryPositionalArgumentNotSupported(
                "Please use keyword arguments to provide the parameters, " +
                "For example: `.save_account(token='your_token')`")

        if IBM_AVAILABLE and IBMQ_AVAILABLE:
            if useIBMProvider:
                IBMProvider.save_account(token=token, **kwargs)
            else:
                IBMQ.save_account(token=token, **kwargs)

        elif IBM_AVAILABLE:
            print("| Provider by 'qiskit_ibm_provider' is only available.")
            IBMProvider.save_account(token=token, **kwargs)

        elif IBMQ_AVAILABLE:
            print(
                "| Provider by 'qiskit.providers.ibmq' is only available, which will be deprecated.")
            IBMQ.save_account(token=token, **kwargs)
            
        else:
            assert False, "No IBM or IBMQ provider available."
