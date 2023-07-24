from ...exceptions import QurryExtraPackageRequired
try: 
    from qiskit.providers.ibmq import IBMQBackend, IBMQJobManager, AccountProvider
    from qiskit.providers.ibmq.managed import ManagedJobSet, IBMQJobManagerInvalidStateError
    from qiskit.providers.ibmq.exceptions import IBMQError
except ImportError:
    raise QurryExtraPackageRequired(
        "These module requires the install of `qiskit-ibmq-provider`, please intall it then restart kernel.")
from qiskit import QuantumCircuit
from typing import Literal, NamedTuple, Hashable, Any, Optional
import warnings

from .runner import Runner
from ..multimanager import MultiManager
from ..container import ExperimentContainer
from ..utils import get_counts, currentTime
from ...tools import qurryProgressBar


class QurryIBMQBackendIO(NamedTuple):

    managedJob: ManagedJobSet
    jobID: str
    report: str
    name: str
    type: Literal['pending', 'retrieve']


class IBMQRunner(Runner):
    """Pending and Retrieve Jobs from IBMQ backend."""

    currentMultiManager: MultiManager
    backend: Optional[IBMQBackend]
    provider: AccountProvider

    reports: dict[str, dict[str, str]]

    JobManager: IBMQJobManager
    """JobManager for IBMQ"""

    def __init__(
        self,
        besummonned: Hashable,
        multimanager: MultiManager,
        experimentalContainer: ExperimentContainer,
        backend: Optional[IBMQBackend] = None,
        provider: Optional[AccountProvider] = None,
    ):
        assert multimanager.summonerID == besummonned, (
            f"Summoner ID not match, multimanager.summonerID: {multimanager.summonerID}, besummonned: {besummonned}"
        )
        if backend is None and provider is None:
            raise ValueError(
                "At least one of backend and provider should be given."
            )

        self.currentMultiManager = multimanager
        """The multimanager from Qurry instance."""
        self.backend = backend
        """The backend will be use to pending and retrieve."""
        self.provider = backend.provider() if backend is not None else provider
        """The provider will be used to pending and retrieve."""
        self.expContainer = experimentalContainer
        """The experimental container from Qurry instance."""

        self.JobManager = IBMQJobManager()
        """JobManager for IBMQ"""
        self.circWithSerial: dict[int, QuantumCircuit] = {}

        self.reports = {}

    def pending(
        self,
        pendingStrategy: Literal['default', 'onetime', 'each',
                                 'tags'] = 'default',
        backend: Optional[IBMQBackend] = None,
    ) -> list[tuple[str, str]]:

        if self.backend is None:
            if backend is None:
                raise ValueError(
                    "At least one of backend and provider should be given.")
            else:
                print(
                    f"| Given backend and provider as {backend.name()} and {backend.provider()}.")
                self.backend = backend
                self.provider = backend.provider()
        else:
            if backend is not None:
                print(
                    f"| Using backend and provider as {self.backend.name()} and {self.backend.provider()}.")
            else:
                ...

        distributingPendingProgressBar = qurryProgressBar(
            self.currentMultiManager.beforewards.expsConfig,
            bar_format=(
                '| {n_fmt}/{total_fmt} - Preparing pending pool - {elapsed} < {remaining}'
            ),
        )

        for id_exec in distributingPendingProgressBar:
            circSerialLen = len(self.circWithSerial)
            for idx, circ in enumerate(
                    self.expContainer[id_exec].beforewards.circuit):
                self.currentMultiManager.beforewards.circuitsMap[id_exec].append(
                    idx + circSerialLen)

                if pendingStrategy == 'each':
                    self.currentMultiManager.beforewards.pendingPools[
                        id_exec].append(idx + circSerialLen)

                elif pendingStrategy == 'tags':
                    tags = self.expContainer[id_exec].commons.tags
                    self.currentMultiManager.beforewards.pendingPools[tags].append(
                        idx + circSerialLen)

                else:
                    if pendingStrategy != 'default' or pendingStrategy != 'onetime':
                        warnings.warn(
                            f"Unknown strategy '{pendingStrategy}, use 'onetime'."
                        )
                    self.currentMultiManager.beforewards.pendingPools[
                        '_onetime'].append(idx + circSerialLen)

                self.circWithSerial[idx + circSerialLen] = circ

        current = currentTime()
        self.currentMultiManager.multicommons.datetimes['pending'] = current

        pendingPoolProgressBar = qurryProgressBar(
            self.currentMultiManager.beforewards.pendingPools.items(),
            bar_format=(
                '| {n_fmt}/{total_fmt} - pending: {desc} - {elapsed} < {remaining}'
            ),
        )

        for pk, pcircIdxs in pendingPoolProgressBar:
            if len(pcircIdxs) > 0:
                if pk == '_onetime':
                    pendingName = f'{self.currentMultiManager.multicommons.summonerName}'
                elif isinstance(pk, (list, tuple)):
                    pendingName = f'{self.currentMultiManager.multicommons.summonerName}-{"-".join(pk)}'
                else:
                    pendingName = f'{self.currentMultiManager.multicommons.summonerName}-{pk}'

                pendingJob = IBMQPending(
                    ibmqJobManager=self.JobManager,
                    experiments=[
                        self.circWithSerial[idx] for idx in pcircIdxs
                    ],
                    backend=self.backend,
                    shots=self.currentMultiManager.multicommons.shots,
                    name=pendingName,
                    managerRunArgs=self.currentMultiManager.multicommons.
                    managerRunArgs,
                )
                pendingPoolProgressBar.set_description_str(
                    f"{pk}/{pendingJob.jobID}/{pendingJob.name}")
                self.currentMultiManager.beforewards.jobID.append(
                    (pendingJob.jobID, pk))
                self.reports[pendingJob.jobID] = {
                    'time': current,
                    'type': 'pending',
                    'report': pendingJob.report
                }

            else:
                self.currentMultiManager.beforewards.jobID.append((None, pk))
                warnings.warn(f"| Pending pool '{pk}' is empty.")

        for id_exec in self.currentMultiManager.beforewards.expsConfig:
            self.expContainer[id_exec].commons.datetimes['pending'] = current

        self.currentMultiManager.multicommons.datetimes[
            'pendingCompleted'] = currentTime()

        return self.currentMultiManager.beforewards.jobID

    def retrieve(
        self,
        provider: AccountProvider,
        refresh: bool = False,
        overwrite: bool = False,
    ) -> list[tuple[str, str]]:

        pendingMapping: dict[Hashable, QurryIBMQBackendIO] = {}
        coutsTmpContainer: dict[str, dict[str, int]] = {}

        def retrieveTimesNamer(retrieveTimes):
            return 'retrieve.' + f'{retrieveTimes}'.rjust(3, '0')

        alreadyRetrieved: list[str] = [
            datetimeTag
            for datetimeTag in self.currentMultiManager.multicommons.datetimes
            if 'retrieve' in datetimeTag
        ]
        retrieveTimes = len(alreadyRetrieved)
        retrieveTimesName = retrieveTimesNamer(retrieveTimes + 1)

        print(f"| retrieve times: {retrieveTimes}, overwrite: {overwrite}")
        if retrieveTimes > 1 and overwrite == False:
            print("| Overwrite not triggerred, read existed data.")
            lastTimeDate = self.currentMultiManager.multicommons.datetimes[
                retrieveTimesNamer(retrieveTimes)]
            print(
                f"| Last retrieve by: {retrieveTimesNamer(retrieveTimes)} at {lastTimeDate}"
            )
            print(f"| Seems to there are some retrieves before.")
            print(
                f"| You can use `overwrite=True` to overwrite the previous retrieve."
            )

            return self.currentMultiManager.beforewards.jobID

        if overwrite:
            print(f"| Overwrite the previous retrieve.")
        self.currentMultiManager.afterwards.reset(security=True, muteWarning=True)
        assert len(self.currentMultiManager.afterwards.allCounts
                   ) == 0, "All counts should be null."

        current = currentTime()
        self.currentMultiManager.multicommons.datetimes[
            retrieveTimesName] = current

        retrieveProgressBar = qurryProgressBar(
            self.currentMultiManager.beforewards.jobID,
            bar_format=(
                '| {n_fmt}/{total_fmt} - retrieve: {desc} - {elapsed} < {remaining}'
            ),
        )

        for pendingID, pk in retrieveProgressBar:
            if pendingID is None:
                warnings.warn(f"Pending pool '{pk}' is empty.")
                continue
            retrieveProgressBar.set_description_str(f"{pk}/{pendingID}")
            pendingMapping[pk] = IBMQRetrieve(
                ibmqJobManager=self.JobManager,
                jobID=pendingID,
                provider=provider,
                refresh=refresh,
            )

        pendingPoolProgressBar = qurryProgressBar(
            self.currentMultiManager.beforewards.pendingPools.items(),
            bar_format=(
                '| {n_fmt}/{total_fmt} - get counts: {desc} - {elapsed} < {remaining}'
            ),
        )

        for pk, pcircs in pendingPoolProgressBar:
            if len(pcircs) > 0:
                pendingJob = pendingMapping[pk]
                pendingPoolProgressBar.set_description_str(
                    f"{pk}/{pendingJob.jobID}/{pendingJob.name}")
                self.reports[pendingJob.jobID] = {
                    'time': current,
                    'type': 'retrieve',
                    'report': pendingJob.report
                }

                if pendingJob.managedJob is not None:
                    pResult = pendingJob.managedJob.results()
                    counts = get_counts(
                        result=pResult,
                        resultIdxList=[rk - pcircs[0] for rk in pcircs])
                    pendingPoolProgressBar.set_description_str(
                        f"{pk}/{pendingJob.jobID}/{pendingJob.name} - len: {len(counts)}")
                else:
                    counts = get_counts(
                        result=None,
                        resultIdxList=[rk - pcircs[0] for rk in pcircs])
                    pendingPoolProgressBar.set_description_str(
                        f"{pk}/{pendingJob.jobID}/{pendingJob.name} - len: {len(counts)}")
                for rk in pcircs:
                    coutsTmpContainer[rk] = counts[rk - pcircs[0]]
                    pendingPoolProgressBar.set_description_str(
                        f"{pk}/{pendingJob.jobID}/{pendingJob.name} - " +
                        f"Packing: {rk} with len {len(counts[rk - pcircs[0]])}")

            else:
                warnings.warn(f"Pending pool '{pk}' is empty.")

        distributingProgressBar = qurryProgressBar(
            self.currentMultiManager.beforewards.circuitsMap.items(),
            bar_format=(
                '| {n_fmt}/{total_fmt} - Distributing {desc} - {elapsed} < {remaining}'
            ),
        )
        for currentID, idxCircs in distributingProgressBar:
            distributingProgressBar.set_description_str(
                f"{currentID} with {len(idxCircs)} circuits")
            self.expContainer[currentID].reset_counts(
                summonerID=self.currentMultiManager.summonerID)
            for idx in idxCircs:
                self.expContainer[currentID].afterwards.counts.append(
                    coutsTmpContainer[idx])
            self.expContainer[currentID].commons.datetimes[
                retrieveTimesName] = current
            self.currentMultiManager.afterwards.allCounts[
                currentID] = self.expContainer[currentID].afterwards.counts

        return self.currentMultiManager.beforewards.jobID


def IBMQPending(
    ibmqJobManager: IBMQJobManager,
    experiments: list[QuantumCircuit],
    backend: IBMQBackend,
    shots: int = 1024,
    name: str = 'qurryV5',
    managerRunArgs: dict[str, Any] = {},
) -> QurryIBMQBackendIO:
    """Pending circuits to `IBMQ`

    Args:
        ibmqJobManager (IBMQJobManager): The instance of :cls:`IBMQJobManager`.
        experiments (list[QuantumCircuit]): The list of circuits to run.
        backend (IBMQBackend): The IBMQ backend instance.
        shots (int, optional): Shots for IBMQ backends. Defaults to 1024.
        name (str, optional): Jobs name for IBMQ backends. Defaults to 'qurryV5'.
        managerRunArgs (dict[str, any], optional): Extra arguments for `IBMQManager.run`. Defaults to {}.

    Returns:
        QurryIBMQPackage: Returns a `QurryIBMQPackage` with the following attributes:
    """

    pendingJob = ibmqJobManager.run(
        **managerRunArgs,
        experiments=experiments,
        backend=backend,
        shots=shots,
        name=name,
    )
    jobID = pendingJob.job_set_id()
    report = pendingJob.report()
    name = pendingJob.name()

    return QurryIBMQBackendIO(managedJob=pendingJob,
                              jobID=jobID,
                              report=report,
                              name=name,
                              type='pending')


def IBMQRetrieve(
    ibmqJobManager: IBMQJobManager,
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
        retrievedJob = ibmqJobManager.retrieve_job_set(
            job_set_id=jobID,
            provider=provider,
            refresh=refresh,
        )
        jobID = retrievedJob.job_set_id()
        report = retrievedJob.report()
        name = retrievedJob.name()

    except IBMQJobManagerInvalidStateError as e:
        retrievedJob = None
        jobID = jobID
        report = f"Job unreachable, '{e}'."
        name = ''

    except IBMQError as e:
        retrievedJob = None
        jobID = jobID
        report = f"Job fully corrupted, '{e}'."
        name = ''

    return QurryIBMQBackendIO(managedJob=retrievedJob,
                              jobID=jobID,
                              report=report,
                              name=name,
                              type='retrieve')
