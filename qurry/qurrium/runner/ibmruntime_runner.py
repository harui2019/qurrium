"""
================================================================
Runner for qiskit-ibm-runtime.
(:mod:`qurry.qurrium.runner.runner_ibm_runtime`)
================================================================

"""

import warnings
from typing import Union, Optional, Literal
from collections.abc import Hashable
from qiskit import QuantumCircuit

from .utils import retrieve_exceptions_loader
from ...exceptions import QurryExtraPackageRequired

try:
    from qiskit_ibm_runtime import (
        QiskitRuntimeService,
        IBMBackend,
    )
    from qiskit_ibm_runtime.runtime_job import RuntimeJob
    from qiskit_ibm_runtime.runtime_job_v2 import RuntimeJobV2
    from qiskit_ibm_runtime.exceptions import IBMError
except ImportError:
    raise QurryExtraPackageRequired(
        "These module requires the install of `qiskit-ibm-provider`,"
        + " please intall it then restart kernel."
    ) from ImportError

from .utils import (
    pending_pool_loading,
    pending_tag_packings,
    pk_from_list_to_tuple,
    retrieve_times_namer,
    retrieve_counter,
    is_not_overwrite_decider,
    circuits_map_distributer,
)
from .runner import Runner
from ..multimanager import MultiManager
from ..multimanager.arguments import PendingStrategyLiteral
from ..container import ExperimentContainer
from ..utils import get_counts_and_exceptions
from ...tools import qurry_progressbar, current_time


class IBMRuntimeRunner(Runner):
    """Pending and Retrieve Jobs from IBM backend."""

    __name__ = "IBMRuntimeRunner"

    backend: Optional[IBMBackend]
    """The backend been used."""
    provider: QiskitRuntimeService
    """The provider used for this backend."""
    reports: dict[str, dict[str, str]]

    def __init__(
        self,
        besummonned: Hashable,
        multimanager: MultiManager,
        experimental_container: ExperimentContainer,
        provider: QiskitRuntimeService,
        backend: Optional[IBMBackend] = None,
    ):
        assert multimanager.summoner_id == besummonned, (
            "Summoner ID not match, multimanager.summoner_id: "
            + f"{multimanager.summoner_id}, besummonned: {besummonned}"
        )
        if backend is None and provider is None:
            raise ValueError("Either backend or provider should be provided.")

        self.current_multimanager = multimanager
        """The multimanager from Qurry instance."""
        self.backend = backend
        """The backend will be use to pending and retrieve."""
        self.provider = provider
        """The provider will be used to pending and retrieve."""
        self.experiment_container = experimental_container
        """The experimental container from Qurry instance."""

        self.circwserial: dict[int, QuantumCircuit] = {}

        self.reports = {}

    def pending(
        self,
        pending_strategy: PendingStrategyLiteral = "tags",
        backend: Optional[IBMBackend] = None,
    ) -> list[tuple[Optional[str], Union[str, tuple[str, ...], Literal["_onetime"], Hashable]]]:
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
            self.backend = backend
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
                f"{pk}/{pending_job.job_id()}/{pending_job.tags}"
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
    ) -> list[tuple[Optional[str], Union[str, tuple[str, ...], Literal["_onetime"], Hashable]]]:
        """Retrieve jobs from remote backend.

        Args:
            overwrite (bool, optional): Overwrite the previous retrieve. Defaults to False.

        Returns:
            list[tuple[Optional[str], str]]: The list of job_id and pending tags.
        """

        pending_map: dict[Hashable, Union[RuntimeJob, RuntimeJobV2, None]] = {}
        counts_tmp_container: dict[int, dict[str, int]] = {}

        retrieve_times = retrieve_counter(self.current_multimanager.multicommons.datetimes)
        retrieve_times_name = retrieve_times_namer(retrieve_times + 1)

        if is_not_overwrite_decider(
            datetimes=self.current_multimanager.multicommons.datetimes,
            retrieve_times=retrieve_times,
            overwrite=overwrite,
        ):
            return self.current_multimanager.beforewards.job_id
        if overwrite:
            print("| Overwrite the previous retrieve.")

        self.current_multimanager.reset_afterwards(security=True, mute_warning=True)
        assert (
            len(self.current_multimanager.afterwards.allCounts) == 0
        ), "All counts should be null."

        current = current_time()
        self.current_multimanager.multicommons.datetimes[retrieve_times_name] = current

        retrieve_progressbar = qurry_progressbar(
            self.current_multimanager.beforewards.job_id,
            bar_format="| {n_fmt}/{total_fmt} - retrieve: {desc} - {elapsed} < {remaining}",
        )

        for pending_id, pk in retrieve_progressbar:
            pending_tags = pk_from_list_to_tuple(pk)
            if pending_id is None:
                warnings.warn(f"Pending pool '{pending_tags}' is empty.")
                continue
            try:
                retrieve_progressbar.set_description_str(
                    f"{pending_tags}/{pending_id}", refresh=True
                )
                pending_map[pending_tags] = self.provider.job(pending_id)
            except IBMError as e:
                retrieve_progressbar.set_description_str(
                    f"{pending_tags}/{pending_id} - Error: {e}", refresh=True
                )
                pending_map[pending_tags] = None

        pendingpool_progressbar = qurry_progressbar(
            self.current_multimanager.beforewards.pending_pool.items(),
            bar_format=("| {n_fmt}/{total_fmt} - get counts: {desc} - {elapsed} < {remaining}"),
        )

        for pk, pcircs in pendingpool_progressbar:
            pending_tags = pk_from_list_to_tuple(pk)
            if len(pcircs) == 0:
                warnings.warn(f"Pending pool '{pending_tags}' is empty.")
                continue

            tmp_pending_map = pending_map[pending_tags]
            if tmp_pending_map is not None:
                pendingpool_progressbar.set_description_str(
                    f"{pending_tags}/{tmp_pending_map.job_id()}/{tmp_pending_map.tags}",
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
