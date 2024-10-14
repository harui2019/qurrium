"""
================================================================
Runner for qiskit-ibmq-provider
(:mod:`qurry.qurrium.runner.ibmqrunner`)

Qutoes:
> For those who still use IBMQ backend...
> UPDATE YOUR CODE BASE AND QISKIT TO LATEST VERSION!!!
> This package is deprecated for years.
================================================================

"""

import warnings
from typing import Literal, Optional, NamedTuple, Any
from collections.abc import Hashable

from qiskit import QuantumCircuit

from .utils import retrieve_exceptions_loader
from ...exceptions import QurryExtraPackageRequired

try:
    from qiskit.providers.ibmq import IBMQBackend, IBMQJobManager, AccountProvider  # type: ignore
    from qiskit.providers.ibmq.managed import (  # type: ignore
        ManagedJobSet,
        IBMQJobManagerInvalidStateError,
    )
    from qiskit.providers.ibmq.exceptions import IBMQError  # type: ignore
except ImportError as exception:
    raise QurryExtraPackageRequired(
        "These module requires the install of "
        + "`qiskit-ibmq-provider`, please intall it then restart kernel."
    ) from exception

from .utils import retrieve_times_namer, retrieve_counter
from .runner import Runner
from ..multimanager import MultiManager
from ..multimanager.beforewards import TagListKeyable
from ..multimanager.arguments import PendingStrategyLiteral
from ..container import ExperimentContainer
from ..utils import get_counts_and_exceptions
from ...tools import qurry_progressbar, current_time


class QurryIBMQBackendIO(NamedTuple):
    """The package for pending and retrieve jobs from IBMQ backend,
    which runs by :cls:`IBMQJobManager`.

    """

    managedJob: Optional[ManagedJobSet]
    """The managed job set."""
    jobID: str
    """The job ID on IBMQ."""
    report: str
    """The report of job from IBMQJobManager."""
    name: str
    """The name of job on IBMQ."""
    type: Literal["pending", "retrieve"]
    """The type of job."""


class IBMQRunner(Runner):
    """Pending and Retrieve Jobs from IBMQ backend."""

    __name__ = "IBMQRunner"

    current_multimanager: MultiManager
    backend: Optional[IBMQBackend]
    provider: AccountProvider

    reports: dict[str, dict[str, str]]

    job_manager: IBMQJobManager
    """JobManager for IBMQ"""

    def __init__(
        self,
        besummonned: Hashable,
        multimanager: MultiManager,
        experimental_container: ExperimentContainer,
        backend: Optional[IBMQBackend] = None,
        provider: Optional[AccountProvider] = None,
    ):
        warnings.warn(
            "The 'IBMQ' backend is deprecated, please use 'IBM' backend instead.",
            DeprecationWarning,
        )

        assert multimanager.summoner_id == besummonned, (
            "Summoner ID not match, multimanager.summoner_id: "
            + f"{multimanager.summoner_id}, besummonned: {besummonned}"
        )
        if backend is None and provider is None:
            raise ValueError("At least one of backend and provider should be given.")

        self.current_multimanager = multimanager
        """The multimanager from Qurry instance."""
        self.backend = backend
        """The backend will be use to pending and retrieve."""
        tmp_provider = backend.provider() if backend is not None else provider
        assert (
            tmp_provider is not None
        ), f"Provider should be given, but got {tmp_provider} from" + (
            "backend.provider()" if backend is not None else "the input."
        )
        self.provider = tmp_provider
        """The provider will be used to pending and retrieve."""
        self.experiment_container = experimental_container
        """The experimental container from Qurry instance."""

        self.job_manager = IBMQJobManager()
        """JobManager for IBMQ"""
        self.circwserial: dict[int, QuantumCircuit] = {}

        self.reports = {}

    def pending(
        self,
        pending_strategy: PendingStrategyLiteral = "tags",
        backend: Optional[IBMQBackend] = None,
    ) -> list[tuple[Optional[str], TagListKeyable]]:
        """Pending jobs to remote backend.

        Args:
            pending_strategy (Literal[
                &quot;default&quot;,
                &quot;onetime&quot;,
                &quot;each&quot;,
                &quot;tags&quot;], optional):
                    Pending strategy. Defaults to &quot;default&quot;.
                    Defaults to "default".
            backend (IBMQBackend, optional):
                The backend will be use to pending and retrieve.
                Defaults to None.

        Raises:
            ValueError: At least one of backend and provider should be given.

        Returns:
            list[tuple[str, str]]: The pending job IDs storation.
        """
        warnings.warn(
            "The 'IBMQ' backend is deprecated, please use 'IBM' backend instead.",
            DeprecationWarning,
        )

        if self.backend is None:
            if backend is None:
                raise ValueError("At least one of backend and provider should be given.")
            print(f"| Given backend and provider as {backend.name()} and {backend.provider()}.")
            self.backend = backend
            tmp_provider = backend.provider()
            assert (
                tmp_provider is not None
            ), f"The backend {backend} has no provider, backend.provider() >>> {tmp_provider}"
            self.provider = tmp_provider
        else:
            if backend is not None:
                print(
                    "| Using backend and provider as "
                    + f"{self.backend.name()} and {self.backend.provider()}."
                )
            else:
                ...

        distributing_pending_progressbar = qurry_progressbar(
            self.current_multimanager.beforewards.exps_config,
            bar_format=("| {n_fmt}/{total_fmt} - Preparing pending pool - {elapsed} < {remaining}"),
        )

        for id_exec in distributing_pending_progressbar:
            circ_serial_len = len(self.circwserial)
            for idx, circ in enumerate(self.experiment_container[id_exec].beforewards.circuit):
                self.current_multimanager.beforewards.circuits_map[id_exec].append(
                    idx + circ_serial_len
                )

                if pending_strategy == "each":
                    self.current_multimanager.beforewards.pending_pool[id_exec].append(
                        idx + circ_serial_len
                    )

                elif pending_strategy == "tags":
                    tags = self.experiment_container[id_exec].commons.tags
                    self.current_multimanager.beforewards.pending_pool[tags].append(
                        idx + circ_serial_len
                    )

                else:
                    if pending_strategy != "default" or pending_strategy != "onetime":
                        warnings.warn(f"Unknown strategy '{pending_strategy}, use 'onetime'.")
                    self.current_multimanager.beforewards.pending_pool["_onetime"].append(
                        idx + circ_serial_len
                    )

                self.circwserial[idx + circ_serial_len] = circ

        current = current_time()
        self.current_multimanager.multicommons.datetimes["pending"] = current

        pendingpool_progressbar = qurry_progressbar(
            self.current_multimanager.beforewards.pending_pool.items(),
            bar_format=("| {n_fmt}/{total_fmt} - pending: {desc} - {elapsed} < {remaining}"),
        )

        for pk, pcirc_idxs in pendingpool_progressbar:
            assert isinstance(pk, str)
            if len(pcirc_idxs) > 0:
                if pk == "_onetime":
                    pending_name = f"{self.current_multimanager.multicommons.summoner_name}"
                elif isinstance(pk, (list, tuple)):
                    pending_name = (
                        f"{self.current_multimanager.multicommons.summoner_name}"
                        + f'-{"-".join(pk)}'
                    )
                else:
                    pending_name = (
                        f"{self.current_multimanager.multicommons.summoner_name}" + f"-{pk}"
                    )

                pending_job = IBMQPending(
                    ibmqjobmanager=self.job_manager,
                    experiments=[self.circwserial[idx] for idx in pcirc_idxs],
                    backend=self.backend,
                    shots=self.current_multimanager.multicommons.shots,
                    name=pending_name,
                    manager_run_args=(
                        self.current_multimanager.multicommons.manager_run_args  # type: ignore
                    ),
                )
                pendingpool_progressbar.set_description_str(
                    f"{pk}/{pending_job.jobID}/{pending_job.name}"
                )
                self.current_multimanager.beforewards.job_id.append((pending_job.jobID, pk))
                self.reports[pending_job.jobID] = {
                    "time": current,
                    "type": "pending",
                    "report": pending_job.report,
                }

            else:
                self.current_multimanager.beforewards.job_id.append((None, pk))
                warnings.warn(f"| Pending pool '{pk}' is empty.")

        for id_exec in self.current_multimanager.beforewards.exps_config:
            self.experiment_container[id_exec].commons.datetimes["pending"] = current

        self.current_multimanager.multicommons.datetimes["pendingCompleted"] = current_time()

        return self.current_multimanager.beforewards.job_id

    def retrieve(
        self,
        overwrite: bool = False,
        refresh: bool = False,
    ) -> list[tuple[Optional[str], TagListKeyable]]:
        """Retrieve jobs from remote backend.

        Args:
            overwrite (bool, optional):
                If `True`, overwrite the previous retrieve. Defaults to False.
            refresh (bool, optional):
                If `True`, re-query the server for the job set information. Defaults to False.

        Returns:
            list[tuple[str, str]]: The retrieved job IDs storation.
        """
        warnings.warn(
            "The 'IBMQ' backend is deprecated, please use 'IBM' backend instead.",
            DeprecationWarning,
        )

        pending_map: dict[Hashable, QurryIBMQBackendIO] = {}
        counts_tmp_container: dict[int, dict[str, int]] = {}

        retrieve_times = retrieve_counter(self.current_multimanager.multicommons.datetimes)
        retrieve_times_name = retrieve_times_namer(retrieve_times + 1)

        print(f"| retrieve times: {retrieve_times}, overwrite: {overwrite}")
        if retrieve_times > 1 and overwrite is False:
            print("| Overwrite not triggerred, read existed data.")
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

        retrieve_progressbar = qurry_progressbar(
            self.current_multimanager.beforewards.job_id,
            bar_format=("| {n_fmt}/{total_fmt} - retrieve: {desc} - {elapsed} < {remaining}"),
        )

        for pending_id, pk in retrieve_progressbar:
            if pending_id is None:
                warnings.warn(f"Pending pool '{pk}' is empty.")
                continue
            retrieve_progressbar.set_description_str(f"{pk}/{pending_id}")
            pending_map[pk] = IBMQRetrieve(
                ibmqjobmanager=self.job_manager,
                jobID=pending_id,
                provider=self.provider,
                refresh=refresh,
            )

        pendingpool_progressbar = qurry_progressbar(
            self.current_multimanager.beforewards.pending_pool.items(),
            bar_format=("| {n_fmt}/{total_fmt} - get counts: {desc} - {elapsed} < {remaining}"),
        )

        for pk, pcircs in pendingpool_progressbar:
            if len(pcircs) > 0:
                pending_job = pending_map[pk]
                pendingpool_progressbar.set_description_str(
                    f"{pk}/{pending_job.jobID}/{pending_job.name}"
                )
                self.reports[pending_job.jobID] = {
                    "time": current,
                    "type": "retrieve",
                    "report": pending_job.report,
                }

                if pending_job.managedJob is not None:
                    try:
                        counts, exceptions = get_counts_and_exceptions(
                            result=pending_job.managedJob.results(),
                            result_idx_list=[rk - pcircs[0] for rk in pcircs],
                        )
                    except IBMQError as e:
                        counts, exceptions = [{}], {pending_job.managedJob.job_set_id(): e}
                    pendingpool_progressbar.set_description_str(
                        f"{pk}/{pending_job.jobID}/{pending_job.name} - len: {len(counts)}"
                    )
                else:
                    counts, exceptions = get_counts_and_exceptions(
                        result=None, result_idx_list=[rk - pcircs[0] for rk in pcircs]
                    )
                    pendingpool_progressbar.set_description_str(
                        f"{pk}/{pending_job.jobID}/{pending_job.name} - len: {len(counts)}"
                    )
                for rk in pcircs:
                    counts_tmp_container[rk] = counts[rk - pcircs[0]]
                    pendingpool_progressbar.set_description_str(
                        f"{pk}/{pending_job.jobID}/{pending_job.name} - "
                        + f"Packing: {rk} with len {len(counts[rk - pcircs[0]])}"
                    )
                retrieve_exceptions_loader(exceptions, self.current_multimanager.outfields)
            else:
                warnings.warn(f"Pending pool '{pk}' is empty.")

        distributing_progressbar = qurry_progressbar(
            self.current_multimanager.beforewards.circuits_map.items(),
            bar_format=("| {n_fmt}/{total_fmt} - Distributing {desc} - {elapsed} < {remaining}"),
        )
        for current_id, idx_circs in distributing_progressbar:
            distributing_progressbar.set_description_str(
                f"{current_id} with {len(idx_circs)} circuits"
            )
            self.experiment_container[current_id].reset_counts(
                summoner_id=self.current_multimanager.summoner_id
            )
            for idx in idx_circs:
                self.experiment_container[current_id].afterwards.counts.append(
                    counts_tmp_container[idx]
                )
            self.experiment_container[current_id].commons.datetimes[retrieve_times_name] = current
            self.current_multimanager.afterwards.allCounts[current_id] = self.experiment_container[
                current_id
            ].afterwards.counts

        return self.current_multimanager.beforewards.job_id


# pylint: disable=invalid-name
def IBMQPending(
    ibmqjobmanager: IBMQJobManager,
    experiments: list[QuantumCircuit],
    backend: IBMQBackend,
    shots: int = 1024,
    name: str = "qurryV5",
    manager_run_args: Optional[dict[str, Any]] = None,
) -> QurryIBMQBackendIO:
    """Pending circuits to `IBMQ`

    Args:
        ibmqJobManager (IBMQJobManager): The instance of :cls:`IBMQJobManager`.
        experiments (list[QuantumCircuit]): The list of circuits to run.
        backend (IBMQBackend): The IBMQ backend instance.
        shots (int, optional): Shots for IBMQ backends. Defaults to 1024.
        name (str, optional): Jobs name for IBMQ backends. Defaults to 'qurryV5'.
        manager_run_args (dict[str, any], optional):
            Extra arguments for `IBMQManager.run`. Defaults to {}.

    Returns:
        QurryIBMQPackage: Returns a `QurryIBMQPackage` with the following attributes:
    """
    if manager_run_args is None:
        manager_run_args = {}

    pending_job = ibmqjobmanager.run(
        **manager_run_args,
        experiments=experiments,
        backend=backend,
        shots=shots,
        name=name,
    )

    return QurryIBMQBackendIO(
        managedJob=pending_job,
        jobID=pending_job.job_set_id(),
        report=pending_job.report(),
        name=pending_job.name(),
        type="pending",
    )


def IBMQRetrieve(
    ibmqjobmanager: IBMQJobManager,
    jobID: str,
    provider: AccountProvider,
    refresh: bool = False,
) -> QurryIBMQBackendIO:
    """Retrieved result from `IBMQ`.

    Args:
        ibmqJobManager (IBMQJobManager): The instance of :cls:`IBMQJobManager`.
        jobID (str): The job ID on IBMQ.
        provider (AccountProvider): The provider instance.
        refresh (bool, optional): If `True`, re-query the server for the job set information.
            Otherwise return the cached value. Defaults to False.

    Returns:
        QurryIBMQPackage: Returns a `QurryIBMQPackage` with the following attributes:
    """

    try:
        retrieved_job = ibmqjobmanager.retrieve_job_set(
            job_set_id=jobID,
            provider=provider,
            refresh=refresh,
        )
        jobID = retrieved_job.job_set_id()
        report = retrieved_job.report()
        name = retrieved_job.name()

    except IBMQJobManagerInvalidStateError as e:
        retrieved_job = None
        report = f"Job unreachable, '{e}'."
        name = ""

    except IBMQError as e:
        retrieved_job = None
        report = f"Job fully corrupted, '{e}'."
        name = ""

    return QurryIBMQBackendIO(
        managedJob=retrieved_job, jobID=jobID, report=report, name=name, type="retrieve"
    )


# pylint: enable=invalid-name
