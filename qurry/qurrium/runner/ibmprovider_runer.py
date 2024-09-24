"""
================================================================
Runner for qiskit-ibm-provider
(:mod:`qurry.qurrium.runner.runner_ibm_provider`)
================================================================

"""

import warnings
from typing import Union, Optional
from collections.abc import Hashable
from qiskit import QuantumCircuit

from .utils import retrieve_exceptions_loader
from ...exceptions import QurryExtraPackageRequired

try:
    from qiskit_ibm_provider import IBMBackend, IBMProvider  # type: ignore
    from qiskit_ibm_provider.job import IBMCircuitJob, IBMJob  # type: ignore
    from qiskit_ibm_provider.exceptions import IBMError  # type: ignore
except ImportError:
    raise QurryExtraPackageRequired(
        "These module requires the install of `qiskit-ibm-provider`,"
        + " please intall it then restart kernel."
    ) from ImportError

try:
    # pylint: disable=ungrouped-imports
    from qiskit.providers.ibmq import IBMQBackend, IBMQError  # type: ignore

    # pylint: enable=ungrouped-imports

    QISKIT_IBMQ_PROVIDER = True

except ImportError:
    QISKIT_IBMQ_PROVIDER = False

    class IBMQBackend(IBMBackend):
        """A dummy class for IBMQBackend."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            raise QurryExtraPackageRequired(
                "These module requires the install of `qiskit-ibmq-provider`,"
                + " please intall it then restart kernel."
            )

    class IBMQError(Exception):
        """A dummy class for IBMQError."""

        def __init__(self):
            raise QurryExtraPackageRequired(
                "These module requires the install of `qiskit-ibmq-provider`,"
                + " please intall it then restart kernel."
            )


from .utils import (
    pending_tag_packings,
    pending_pool_loading,
    pk_from_list_to_tuple,
    retrieve_times_namer,
    retrieve_counter,
    circuits_map_distributer,
)
from .runner import Runner
from ..multimanager import MultiManager
from ..multimanager.beforewards import TagListKeyable
from ..multimanager.arguments import PendingStrategyLiteral
from ..container import ExperimentContainer
from ..utils import get_counts_and_exceptions
from ...tools import qurry_progressbar, current_time


class IBMProviderRunner(Runner):
    """Pending and Retrieve Jobs from IBM backend."""

    __name__ = "IBMProviderRunner"

    backend: Optional[IBMBackend]
    """The backend been used."""
    reports: dict[str, dict[str, str]]

    def __init__(
        self,
        besummonned: Hashable,
        multimanager: MultiManager,
        experimental_container: ExperimentContainer,
        backend: Optional[IBMBackend] = None,
        provider: Optional[IBMProvider] = None,
    ):
        assert multimanager.summoner_id == besummonned, (
            "Summoner ID not match, multimanager.summoner_id: "
            + f"{multimanager.summoner_id}, besummonned: {besummonned}"
        )
        if backend is None and provider is None:
            raise ValueError("Either backend or provider should be provided.")

        if backend is not None:
            if isinstance(backend, IBMBackend):
                ...
            elif QISKIT_IBMQ_PROVIDER:
                if isinstance(backend, IBMQBackend):
                    print("| Downgrade compatibility with qiskit-ibmq-provider is available.")
                    warnings.warn(
                        "You should use 'IBMBackend' from 'qiskit_ibm_provider' "
                        + "which imports from 'qiskit.providers.ibm' for 'IBM' jobstype. "
                        + "qiskit-ibmq-provider is deprecated.",
                        category=DeprecationWarning,
                    )
                else:
                    raise TypeError(
                        "You must use 'IBMBackend' from 'qiskit_ibm_provider' "
                        + "which imports from 'qiskit.providers.ibm' for 'IBM' jobstype. "
                    )
            else:
                raise TypeError(
                    "You must use 'IBMBackend' from 'qiskit_ibm_provider' "
                    + "which imports from 'qiskit.providers.ibm' for 'IBM' jobstype. "
                )
        if provider is not None:
            if not isinstance(provider, IBMProvider):
                raise TypeError(
                    "You must use 'IBMProvider' from 'qiskit_ibm_provider' "
                    + "which imports from 'qiskit.providers.ibm' for 'IBM' jobstype. "
                )

        self.current_multimanager = multimanager
        """The multimanager from Qurry instance."""
        self.backend = backend
        """The backend will be use to pending and retrieve."""
        self.provider = backend.provider if backend is not None else provider
        """The provider will be used to pending and retrieve."""
        self.experiment_container = experimental_container
        """The experimental container from Qurry instance."""

        self.circwserial: dict[int, QuantumCircuit] = {}

        self.reports = {}

    def pending(
        self,
        pending_strategy: PendingStrategyLiteral = "tags",
        backend: Optional[IBMBackend] = None,
    ) -> list[tuple[Optional[str], TagListKeyable]]:
        """Pending jobs to remote backend.

        Args:
            pending_strategy (Literal["onetime", "each", "tags"], optional):

                - "onetime": Pending all circuits in one job.
                - "each": Pending each circuit in one job.
                - "tags": Pending each circuit in one job with tags.

                Defaults to "onetime".
            backend (Optional[IBMBackend], optional):
                The backend will be used to pending. Defaults to None.

        Returns:
            list[tuple[Optional[str], str]]: The list of job_id and pending tags.
        """

        if self.backend is None:
            if backend is None:
                raise ValueError("At least one of backend and provider should be given.")
            print(f"| Given backend and provider as {backend.name} and {backend.provider}.")
            self.backend = backend
            self.provider = backend.provider
        else:
            print("| Using backend and provider as " + f"{self.backend.name} and {self.provider}.")

        pending_pool_loading(
            pending_strategy=pending_strategy,
            circ_with_serial_num=self.circwserial,
            current_multimanager=self.current_multimanager,
            experiment_container=self.experiment_container,
        )

        current = current_time()
        self.current_multimanager.multicommons.datetimes["pending"] = current

        pendingpool_progressbar = qurry_progressbar(
            self.current_multimanager.beforewards.pending_pool.items(),
            bar_format="| {n_fmt}/{total_fmt} - pending: {desc} - {elapsed} < {remaining}",
            # leave=False,
        )

        for pk, pcirc_idxs in pendingpool_progressbar:
            if len(pcirc_idxs) == 0:
                self.current_multimanager.beforewards.job_id.append((None, pk))
                warnings.warn(f"| Pending pool '{pk}' is empty.")
                continue

            all_pending_tags = pending_tag_packings(pk, self.current_multimanager)

            pending_job = self.backend.run(
                circuits=[self.circwserial[idx] for idx in pcirc_idxs],
                shots=self.current_multimanager.multicommons.shots,
                job_tags=all_pending_tags,
                **self.current_multimanager.multicommons.manager_run_args,  # type: ignore
            )
            pendingpool_progressbar.set_description_str(
                f"{pk}/{pending_job.job_id()}/{pending_job.tags()}"
            )
            self.current_multimanager.beforewards.job_id.append((pending_job.job_id(), pk))
            self.reports[pending_job.job_id()] = {
                "time": current,
                "type": "pending",
            }

        for id_exec in self.current_multimanager.beforewards.exps_config:
            self.experiment_container[id_exec].commons.datetimes["pending"] = current

        self.current_multimanager.multicommons.datetimes["pendingCompleted"] = current_time()

        return self.current_multimanager.beforewards.job_id

    def retrieve(
        self,
        overwrite: bool = False,
    ) -> list[tuple[Optional[str], TagListKeyable]]:
        """Retrieve jobs from remote backend.

        Args:
            overwrite (bool, optional): Overwrite the previous retrieve. Defaults to False.

        Returns:
            list[tuple[Optional[str], str]]: The list of job_id and pending tags.
        """

        pending_map: dict[Hashable, Union[IBMCircuitJob, "IBMJob", None]] = {}
        counts_tmp_container: dict[int, dict[str, int]] = {}

        retrieve_times = retrieve_counter(self.current_multimanager.multicommons.datetimes)
        retrieve_times_name = retrieve_times_namer(retrieve_times + 1)

        if retrieve_times > 0 and not overwrite:
            print(f"| retrieve times: {retrieve_times}, overwrite: {overwrite}")
            last_time_date = self.current_multimanager.multicommons.datetimes[
                retrieve_times_namer(retrieve_times)
            ]
            print(f"| Last retrieve by: {retrieve_times_namer(retrieve_times)} at {last_time_date}")
            print("| Seems to there are some retrieves before.")
            print("| You can use `overwrite=True` to overwrite the previous retrieve.")

            return self.current_multimanager.beforewards.job_id

        if overwrite:
            print("| Overwrite the previous retrieve.")
        self.current_multimanager.reset_afterwards(security=True, mute_warning=True)
        assert (
            len(self.current_multimanager.afterwards.allCounts) == 0
        ), "All counts should be null."

        current = current_time()
        self.current_multimanager.multicommons.datetimes[retrieve_times_name] = current

        if QISKIT_IBMQ_PROVIDER:
            print("| Downgrade compatibility with qiskit-ibmq-provider is available.")

        retrieve_progressbar = qurry_progressbar(
            self.current_multimanager.beforewards.job_id,
            bar_format="| {n_fmt}/{total_fmt} - retrieve: {desc} - {elapsed} < {remaining}",
            # leave=False,
        )
        if self.provider is None:
            raise ValueError("provider should not be None.")
        assert isinstance(self.provider, IBMProvider), (
            "provider should be IBMProvider, not " + f"{type(self.provider)}: {self.provider}."
        )

        retrieve_principal: Union["IBMQBackend", IBMProvider]
        retrieve_principal = (
            self.backend
            if QISKIT_IBMQ_PROVIDER and isinstance(self.backend, IBMQBackend)
            else self.provider
        )
        assert hasattr(retrieve_principal, "retrieve_job"), "retrieve_principal should not be None."

        for pending_id, pk in retrieve_progressbar:
            pending_tags = pk_from_list_to_tuple(pk)
            if pending_id is None:
                warnings.warn(f"Pending pool '{pending_tags}' is empty.")
                continue
            try:
                retrieve_progressbar.set_description_str(
                    f"{pending_tags}/{pending_id}", refresh=True
                )
                pending_map[pending_tags] = retrieve_principal.retrieve_job(job_id=pending_id)
            except IBMError as e:
                retrieve_progressbar.set_description_str(
                    f"{pending_tags}/{pending_id} - Error: {e}", refresh=True
                )
                pending_map[pending_tags] = None
            except IBMQError as e:
                retrieve_progressbar.set_description_str(
                    f"{pending_tags}/{pending_id} - Error: {e}", refresh=True
                )
                pending_map[pending_tags] = None

        pendingpool_progressbar = qurry_progressbar(
            self.current_multimanager.beforewards.pending_pool.items(),
            bar_format=("| {n_fmt}/{total_fmt} - get counts: {desc} - {elapsed} < {remaining}"),
            # leave=False,
        )

        for pk, pcircs in pendingpool_progressbar:
            pending_tags = pk_from_list_to_tuple(pk)
            if len(pcircs) == 0:
                warnings.warn(f"Pending pool '{pending_tags}' is empty.")
                continue

            tmp_pending_map = pending_map[pending_tags]
            if tmp_pending_map is not None:
                pendingpool_progressbar.set_description_str(
                    f"{pending_tags}/{tmp_pending_map.job_id()}" + f"/{tmp_pending_map.tags()}",
                    refresh=True,
                )
                self.reports[tmp_pending_map.job_id()] = {
                    "time": current,
                    "type": "retrieve",
                }
                try:
                    counts, exceptions = get_counts_and_exceptions(
                        result=tmp_pending_map.result(),
                        result_idx_list=[rk - pcircs[0] for rk in pcircs],
                    )
                except IBMError as e:
                    counts, exceptions = [{} for _ in pcircs], {tmp_pending_map.job_id(): e}
            else:
                pendingpool_progressbar.set_description_str(
                    f"{pending_tags} failed - No available tags", refresh=True
                )
                counts, exceptions = get_counts_and_exceptions(
                    result=None, result_idx_list=[rk - pcircs[0] for rk in pcircs]
                )
                pendingpool_progressbar.set_description_str(
                    f"{pending_tags} failed - No available tags - {len(counts)}",
                    refresh=True,
                )
            assert len(counts) == len(pcircs), (
                f"Length of counts {len(counts)} not equal to length of "
                + f"pcircs {len(pcircs)} in pending pool '{pending_tags}'."
            )
            for rk in pcircs:
                counts_tmp_container[rk] = counts[rk - pcircs[0]]
                pendingpool_progressbar.set_description_str(
                    f"{pending_tags} - Packing: {rk} with len {len(counts[rk - pcircs[0]])}",
                    refresh=True,
                )
            retrieve_exceptions_loader(exceptions, self.current_multimanager.outfields)

        circuits_map_distributer(
            current_multimanager=self.current_multimanager,
            experiment_container=self.experiment_container,
            counts_tmp_container=counts_tmp_container,
            retrieve_times_name=retrieve_times_name,
        )

        return self.current_multimanager.beforewards.job_id
