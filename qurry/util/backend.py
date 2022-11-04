from qiskit.version import __qiskit_version__
from qiskit.providers import Backend
from qiskit.providers.ibmq import AccountProvider
from qiskit_aer import AerProvider
from qiskit_aer.version import get_version_info as get_version_info_aer

import requests
from random import random
from typing import Optional, Hashable

from .command import cmdWrapper, pytorchCUDACheck
from ..hoshi import Hoshi


class backendWrapper:
    """The quicker method to call a backend.

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
        }

    def _update_backend(self) -> None:
        self.backend = {
            **self.backend_ibmq,
            **self.backend_aer,
        }

    def __init__(
        self,
        realProvider: Optional[AccountProvider] = None,
    ) -> None:

        try:
            package = 'qiskit'  # replace with the package you want to check
            response = requests.get(f'https://pypi.org/pypi/{package}/json')
            latest_version = response.json()['info']['version']
            latest_version_tuple = tuple(map(int, latest_version.split('.')))
            local_version = tuple(
                map(int, __qiskit_version__['qiskit'].split('.')))

            if latest_version_tuple > local_version:
                check_msg = Hoshi([
                    ('divider', 60),
                    ('h3', 'Qiskit version outdated warning'),
                    ('txt', "Please keep mind on your qiskit version, a very outdated version may cause some problems."),
                    (
                        'itemize',
                        'Local Qiskit version',
                        __qiskit_version__['qiskit'],
                        'The version on this environment.',
                    ),
                    {
                        'type': 'itemize',
                        'description': 'Latest Qiskit version',
                        'value': latest_version,
                        'hint': 'The latest version on PyPI.',
                        
                    }
                ],
                    ljust_describe_len=40,
                )
                print(check_msg)
        finally:
            ...

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
        self.backend_aer: dict[str, Backend] = {
            self._shorten_name(b.name(), ['_simulator']): b for b in self._AerOwnedBackends if b.name() not in [
                # NOTE: Deprecated backend
                'qasm_simulator', 'statevector_simulator', 'unitary_simulator'
            ]
        }
        if self.isAerGPU:
            self.backend_aer = {
                "aer_gpu": self._AerOwnedBackends[0],
                **self.backend_aer,
            }
            self.backend_aer["aer_gpu"].set_options(device='GPU')
            # for k in self.backend_sim:
            #     if 'gpu' in k:
            #         self.backend_sim[k].set_option(device='GPU')

        self.backend_ibmq_callsign = {}
        self.backend_ibmq = {}
        self._RealProvider = None
        if not realProvider is None:
            self._RealProvider = realProvider
            self.backend_ibmq = {
                b.name(): b for b in realProvider.backends()
            }
            self.backend_ibmq_callsign = {
                self._shorten_name(
                    bn, ['ibm_', 'ibmq_'], ['ibmq_qasm_simulator']
                ): bn for bn in self.backend_ibmq
            }
            self.backend_ibmq_callsign['ibmq_qasm'] = 'ibmq_qasm_simulator'

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
        else:
            raise ValueError(f"'{who}' unknown backend.")

        self._update_callsign()

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
    ) -> Backend:
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

    def aer_gpu_installed_check(self):

        print(f" - Qiskit version:")
        for k, v in __qiskit_version__.items():
            print(f"   - {k}: {v}")
        print(f" - Aer version: {get_version_info_aer()}")
        print(" - Installed state:")
        print("   - If version of 'qiskit-aer' is not same with 'qiskit-aer-gpu, it may cause GPU backend not working.'")
        print('-'*30)
        cmdWrapper("pip show qiskit")
        print('-'*30)
        cmdWrapper("pip show qiskit-aer-gpu")
        print('-'*30)
        pytorchCUDACheck()
