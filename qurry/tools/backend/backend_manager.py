"""
=============================================
Aer Import Point
=============================================

For qiskit-aer has been divided into two packages since qiskit some version,
So it needs to be imported differently by trying to import qiskit-aer first,

"""

from random import random
from typing import Optional, Union, Literal, TypedDict

from qiskit.providers import Backend, Provider
from qiskit.providers.fake_provider import (
    FakeProvider,
    FakeProviderForBackendV2,
    FakeBackend,
    FakeBackendV2,
)

from .import_manage import (
    backend_name_getter,
    real_backend_loader,
    fack_backend_loader,
    shorten_name,
)
from .import_simulator import (
    GeneralBackend,
    GeneralProvider,
    DEFAULT_SOURCE as sim_default_source,
)
from .import_ibm import (
    DEFAULT_SOURCE as real_default_source,
    ImportPointType as RealImportPointType,
)
from ...exceptions import QurryPositionalArgumentNotSupported
from ...capsule.hoshi import Hoshi


BackendDict = dict[
    Union[Literal["real", "sim", "fake", "extra"], str],
    dict[str, Union[Backend, GeneralBackend, FakeBackend, FakeBackendV2, any]],
]
"""The dict of backend."""


BackendCallSignDict = dict[
    Union[Literal["real", "sim", "fake", "extra"], str],
    dict[str, str],
]
"""The dict of backend callsign."""


class ProviderDict(TypedDict):
    """The dict of provider."""

    real: Union[Provider, None]
    sim: GeneralProvider
    fake: Union[FakeProvider, FakeProviderForBackendV2, None]


def _statesheet_preparings(
    check_msg: Hoshi,
    desc: str,
    backs: list[str],
    backs_callsign: dict[str, str],
    is_aer_gpu: bool,
    fake_provider: Union[FakeProvider, FakeProviderForBackendV2, None],
):
    backs_len = len(backs)
    check_msg.divider()
    check_msg.h4(desc)
    if "Simulator" in desc:
        check_msg.newline(
            {
                "type": "itemize",
                "description": "Aer GPU",
                "value": is_aer_gpu,
                "ljust_description_filler": ".",
            }
        )
        check_msg.newline(
            {
                "type": "itemize",
                "description": "Simulator Provider by",
                "value": sim_default_source,
                "ljust_description_filler": ".",
            }
        )
    elif "IBM" in desc:
        if len(backs) > 0:
            check_msg.newline(
                {
                    "type": "itemize",
                    "description": "IBM Real Provider by",
                    "value": (
                        real_default_source
                        if real_default_source
                        else "Not available, please install them first."
                    ),
                    "ljust_description_filler": ".",
                }
            )
    elif "Fake" in desc:
        if fake_provider:
            check_msg.newline(
                {
                    "type": "itemize",
                    "description": "Fake Provider by",
                    "value": (
                        "FackBackendV2"
                        if isinstance(fake_provider, FakeProviderForBackendV2)
                        else "FackBackendV1"
                    ),
                    "ljust_description_filler": ".",
                }
            )
        check_msg.newline(
            {
                "type": "itemize",
                "description": f"Available {desc} Backends",
                # 'value': backs,
            }
        )
    if backs_len == 0:
        check_msg.newline(
            {
                "type": "txt",
                "listing_level": 2,
                "text": (
                    "No Backends Available."
                    + (
                        " Choose fake version when initializing the backend wrapper."
                        if "Fake" in desc
                        else ""
                    )
                    + (
                        (
                            " Real backends need to be loaded by 'BackendManager' "
                            + "instead of 'BackendWrapper'."
                        )
                        if "IBM" in desc
                        else ""
                    )
                ),
            }
        )
    else:
        for i in range(0, backs_len, 3):
            tmp_backs = backs[i : i + 3]
            tmp_backs_str = ", ".join(tmp_backs) + ("," if len(tmp_backs) == 3 else "")
            check_msg.newline(
                {
                    "type": "txt",
                    "listing_level": 2,
                    "text": tmp_backs_str,
                }
            )

    if len(backs_callsign) == 0:
        check_msg.newline(
            {
                "type": "txt",
                "listing_level": 2,
                "text": "No Callsign Added",
            }
        )
    else:
        check_msg.newline(
            {
                "type": "itemize",
                "description": f"Available {desc} Backends Callsign",
            }
        )
        for k, v in backs_callsign.items():
            check_msg.newline(
                {
                    "type": "itemize",
                    "description": f"{k}",
                    "value": f"{v}",
                    "listing_level": 2,
                    "ljust_description_filler": ".",
                }
            )


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

    So this wrapper only call :cls:`AerSimulator('aer_simulator')` as simulator backend,
    and use :meth:`set_option` to get different backends.

    """

    @staticmethod
    def _hint_ibmq_sim(name: str) -> str:
        return "ibm" + name if not "ibm" in name else name

    def __init__(
        self,
        real_provider: Optional[Provider] = None,
        fake_version: Union[Literal["v1", "v2"], None] = None,
    ) -> None:
        self.is_aer_gpu = False
        self._providers: ProviderDict = {
            "sim": GeneralProvider(),
            "real": None,
            "fake": None,
        }
        self.backend_dict: BackendDict = {
            "sim": {},
            "real": {},
            "fake": {},
            "extra": {},
        }
        self.backend_callsign_dict: BackendCallSignDict = {
            "sim": {},
            "real": {},
            "fake": {},
            "extra": {},
        }

        assert self._providers["sim"] is not None
        _sim_backends: list[GeneralBackend] = self._providers["sim"].backends()

        if sim_default_source == "qiskit.providers.basicaer":
            self.backend_callsign_dict["sim"] = {
                "state": "statevector",
            }
            self.backend_dict["sim"] = {
                shorten_name(backend_name_getter(b), ["_simulator"]): b
                for b in _sim_backends
            }
        else:
            if hasattr(_sim_backends[0], "available_devices"):
                self.is_aer_gpu = "GPU" in _sim_backends[0].available_devices()
            else:
                self.is_aer_gpu = False

            self.backend_callsign_dict["sim"] = {
                "state": "statevector",
                "aer_state": "aer_statevector",
                "aer_density": "aer_density_matrix",
                "aer_state_gpu": "aer_statevector_gpu",
                "aer_density_gpu": "aer_density_matrix_gpu",
            }
            self.backend_dict["sim"] = {
                shorten_name(backend_name_getter(b), ["_simulator"]): b
                for b in _sim_backends
                if backend_name_getter(b)
                not in ["qasm_simulator", "statevector_simulator", "unitary_simulator"]
            }
        if self.is_aer_gpu:
            _aer_gpu_backend = _sim_backends[0]
            _aer_gpu_backend.set_options(device="GPU")
            assert _aer_gpu_backend.options.device == "GPU", "GPU not available."
            self.backend_dict["sim"] = {
                "aer_gpu": _aer_gpu_backend,
                **self.backend_dict["sim"],
            }

        (
            self.backend_callsign_dict["real"],
            self.backend_dict["real"],
            self._providers["real"],
        ) = real_backend_loader(real_provider)

        (
            self.backend_callsign_dict["fake"],
            self.backend_dict["fake"],
            self._providers["fake"],
        ) = fack_backend_loader(fake_version)

    def __repr__(self):
        repr_str = f"<{self.__class__.__name__}("
        repr_str += f'sim="{sim_default_source}", '
        fakeprovider_repr = (
            (
                "FakeProviderV2"
                if isinstance(self._providers["fake"], FakeProviderForBackendV2)
                else "FakeProvider"
            )
            if self._providers["fake"]
            else None
        )
        repr_str += f'fake="{fakeprovider_repr}"'
        repr_str += ")>"
        return repr_str

    def make_callsign(
        self,
        sign: str = "Galm 2",
        who: str = "solo_wing_pixy",
    ) -> None:
        """Make a callsign for backend.

        Args:
            sign (str, optional): The callsign.
            who (str, optional): The backend.

        Raises:
            ValueError: If the callsign already exists.
            ValueError: If the backend is unknown.
        """

        if sign == "Galm 2" or who == "solo_wing_pixy":
            if random() <= 0.2:
                print(
                    "Those who survive a long time on the battlefield "
                    + "start to think they're invincible. I bet you do, too, Buddy."
                )
        for avaiable_type in ["real", "sim", "fake", "extra"]:
            if sign in self.backend_callsign_dict[avaiable_type]:
                raise ValueError(f"'{sign}' callsign already exists.")
        for avaiable_type in ["real", "sim", "fake", "extra"]:
            if who in self.backend_dict[avaiable_type]:
                self.backend_callsign_dict[avaiable_type][sign] = who
                return
        raise ValueError(f"'{who}' unknown backend.")

    @property
    def available_backends(self) -> BackendDict:
        """The available backends."""
        return self.backend_dict

    @property
    def available_backends_callsign(self) -> BackendCallSignDict:
        """The available backends callsign."""
        return self.backend_callsign_dict

    @property
    def available_aer(self) -> list[str]:
        """The available aer backends."""
        return list(self.backend_dict["sim"].keys())

    @property
    def available_aer_callsign(self) -> list[str]:
        """The available aer backends callsign."""
        return list(self.backend_callsign_dict["sim"].keys())

    @property
    def available_ibmq(self) -> list[str]:
        """The available ibmq/ibm backends."""
        return list(self.backend_dict["real"].keys())

    @property
    def available_ibmq_callsign(self) -> list[str]:
        """The available ibmq/ibm backends callsign."""
        return list(self.backend_callsign_dict["real"].keys())

    @property
    def available_fake(self) -> list[str]:
        """The available fake backends."""
        return list(self.backend_dict["fake"].keys())

    @property
    def available_fake_callsign(self) -> list[str]:
        """The available fake backends callsign."""
        return list(self.backend_callsign_dict["fake"].keys())

    def statesheet(self):
        """The statesheet of backend wrapper."""
        check_msg = Hoshi(
            [
                ("divider", 60),
                ("h3", "BackendWrapper Statesheet"),
            ],
            ljust_description_len=35,
            ljust_description_filler=".",
        )

        for desc, backs, backs_callsign in [
            ("Simulator", self.available_aer, self.backend_callsign_dict["sim"]),
            ("IBM", self.available_ibmq, self.backend_callsign_dict["real"]),
            ("Fake", self.available_fake, self.backend_callsign_dict["fake"]),
            (
                "Extra",
                self.available_backends["extra"],
                self.backend_callsign_dict["extra"],
            ),
        ]:
            _statesheet_preparings(
                check_msg,
                desc,
                backs,
                backs_callsign,
                self.is_aer_gpu,
                self._providers["fake"],
            )

        return check_msg

    def add_backend(
        self,
        name: str,
        backend: Backend,
        callsign: Optional[str] = None,
    ) -> None:
        """Add a backend to backend wrapper.

        Args:
            name (str): The name of backend.
            backend (Backend): The backend.
            callsign (Optional[str], optional): The callsign of backend. Defaults to None.
        """

        if not isinstance(backend, Backend):
            raise TypeError(
                "The backend should be a instance of 'qiskit.providers.Backend'"
            )

        if name in self.backend_dict["extra"]:
            raise ValueError(f"'{name}' backend already exists.")

        self.backend_dict["extra"][name] = backend
        if not callsign is None:
            self.backend_callsign_dict["extra"][callsign] = name

    def __call__(
        self,
        backend_name: str,
    ) -> Union[Backend, GeneralBackend]:

        for avaiable_type in ["real", "sim", "fake", "extra"]:
            if backend_name in self.backend_dict[avaiable_type]:
                return self.backend_dict[avaiable_type][backend_name]
            if backend_name in self.backend_callsign_dict[avaiable_type]:
                return self.backend_dict[avaiable_type][
                    self.backend_callsign_dict[avaiable_type][backend_name]
                ]

        raise ValueError(f"'{backend_name}' unknown backend or backend callsign.")


class BackendManager(BackendWrapper):
    """A wrapper includes accout loading and backend loading.
    And deal wtth either :module:`qiskit-ibmq-provider`
    or the older version `qiskit.providers.ibmq`.
    """

    def __init__(
        self,
        hub: Optional[str] = None,
        group: Optional[str] = None,
        project: Optional[str] = None,
        instance: Optional[str] = None,
        real_provider_source: Optional[RealImportPointType] = real_default_source,
        fake_version: Union[Literal["v1", "v2"], None] = None,
    ) -> None:
        if instance is not None:
            self.instance = instance
            self.hub, self.group, self.project = instance.split("/")
        else:
            for name in [hub, group, project]:
                if name is None:
                    raise ValueError(
                        "Please provide either instance or hub, group, project."
                    )
            self.instance = f"{hub}/{group}/{project}"
            self.hub = hub
            self.group = group
            self.project = project

        # pylint: disable=import-outside-toplevel, import-error, no-name-in-module
        if real_provider_source == "qiskit_ibm_provider":
            print("| Provider by 'qiskit_ibm_provider'.")
            try:
                from qiskit_ibm_provider import IBMProvider

                new_provider = IBMProvider(instance=self.instance)
                super().__init__(
                    real_provider=new_provider,
                    fake_version=fake_version,
                )
            except ImportError as err:
                raise ImportError(
                    "Provider by 'qiskit_ibm_provider' is not available, "
                    + "check installation of 'qiskit-ibm-provider' first."
                ) from err
        elif real_provider_source == "qiskit_ibmq_provider":
            print("| Provider by 'qiskit.providers.ibmq', which will be deprecated.")
            try:
                from qiskit.providers.ibmq import IBMQ  # type: ignore

                IBMQ.load_account()
                old_provider = IBMQ.get_provider(
                    hub=self.hub, group=self.group, project=self.project
                )
                super().__init__(
                    real_provider=old_provider,
                    fake_version=fake_version,
                )
            except ImportError as err:
                raise ImportError(
                    "Provider by 'qiskit_ibmq_provider' is not available, "
                    + "but it is a deprecated module, consider to use 'qiskit_ibm_provider'."
                    + "then check installation of 'qiskit-ibmq-provider'."
                ) from err

        else:
            print("| No IBM or IBMQ provider available.")
            super().__init__(
                real_provider=None,
                fake_version=fake_version,
            )

    def __repr__(self):
        repr_str = f"<{self.__class__.__name__}("
        repr_str += f'sim="{sim_default_source}", '
        repr_str += f'real="{real_default_source}", '
        repr_str += f'instance="{self.instance}", '
        fakeprovider_repr = (
            (
                "FakeProviderV2"
                if isinstance(self._providers["fake"], FakeProviderForBackendV2)
                else "FakeProvider"
            )
            if self._providers["fake"]
            else None
        )
        repr_str += f'fake="{fakeprovider_repr}"'
        repr_str += ")>"
        return repr_str

    @staticmethod
    def save_account(
        token: str,
        *args,
        real_provider_source: RealImportPointType = "qiskit_ibm_provider",
        overwrite: bool = False,
        **kwargs,
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
                "Please use keyword arguments to provide the parameters, "
                + "For example: `.save_account(token='your_token')`"
            )

        # pylint: disable=import-outside-toplevel, import-error, no-name-in-module
        if real_provider_source == "qiskit_ibm_provider":
            try:
                from qiskit_ibm_provider import IBMProvider

                IBMProvider.save_account(token=token, overwrite=overwrite, **kwargs)
            except ImportError as err:
                raise ImportError(
                    "Provider by 'qiskit_ibm_provider' is not available, "
                    + "check installation of 'qiskit-ibm-provider' first."
                ) from err

        elif real_provider_source == "qiskit_ibmq_provider":
            try:
                from qiskit.providers.ibmq import IBMQ  # type: ignore

                IBMQ.save_account(token=token, overwrite=overwrite, **kwargs)
            except ImportError as err:
                raise ImportError(
                    "Provider by 'qiskit_ibmq_provider' is not available, "
                    + "but it is a deprecated module, consider to use 'qiskit_ibm_provider'."
                    + "then check installation of 'qiskit-ibmq-provider'."
                ) from err
        else:
            raise ValueError(f"Unknown provider source: {real_default_source}.")
