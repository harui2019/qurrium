from qiskit import QuantumCircuit
try:
    from qiskit.providers.ibmq import IBMQBackend
    from qiskit.providers.ibmq.job import IBMQJob
    from qiskit.providers.ibmq.exceptions import IBMQBackendApiError
    qiskit_ibmq_provider = True
except ImportError:
    qiskit_ibmq_provider = False
from qiskit_ibm_provider import IBMBackend, IBMProvider
from qiskit_ibm_provider.job import IBMCircuitJob
from qiskit_ibm_provider.exceptions import IBMBackendApiError

from typing import Literal, Hashable, Union, Optional
import warnings
import tqdm

from .multimanager import MultiManager
from .runner import Runner
from ..container import ExperimentContainer
from ..utils import get_counts, currentTime


class IBMRunner(Runner):
    """Pending and Retrieve Jobs from IBM backend."""

    currentMultiJob: MultiManager
    backend: IBMBackend

    reports: dict[str, dict[str, str]]

    def __init__(
        self,
        besummonned: Hashable,
        multiJob: MultiManager,
        experimentalContainer: ExperimentContainer,
        backend: Optional[IBMBackend] = None,
        provider: Optional[IBMProvider] = None,
    ):
        assert multiJob.summonerID == besummonned, (
            f"Summoner ID not match, multiJob.summonerID: {multiJob.summonerID}, besummonned: {besummonned}"
        )
        if backend is None and provider is None:
            raise ValueError(
                "Either backend or provider should be provided."
            )

        self.currentMultiJob = multiJob
        """The multiJob from Qurry instance."""
        self.backend = backend
        """The backend will be use to pending and retrieve."""
        self.provider = backend.provider if backend is not None else provider
        """The provider will be used to pending and retrieve."""
        self.expContainer = experimentalContainer
        """The experimental container from Qurry instance."""

        self.circWithSerial: dict[int, QuantumCircuit] = {}

        self.reports = {}

    def pending(
        self,
        pendingStrategy: Literal['default', 'onetime', 'each',
                                 'tags'] = 'default',
        backend: Optional[IBMBackend] = None,
    ) -> list[tuple[str, str]]:

        if self.backend is None:
            if backend is None:
                raise ValueError(
                    "At least one of backend and provider should be given.")
            else:
                print(
                    f"| Given backend and provider as {backend.name} and {backend.provider()}.")
                self.backend = backend
                self.provider = backend.provider()
        else:
            if backend is not None:
                print(
                    f"| Using backend and provider as {self.backend.name} and {self.backend.provider()}.")
            else:
                ...

        distributingPendingProgressBar = tqdm.tqdm(
            self.currentMultiJob.beforewards.expsConfig,
            bar_format=(
                '| {n_fmt}/{total_fmt} - Preparing pending pool - {elapsed} < {remaining}'
            ),
        )

        for id_exec in distributingPendingProgressBar:
            circSerialLen = len(self.circWithSerial)
            for idx, circ in enumerate(
                    self.expContainer[id_exec].beforewards.circuit):
                self.currentMultiJob.beforewards.circuitsMap[id_exec].append(
                    idx + circSerialLen)

                if pendingStrategy == 'each':
                    self.currentMultiJob.beforewards.pendingPools[
                        id_exec].append(idx + circSerialLen)

                elif pendingStrategy == 'tags':
                    tags = self.expContainer[id_exec].commons.tags
                    self.currentMultiJob.beforewards.pendingPools[tags].append(
                        idx + circSerialLen)

                else:
                    if pendingStrategy != 'default' or pendingStrategy != 'onetime':
                        warnings.warn(
                            f"Unknown strategy '{pendingStrategy}, use 'onetime'."
                        )
                    self.currentMultiJob.beforewards.pendingPools[
                        '_onetime'].append(idx + circSerialLen)

                self.circWithSerial[idx + circSerialLen] = circ

        current = currentTime()
        self.currentMultiJob.multicommons.datetimes['pending'] = current

        pendingPoolProgressBar = tqdm.tqdm(
            self.currentMultiJob.beforewards.pendingPools.items(),
            bar_format=(
                '| {n_fmt}/{total_fmt} - pending: {desc} - {elapsed} < {remaining}'
            ),
        )

        for pk, pcircIdxs in pendingPoolProgressBar:
            if len(pcircIdxs) > 0:
                if pk == '_onetime':
                    pendingTag = []
                elif isinstance(pk, (list, tuple)):
                    pendingTag = list(pk)
                else:
                    pendingTag = [pk]

                pendingJob = self.backend.run(
                    circuits=[self.circWithSerial[idx] for idx in pcircIdxs],
                    shots=self.currentMultiJob.multicommons.shots,
                    job_tags=[
                        self.currentMultiJob.multicommons.summonerName,
                        self.currentMultiJob.multicommons.summonerID,
                        self.currentMultiJob.namingCpx.expsName,
                        *pendingTag,
                        *self.currentMultiJob.multicommons.tags,
                    ],
                    **self.currentMultiJob.multicommons.managerRunArgs,
                )
                pendingPoolProgressBar.set_description(
                    f"{pk}/{pendingJob.job_id()}/{pendingJob.tags()}")
                self.currentMultiJob.beforewards.jobID.append(
                    (pendingJob.job_id(), pk))
                self.reports[pendingJob.job_id()] = {
                    'time': current,
                    'type': 'pending',
                }

            else:
                self.currentMultiJob.beforewards.jobID.append((None, pk))
                warnings.warn(f"| Pending pool '{pk}' is empty.")

        for id_exec in self.currentMultiJob.beforewards.expsConfig:
            self.expContainer[id_exec].commons.datetimes['pending'] = current

        self.currentMultiJob.multicommons.datetimes[
            'pendingCompleted'] = currentTime()

        return self.currentMultiJob.beforewards.jobID

    def retrieve(
        self,
        overwrite: bool = False,
    ) -> list[tuple[str, str]]:

        pendingMapping: dict[Hashable, Union[IBMCircuitJob, 'IBMQJob']] = {}
        coutsTmpContainer: dict[str, dict[str, int]] = {}

        def retrieveTimesNamer(retrieveTimes):
            return 'retrieve.' + f'{retrieveTimes}'.rjust(3, '0')

        alreadyRetrieved: list[str] = [
            datetimeTag
            for datetimeTag in self.currentMultiJob.multicommons.datetimes
            if 'retrieve' in datetimeTag
        ]
        retrieveTimes = len(alreadyRetrieved)
        retrieveTimesName = retrieveTimesNamer(retrieveTimes + 1)

        if retrieveTimes > 1 and overwrite == False:
            print(f"| retrieve times: {retrieveTimes}, overwrite: {overwrite}")
            lastTimeDate = self.currentMultiJob.multicommons.datetimes[
                retrieveTimesNamer(retrieveTimes)]
            print(
                f"| Last retrieve by: {retrieveTimesNamer(retrieveTimes)} at {lastTimeDate}"
            )
            print(f"| Seems to there are some retrieves before.")
            print(
                f"| You can use `overwrite=True` to overwrite the previous retrieve."
            )

            return self.currentMultiJob.beforewards.jobID

        if overwrite:
            print(f"| Overwrite the previous retrieve.")
        self.currentMultiJob.reset_afterwards(security=True, muteWarning=True)
        assert len(self.currentMultiJob.afterwards.allCounts
                   ) == 0, "All counts should be null."

        current = currentTime()
        self.currentMultiJob.multicommons.datetimes[
            retrieveTimesName] = current

        if qiskit_ibmq_provider:
            print("| Downgrade compatibility with qiskit-ibmq-provider is available.")
            if isinstance(self.backend, IBMQBackend):

                retrieveProgressBar = tqdm.tqdm(
                    self.currentMultiJob.beforewards.jobID,
                    bar_format=(
                        '| {n_fmt}/{total_fmt} - retrieve: {desc} - {elapsed} < {remaining}'
                    ),
                )
                for pendingID, pk in retrieveProgressBar:
                    if pendingID is None:
                        warnings.warn(f"Pending pool '{pk}' is empty.")
                        continue
                    try:
                        retrieveProgressBar.set_description(
                            f"{pk}/{pendingID}")
                        pendingMapping[pk] = self.backend.retrieve_job(
                            job_id=pendingID)
                    except IBMQBackendApiError as e:
                        pendingMapping[pk] = None
                        retrieveProgressBar.set_description(
                            f"{pk}/{pendingID} - Error: {e}")

            else:
                provider: IBMProvider = self.backend.provider

                retrieveProgressBar = tqdm.tqdm(
                    self.currentMultiJob.beforewards.jobID,
                    bar_format=(
                        '| {n_fmt}/{total_fmt} - retrieve: {desc} - {elapsed} < {remaining}'
                    ),
                )
                for pendingID, pk in retrieveProgressBar:
                    if pendingID is None:
                        warnings.warn(f"Pending pool '{pk}' is empty.")
                        continue
                    try:
                        retrieveProgressBar.set_description(
                            f"{pk}/{pendingID}")
                        pendingMapping[pk] = provider.retrieve_job(
                            job_id=pendingID)
                    except IBMBackendApiError as e:
                        pendingMapping[pk] = None
                        retrieveProgressBar.set_description(
                            f"{pk}/{pendingID} - Error: {e}")

        else:
            provider: IBMProvider = self.backend.provider
            retrieveProgressBar = tqdm.tqdm(
                self.currentMultiJob.beforewards.jobID,
                bar_format=(
                    '| {n_fmt}/{total_fmt} - retrieve: {desc} - {elapsed} < {remaining}'
                ),
            )
            for pendingID, pk in retrieveProgressBar:
                if pendingID is None:
                    warnings.warn(f"Pending pool '{pk}' is empty.")
                    continue
                try:
                    retrieveProgressBar.set_description(
                        f"{pk}/{pendingID}")
                    pendingMapping[pk] = provider.retrieve_job(
                        job_id=pendingID)
                    retrieveProgressBar.set_description(f"{pk}/{pendingID}")
                except IBMBackendApiError as e:
                    retrieveProgressBar.set_description(
                        f"{pk}/{pendingID} - Error: {e}")
                    pendingMapping[pk] = None

        pendingPoolProgressBar = tqdm.tqdm(
            self.currentMultiJob.beforewards.pendingPools.items(),
            bar_format=(
                '| {n_fmt}/{total_fmt} - get counts: {desc} - {elapsed} < {remaining}'
            ),
        )

        for pk, pcircs in pendingPoolProgressBar:
            if len(pcircs) > 0:
                pendingJob = pendingMapping[pk]
                if pendingJob is not None:
                    pendingPoolProgressBar.set_description(
                        f"{pk}/{pendingJob.job_id()}/{pendingJob.tags()}")
                    self.reports[pendingJob.job_id()] = {
                        'time': current,
                        'type': 'retrieve',
                    }

                    pResult = pendingJob.result()
                    counts = get_counts(
                        result=pResult,
                        resultIdxList=[rk - pcircs[0] for rk in pcircs])
                    pendingPoolProgressBar.set_description(
                        f"{pk}/{pendingJob.job_id()}/{pendingJob.tags()} - {len(counts)}")
                else:
                    pendingPoolProgressBar.set_description(
                        f"{pk} failed - No available tags")

                    counts = get_counts(
                        result=None,
                        resultIdxList=[rk - pcircs[0] for rk in pcircs])
                    pendingPoolProgressBar.set_description(
                        f"{pk} failed - No available tags - {len(counts)}")

                for rk in pcircs:
                    coutsTmpContainer[rk] = counts[rk - pcircs[0]]
                    pendingPoolProgressBar.set_description(
                        f"{pk} - Packing: {rk} with len {len(counts[rk - pcircs[0]])}")

            else:
                warnings.warn(f"Pending pool '{pk}' is empty.")

        distributingProgressBar = tqdm.tqdm(
            self.currentMultiJob.beforewards.circuitsMap.items(),
            bar_format=(
                '| {n_fmt}/{total_fmt} - Distributing {desc} - {elapsed} < {remaining}'
            ),
        )
        for currentID, idxCircs in distributingProgressBar:
            distributingProgressBar.set_description(
                f"{currentID} with {len(idxCircs)} circuits")
            self.expContainer[currentID].reset_counts(
                summonerID=self.currentMultiJob.summonerID)
            for idx in idxCircs:
                self.expContainer[currentID].afterwards.counts.append(
                    coutsTmpContainer[idx])
            self.expContainer[currentID].commons.datetimes[
                retrieveTimesName] = current
            self.currentMultiJob.afterwards.allCounts[
                currentID] = self.expContainer[currentID].afterwards.counts

        return self.currentMultiJob.beforewards.jobID
