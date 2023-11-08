"""
=============================================
Aer Import Point
=============================================

For qiskit-aer has been divided into two packages since qiskit some version,
So it needs to be imported differently by trying to import qiskit-aer first,

"""
from random import random
from typing import Optional, Hashable, Union, Literal

from qiskit.providers import Backend, Provider
from qiskit.providers.fake_provider import FakeProviderForBackendV2

from .import_manage import (
    IBM_AVAILABLE, IBMQ_AVAILABLE, AER_IMPORT_POINT, backendName,
    _real_backend_loader, fack_backend_loader, shorten_name,
    IBMQ, IBMProvider, GeneralAerProvider, GeneralAerBackend,
)
from ...exceptions import QurryPositionalArgumentNotSupported
from ...capsule.hoshi import Hoshi


class BackendWrapper:
    """A wrapper for :class:`qiskit.providers.Backend` to provide more convenient way to use.


    :cls:`QasmSimulator('qasm_simulator')` and :cls:`AerSimulator('aer_simulator')` 
    are using same simulating methods.
    So call 'qasm_simulator' and 'aer_simulator' used in :meth:`Aer.get_backend` 
    are a container of multiple method of simulation
    like 'statevector', 'density_matrix', 'stabilizer' ... which is not a name of simulating method.

    - :cls:`QasmSimulator('qasm_simulator')` has:

        `(
            'automatic', 'statevector', 'density_matrix', 'stabilizer', 
            'matrix_product_state', 'extended_stabilizer'
        )`

    - :cls:`AerSimulator('aer_simulator')`  has:

        `(
            'automatic', 'statevector', 'density_matrix', 'stabilizer', 
            'matrix_product_state', 'extended_stabilizer', 'unitary', 'superop'
        )`
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

    @staticmethod
    def _hint_ibmq_sim(name: str) -> str:
        return 'ibm'+name if not 'ibm' in name else name

    def _update_callsign(self) -> None:
        self.backend_callsign = {
            **self.backend_callsign_dict['real'],
            **self.backend_callsign_dict['aer'],
            **self.backend_callsign_dict['fake'],
        }

    def _update_backend(self) -> None:
        self.backend = {
            **self.backend_dict['real'],
            **self.backend_dict['aer'],
            **self.backend_dict['fake'],
        }

    def __init__(
        self,
        real_provider: Optional[Provider] = None,
        fake_version: Union[Literal['v1', 'v2'], None] = None,
    ) -> None:

        self.is_aer_gpu = False
        self._providers: dict[Literal['aer', 'real', 'fake'], Provider] = {}
        self._providers['aer'] = GeneralAerProvider()
        self.backend_dict: dict[
            Literal['aer', 'real', 'fake'], list[Union[Backend, GeneralAerBackend]]
        ] = {}
        self.backend_callsign_dict: dict[
            Literal['aer', 'real', 'fake'], str
        ] = {}

        _aer_owned_backends: list[GeneralAerBackend] = self._providers['aer'].backends()

        if AER_IMPORT_POINT == 'qiskit.providers.basicaer':
            self.backend_callsign_dict['aer'] = {
                'state': 'statevector',
            }
            self.backend_dict['aer']: dict[str, Union[Backend, GeneralAerBackend]] = {
                shorten_name(backendName(b), ['_simulator']):
                b for b in _aer_owned_backends
            }
        else:
            if 'GPU' in _aer_owned_backends[0].available_devices():
                self.is_aer_gpu = True
            self.backend_callsign_dict['aer'] = {
                'state': 'statevector',
                'aer_state': 'aer_statevector',
                'aer_density': 'aer_density_matrix',

                'aer_state_gpu': 'aer_statevector_gpu',
                'aer_density_gpu': 'aer_density_matrix_gpu',
            }
            self.backend_dict['aer']: dict[str, Union[Backend, GeneralAerBackend]] = {
                shorten_name(backendName(b), ['_simulator']):
                    b for b in _aer_owned_backends if backendName(b) not in [
                        'qasm_simulator', 'statevector_simulator', 'unitary_simulator'
                ]
            }
        if self.is_aer_gpu:
            self.backend_dict['aer'] = {
                "aer_gpu": _aer_owned_backends[0],
                **self.backend_dict['aer'],
            }
            self.backend_dict['aer']["aer_gpu"].set_options(device='GPU')

        (
            self.backend_callsign_dict['real'], self.backend_dict['real'], self._providers['real']
        ) = _real_backend_loader(real_provider)

        (
            self.backend_callsign_dict['fake'], self.backend_dict['fake'], self._providers['fake']
        ) = fack_backend_loader(fake_version)

        self._update_callsign()
        self._update_backend()

    def __repr__(self):
        if self._providers['real'] is None:
            return '<BackendWrapper with AerProvider>'
        return f'<BackendWrapper with AerProvider and {self._providers["real"].__repr__()[1:-1]}>'

    def make_callsign(
        self,
        sign: Hashable = 'Galm 2',
        who: str = 'solo_wing_pixy',
    ) -> None:
        """Make a callsign for backend.

        Args:
            sign (Hashable, optional): The callsign.
            who (str, optional): The backend.
        """

        if sign == 'Galm 2' or who == 'solo_wing_pixy':
            if random() <= 0.2:
                print(
                    "Those who survive a long time on the battlefield " +
                    "start to think they're invincible. I bet you do, too, Buddy.")

        if who in self.backend_dict['aer']:
            self.backend_callsign_dict['aer'][sign] = who
        elif who in self.backend_dict['real']:
            self.backend_callsign_dict['real'][sign] = who
        elif who in self.backend_dict['fake']:
            self.backend_callsign_dict['fake'][sign] = who
        else:
            raise ValueError(f"'{who}' unknown backend.")

        self._update_callsign()

    @property
    def avavilable_backends(self) -> list[str]:
        """The available backends.
        """
        return list(self.backend.keys())

    @property
    def avavilable_backends_callsign(self) -> list[str]:
        """The available backends callsign.
        """
        return list(self.backend_callsign.keys())

    @property
    def available_aer(self) -> list[str]:
        """The available aer backends.
        """
        return list(self.backend_dict['aer'].keys())

    @property
    def available_aer_callsign(self) -> list[str]:
        """The available aer backends callsign.
        """
        return list(self.backend_callsign_dict['aer'].keys())

    @property
    def available_ibmq(self) -> list[str]:
        """The available ibmq/ibm backends.
        """
        return list(self.backend_dict['real'].keys())

    @property
    def available_ibmq_callsign(self) -> list[str]:
        """The available ibmq/ibm backends callsign.
        """
        return list(self.backend_callsign_dict['real'].keys())

    @property
    def available_fake(self) -> list[str]:
        """The available fake backends.
        """
        return list(self.backend_dict['fake'].keys())

    @property
    def available_fake_callsign(self) -> list[str]:
        """The available fake backends callsign.
        """
        return list(self.backend_callsign_dict['fake'].keys())

    def statesheet(self):
        """The statesheet of backend wrapper.
        """
        check_msg = Hoshi([
            ('divider', 60),
            ('h3', 'BackendWrapper Statesheet'),
        ], ljust_describe_len=35)

        for desc, backs, backs_callsign in [
            ('Aer', self.available_aer, self.backend_callsign_dict['aer']),
            ('IBM', self.available_ibmq, self.backend_callsign_dict['real']),
            ('Fake', self.available_fake, self.backend_callsign_dict['fake']),
        ]:
            check_msg.divider()
            check_msg.h4(desc)
            if 'Aer' in desc:
                check_msg.newline({
                    'type': 'itemize',
                    'description': 'Aer GPU',
                    'value': self.is_aer_gpu,
                })
            elif 'IBM' in desc:
                if IBM_AVAILABLE and IBMQ_AVAILABLE:
                    value_txt = (
                        '"qiskit_ibm_provider"' if isinstance(self._providers['real'], IBMProvider)
                        else 'qiskit.providers.ibmq')
                elif IBM_AVAILABLE:
                    value_txt = '"qiskit_ibm_provider"'
                elif IBMQ_AVAILABLE:
                    value_txt = 'qiskit.providers.ibmq'
                else:
                    value_txt = 'Not available, please install them first.'
                check_msg.newline({
                    'type': 'itemize',
                    'description': 'IBM Real Provider by',
                    'value': value_txt,
                })
            elif 'Fake' in desc:
                check_msg.newline({
                    'type': 'itemize',
                    'description': 'Fake Provider by',
                    'value': (
                        'FackBackendV2' if isinstance(self._providers['real'], FakeProviderForBackendV2)
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
        """Add a backend to backend wrapper.

        Args:
            name (str): The name of backend.
            backend (Backend): The backend.
            callsign (Hashable, optional): The callsign of backend. Defaults to None.
        """
        if name in self.backend:
            raise ValueError(f"'{name}' backend already exists.")

        self.backend_dict['real'][name] = backend
        self._update_backend()
        if not callsign is None:
            self.backend_callsign_dict['real'][callsign] = name
            self._update_callsign()

    def __call__(
        self,
        backend_name: str,
    ) -> Union[Backend, GeneralAerBackend]:
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


class BackendManager(BackendWrapper):
    """A wrapper includes accout loading and backend loading.
    And deal wtth either :module:`qiskit-ibmq-provider` 
    or the older version `qiskit.providers.ibmq`.
    """

    __version__ = '0.6.2'

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
                new_provider = IBMProvider(instance=self.instance)
                super().__init__(
                    real_provider=new_provider,
                    fake_version=fakeVersion,
                )
            else:
                print("| Provider by 'qiskit.providers.ibmq', which will be deprecated.")
                IBMQ.load_account()
                old_provider = IBMQ.get_provider(
                    hub=self.hub, group=self.group, project=self.project)
                super().__init__(
                    real_provider=old_provider,
                    fake_version=fakeVersion,
                )

        elif IBM_AVAILABLE:
            print("| Provider by 'qiskit_ibm_provider' is only available.")
            new_provider = IBMProvider(instance=self.instance)
            super().__init__(
                real_provider=new_provider,
                fake_version=fakeVersion,
            )

        elif IBMQ_AVAILABLE:
            print(
                "| Provider by 'qiskit.providers.ibmq' is only available, " +
                "which will be deprecated.")
            IBMQ.load_account()
            old_provider = IBMQ.get_provider(
                hub=self.hub, group=self.group, project=self.project)
            super().__init__(
                real_provider=old_provider,
                fake_version=fakeVersion,
            )

        else:
            print("| No IBM or IBMQ provider available.")
            super().__init__(
                real_provider=None,
                fake_version=fakeVersion,
            )

    def save_account(
        self,
        token: str,
        *args,
        useIBMProvider: bool = True,
        **kwargs
    ) -> None:
        """Save account to Qiskit.

        (The following is copied from :func:`qiskit_ibmq_provider.IBMProvider.save_account`)
        Args:
            useIBMProvider: 
                Using provider by 'qiskit_ibm_provider' instead of 'qiskit.providers.ibmq'.
            token: 
                IBM Quantum API token.
            url: The API URL.
                Defaults to https://auth.quantum-computing.ibm.com/api
            instance: 
                The hub/group/project.
            name:
                Name of the account to save.
            proxies: 
                Proxy configuration. Supported optional keys are ``urls`` 
                (a dictionary mapping protocol or protocol 
                and host to the URL of the proxy, documented at 
                https://docs.python-requests.org/en/latest/api/#requests.Session.proxies),
                ``username_ntlm``, ``password_ntlm`` (username and password to enable NTLM user
                authentication)
            verify: 
                Verify the server's TLS certificate.
            overwrite: 
                ``True`` if the existing account is to be overwritten.

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
                "| Provider by 'qiskit.providers.ibmq' is only available, " +
                "which will be deprecated.")
            IBMQ.save_account(token=token, **kwargs)

        else:
            assert False, "No IBM or IBMQ provider available."
