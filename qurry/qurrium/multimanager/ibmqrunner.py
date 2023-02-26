from qiskit import QuantumCircuit
from qiskit.providers import Backend
from qiskit.providers.ibmq import IBMQBackend, IBMQJobManager, AccountProvider
from qiskit.providers.ibmq.managed import ManagedJobSet, IBMQJobManagerInvalidStateError
from qiskit.providers.ibmq.exceptions import IBMQError

from typing import Literal, NamedTuple, Hashable, Any
from datetime import datetime
import warnings

from .multimanager import MultiManager
from .runner import Runner
from ..container import ExperimentContainer
from ..utils import get_counts


class QurryIBMQBackendIO(NamedTuple):

    managedJob: ManagedJobSet
    jobID: str
    report: str
    name: str
    type: Literal['pending', 'retrieve']


class IBMQRunner(Runner):
    """Pending and Retrieve Jobs from IBMQ backend."""

    currentMultiJob: MultiManager
    backend: Backend

    reports: dict[str, dict[str, str]]

    JobManager: IBMQJobManager
    """JobManager for IBMQ"""

    def __init__(
        self,
        besummonned: Hashable,
        multiJob: MultiManager,
        backend: Backend,
        experimentalContainer: ExperimentContainer
    ):
        assert multiJob.summonerID == besummonned, (
            f"Summoner ID not match, multiJob.summonerID: {multiJob.summonerID}, besummonned: {besummonned}")
        self.currentMultiJob = multiJob
        """The multiJob from Qurry instance."""
        self.backend = backend
        """The backend will be use to pending and retrieve."""
        self.expContainer = experimentalContainer
        """The experimental container from Qurry instance."""

        self.JobManager = IBMQJobManager()
        """JobManager for IBMQ"""
        self.circWithSerial: dict[int, QuantumCircuit] = {}

        self.reports = {}

    def pending(
        self,
        pendingStrategy: Literal[
            'default', 'onetime', 'each', 'tags'] = 'default',
    ) -> list[tuple[str, str]]:

        for id_exec in self.currentMultiJob.beforewards.configDict:
            circSerialLen = len(self.circWithSerial)
            for idx, circ in enumerate(self.expContainer[id_exec].beforewards.circuit):
                self.currentMultiJob.beforewards.circuitsMap[id_exec].append(
                    idx+circSerialLen)

                if pendingStrategy == 'each':
                    self.currentMultiJob.beforewards.pendingPools[id_exec].append(
                        idx+circSerialLen)

                elif pendingStrategy == 'tags':
                    tags = self.expContainer[id_exec].commons.tags
                    self.currentMultiJob.beforewards.pendingPools[tags].append(
                        idx+circSerialLen)

                else:
                    if pendingStrategy != 'default' or pendingStrategy != 'onetime':
                        warnings.warn(
                            f"Unknown strategy '{pendingStrategy}, use 'onetime'.")
                    self.currentMultiJob.beforewards.pendingPools['_onetime'].append(
                        idx+circSerialLen)

                self.circWithSerial[idx+circSerialLen] = circ

        current = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.currentMultiJob.multicommons.datetimes['pending'] = current

        for pk, pcircIdxs in self.currentMultiJob.beforewards.pendingPools.items():
            if len(pcircIdxs) > 0:
                if pk == '_onetime':
                    pendingName = f'{self.currentMultiJob.multicommons.summonerName}'
                elif isinstance(pk, (list, tuple)):
                    pendingName = f'{self.currentMultiJob.multicommons.summonerName}-{"-".join(pk)}'
                else:
                    pendingName = f'{self.currentMultiJob.multicommons.summonerName}-{pk}'

                pendingJob = IBMQPending(
                    ibmqJobManager=self.JobManager,
                    experiments=[self.circWithSerial[idx]
                                 for idx in pcircIdxs],
                    backend=self.backend,
                    shots=self.currentMultiJob.multicommons.shots,
                    name=pendingName,
                    managerRunArgs=self.currentMultiJob.multicommons.managerRunArgs,
                )
                self.currentMultiJob.beforewards.jobID.append(
                    (pendingJob.jobID, pk))
                self.reports[pendingJob.jobID] = {
                    'time': current,
                    'type': 'pending',
                    'report': pendingJob.report
                }
                print(f"| pending: {pk} - {pendingJob.jobID}")
                print(f"| report:", pendingJob.report)
                print(f"| name:", pendingJob.name)

            else:
                self.currentMultiJob.beforewards.jobID.append((None, pk))
                warnings.warn(f"Pending pool '{pk}' is empty.")

        for id_exec in self.currentMultiJob.beforewards.configDict:
            self.expContainer[id_exec].commons.datetimes['pending'] = current

        self.currentMultiJob.multicommons.datetimes['pendingCompleted'] = datetime.now(
        ).strftime("%Y-%m-%d %H:%M:%S")

        return self.currentMultiJob.beforewards.jobID

    def retrieve(
        self,
        provider: AccountProvider,
        refresh: bool = False,
        overwrite: bool = False,
    ) -> list[tuple[str, str]]:

        pendingMapping: dict[Hashable, QurryIBMQBackendIO] = {}
        coutsTmpContainer: dict[str, dict[str, int]] = {}
        def retrieveTimesNamer(
            retrieveTimes): return 'retrieve.'+f'{retrieveTimes}'.rjust(3, '0')

        alreadyRetrieved: list[str] = [
            datetimeTag for datetimeTag in self.currentMultiJob.multicommons.datetimes
            if 'retrieve' in datetimeTag]
        retrieveTimes = len(alreadyRetrieved)
        retrieveTimesName = retrieveTimesNamer(retrieveTimes)

        if retrieveTimes > 1 and overwrite == False:
            print(f"| retrieve times: {retrieveTimes-1}, overwrite: {overwrite}")
            lastTimeDate = self.currentMultiJob.multicommons.datetimes[
                retrieveTimesNamer(retrieveTimes-1)
            ]
            print(f"| Last retrieve by: {retrieveTimesNamer(retrieveTimes-1)} at {lastTimeDate}")
            print(f"| Seems to there are some retrieves before.")
            print(f"| You can use `overwrite=True` to overwrite the previous retrieve.")

            return self.currentMultiJob.beforewards.jobID
        
        if overwrite:
            print(f"| Overwrite the previous retrieve.")
            self.currentMultiJob.afterwards.reset(
                security=True, muteWarning=True)

        current = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.currentMultiJob.multicommons.datetimes[retrieveTimesName] = current

        for pendingID, pk in self.currentMultiJob.beforewards.jobID:
            if pendingID is None:
                warnings.warn(f"Pending pool '{pk}' is empty.")
                continue
            pendingMapping[pk] = IBMQRetrieve(
                ibmqJobManager=self.JobManager,
                jobID=pendingID,
                provider=provider,
                refresh=refresh,
            )

        for pk, pcircs in self.currentMultiJob.beforewards.pendingPools.items():
            if len(pcircs) > 0:
                pendingJob = pendingMapping[pk]
                self.reports[pendingJob.jobID] = {
                    'time': current,
                    'type': 'retrieve',
                    'report': pendingJob.report
                }
                print(f"| retrieve: {pk} - {pendingJob.jobID}")
                print(f"| report:", pendingJob.report)
                print(f"| name:", pendingJob.name)

                if pendingJob.managedJob is not None:
                    pResult = pendingJob.managedJob.results()
                    counts = get_counts(
                        result=pResult,
                        resultIdxList=[rk-pcircs[0] for rk in pcircs]
                    )
                    print("| Getting Counts length:", len(counts))
                else:
                    counts = get_counts(
                        result=None,
                        resultIdxList=[rk-pcircs[0] for rk in pcircs]
                    )
                    print("| Getting Counts length:", len(counts))
                for rk in pcircs:
                    coutsTmpContainer[rk] = counts[rk-pcircs[0]]
                    print(f"| Packing Counts of {rk} length:", len(
                        counts[rk-pcircs[0]]))

            else:
                warnings.warn(f"Pending pool '{pk}' is empty.")

        print("| Distributing all circuits to their original experimemts.")
        for currentID, idxCircs in self.currentMultiJob.beforewards.circuitsMap.items():
            print(
                f"| Distributing to {currentID} with {len(idxCircs)} circuits.")
            for idx in idxCircs:
                self.expContainer[currentID].afterwards.counts.append(
                    coutsTmpContainer[idx])
            self.expContainer[currentID].commons.datetimes[retrieveTimesName] = current
            self.currentMultiJob.afterwards.allCounts[
                currentID] = self.expContainer[currentID].afterwards.counts

        return self.currentMultiJob.beforewards.jobID


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

    return QurryIBMQBackendIO(
        managedJob=pendingJob,
        jobID=jobID,
        report=report,
        name=name,
        type='pending'
    )


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

    return QurryIBMQBackendIO(
        managedJob=retrievedJob,
        jobID=jobID,
        report=report,
        name=name,
        type='retrieve'
    )
