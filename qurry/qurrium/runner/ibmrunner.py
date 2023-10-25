from ...exceptions import QurryExtraPackageRequired
try:
    from qiskit.providers.ibmq import IBMQBackend
    from qiskit.providers.ibmq.job import IBMQJob
    from qiskit.providers.ibmq.exceptions import IBMQBackendApiError
    qiskit_ibmq_provider = True
except ImportError:
    qiskit_ibmq_provider = False
try: 
    from qiskit_ibm_provider import IBMBackend, IBMProvider
    from qiskit_ibm_provider.job import IBMCircuitJob
    from qiskit_ibm_provider.exceptions import IBMBackendApiError
except ImportError:
    raise QurryExtraPackageRequired(
        "These module requires the install of `qiskit-ibm-provider`, please intall it then restart kernel.")
from qiskit import QuantumCircuit
from typing import Literal, Hashable, Union, Optional
import warnings
import time

from typing import Iterable

from .runner import Runner
from ..multimanager import MultiManager
from ..container import ExperimentContainer
from ..utils import get_counts, current_time
from ...tools import qurryProgressBar


class IBMRunner(Runner):
    """Pending and Retrieve Jobs from IBM backend."""
    
    backend: IBMBackend
    """The backend been used."""
    reports: dict[str, dict[str, str]]

    def __init__(
        self,
        besummonned: Hashable,
        multimanager: MultiManager,
        experimentalContainer: ExperimentContainer,
        backend: Optional[IBMBackend] = None,
        provider: Optional[IBMProvider] = None,
    ):
        assert multimanager.summonerID == besummonned, (
            f"Summoner ID not match, multimanager.summonerID: {multimanager.summonerID}, besummonned: {besummonned}"
        )
        if backend is None and provider is None:
            raise ValueError(
                "Either backend or provider should be provided."
            )

        self.currentMultimanager = multimanager
        """The multimanager from Qurry instance."""
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

        begin = time.time()
        distributingPendingProgressBar = qurryProgressBar(
            self.currentMultimanager.beforewards.expsConfig,
            bar_format='| {n_fmt}/{total_fmt} - Preparing pending pool - {elapsed} < {remaining}',
            # leave=False,
        )

        for id_exec in distributingPendingProgressBar:
            circSerialLen = len(self.circWithSerial)
            for idx, circ in enumerate(
                    self.expContainer[id_exec].beforewards.circuit):
                self.currentMultimanager.beforewards.circuitsMap[id_exec].append(
                    idx + circSerialLen)

                if pendingStrategy == 'each':
                    self.currentMultimanager.beforewards.pendingPools[
                        id_exec].append(idx + circSerialLen)

                elif pendingStrategy == 'tags':
                    tags = self.expContainer[id_exec].commons.tags
                    self.currentMultimanager.beforewards.pendingPools[tags].append(
                        idx + circSerialLen)

                else:
                    if pendingStrategy != 'default' or pendingStrategy != 'onetime':
                        warnings.warn(
                            f"Unknown strategy '{pendingStrategy}, use 'onetime'."
                        )
                    self.currentMultimanager.beforewards.pendingPools[
                        '_onetime'].append(idx + circSerialLen)

                self.circWithSerial[idx + circSerialLen] = circ

        current = current_time()
        self.currentMultimanager.multicommons.datetimes['pending'] = current

        pendingPoolProgressBar = qurryProgressBar(
            self.currentMultimanager.beforewards.pendingPools.items(),
            bar_format='| {n_fmt}/{total_fmt} - pending: {desc} - {elapsed} < {remaining}',
            # leave=False,
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
                    shots=self.currentMultimanager.multicommons.shots,
                    job_tags=[str(s) for s in [
                        self.currentMultimanager.multicommons.summonerName,
                        self.currentMultimanager.multicommons.summonerID,
                        self.currentMultimanager.namingCpx.expsName,
                        *pendingTag,
                        *self.currentMultimanager.multicommons.tags,
                    ]],
                    **self.currentMultimanager.multicommons.managerRunArgs,
                )
                pendingPoolProgressBar.set_description_str(
                    f"{pk}/{pendingJob.job_id()}/{pendingJob.tags()}")
                self.currentMultimanager.beforewards.jobID.append(
                    (pendingJob.job_id(), pk))
                self.reports[pendingJob.job_id()] = {
                    'time': current,
                    'type': 'pending',
                }

            else:
                self.currentMultimanager.beforewards.jobID.append((None, pk))
                warnings.warn(f"| Pending pool '{pk}' is empty.")
        # print(f"| Pending time: {time.time() - begin:.2f}s with {len(pendingPoolProgressBar)} jobs.")

        for id_exec in self.currentMultimanager.beforewards.expsConfig:
            self.expContainer[id_exec].commons.datetimes['pending'] = current

        self.currentMultimanager.multicommons.datetimes[
            'pendingCompleted'] = current_time()

        return self.currentMultimanager.beforewards.jobID

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
            for datetimeTag in self.currentMultimanager.multicommons.datetimes
            if 'retrieve' in datetimeTag
        ]
        retrieveTimes = len(alreadyRetrieved)
        retrieveTimesName = retrieveTimesNamer(retrieveTimes + 1)

        if retrieveTimes > 1 and overwrite == False:
            print(f"| retrieve times: {retrieveTimes}, overwrite: {overwrite}")
            lastTimeDate = self.currentMultimanager.multicommons.datetimes[
                retrieveTimesNamer(retrieveTimes)]
            print(
                f"| Last retrieve by: {retrieveTimesNamer(retrieveTimes)} at {lastTimeDate}"
            )
            print(f"| Seems to there are some retrieves before.")
            print(
                f"| You can use `overwrite=True` to overwrite the previous retrieve."
            )

            return self.currentMultimanager.beforewards.jobID

        if overwrite:
            print(f"| Overwrite the previous retrieve.")
        self.currentMultimanager.reset_afterwards(security=True, muteWarning=True)
        assert len(self.currentMultimanager.afterwards.allCounts
                   ) == 0, "All counts should be null."

        current = current_time()
        self.currentMultimanager.multicommons.datetimes[
            retrieveTimesName] = current

        if qiskit_ibmq_provider:
            print("| Downgrade compatibility with qiskit-ibmq-provider is available.")
        begin = time.time()
        retrieveProgressBar = qurryProgressBar(
            self.currentMultimanager.beforewards.jobID,
            bar_format='| {n_fmt}/{total_fmt} - retrieve: {desc} - {elapsed} < {remaining}',
            # leave=False,
        )

        if qiskit_ibmq_provider:
            if isinstance(self.backend, IBMQBackend):
                for pendingID, pk in retrieveProgressBar:
                    if pendingID is None:
                        warnings.warn(f"Pending pool '{pk}' is empty.")
                        continue
                    try:
                        retrieveProgressBar.set_description_str(
                            f"{pk}/{pendingID}", refresh=True)
                        pendingMapping[pk] = self.backend.retrieve_job(
                            job_id=pendingID)
                    except IBMQBackendApiError as e:
                        pendingMapping[pk] = None
                        retrieveProgressBar.set_description_str(
                            f"{pk}/{pendingID} - Error: {e}", refresh=True)

            else:
                provider: IBMProvider = self.backend.provider
                for pendingID, pk in retrieveProgressBar:
                    if pendingID is None:
                        warnings.warn(f"Pending pool '{pk}' is empty.")
                        continue
                    if isinstance(pk, str):
                        ...
                    elif isinstance(pk, Iterable) and not isinstance(pk, tuple):
                        pk = tuple(pk)
                    try:
                        retrieveProgressBar.set_description_str(
                            f"{pk}/{pendingID}", refresh=True)
                        pendingMapping[pk] = provider.retrieve_job(
                            job_id=pendingID)
                    except IBMBackendApiError as e:
                        pendingMapping[pk] = None
                        retrieveProgressBar.set_description_str(
                            f"{pk}/{pendingID} - Error: {e}", refresh=True)

        else:
            provider: IBMProvider = self.backend.provider
            for pendingID, pk in retrieveProgressBar:
                if pendingID is None:
                    warnings.warn(f"Pending pool '{pk}' is empty.")
                    continue
                try:
                    retrieveProgressBar.set_description_str(
                        f"{pk}/{pendingID}", refresh=True)
                    pendingMapping[pk] = provider.retrieve_job(
                        job_id=pendingID)
                except IBMBackendApiError as e:
                    retrieveProgressBar.set_description_str(
                        f"{pk}/{pendingID} - Error: {e}", refresh=True)
                    pendingMapping[pk] = None
        # print(f"| Retrieve time: {time.time() - begin:.2f}s with {len(retrieveProgressBar)} jobs.")

        begin = time.time()
        pendingPoolProgressBar = qurryProgressBar(
            self.currentMultimanager.beforewards.pendingPools.items(),
            bar_format=(
                '| {n_fmt}/{total_fmt} - get counts: {desc} - {elapsed} < {remaining}'
            ),
            # leave=False,
        )

        for pk, pcircs in pendingPoolProgressBar:
            if len(pcircs) > 0:
                pendingJob = pendingMapping[pk]
                if pendingJob is not None:
                    pendingPoolProgressBar.set_description_str(
                        f"{pk}/{pendingJob.job_id()}/{pendingJob.tags()}", refresh=True)
                    self.reports[pendingJob.job_id()] = {
                        'time': current,
                        'type': 'retrieve',
                    }

                    pResult = pendingJob.result()
                    counts = get_counts(
                        result=pResult,
                        resultIdxList=[rk - pcircs[0] for rk in pcircs])
                else:
                    pendingPoolProgressBar.set_description_str(
                        f"{pk} failed - No available tags", refresh=True)

                    counts = get_counts(
                        result=None,
                        resultIdxList=[rk - pcircs[0] for rk in pcircs])
                    pendingPoolProgressBar.set_description_str(
                        f"{pk} failed - No available tags - {len(counts)}", refresh=True)

                for rk in pcircs:
                    coutsTmpContainer[rk] = counts[rk - pcircs[0]]
                    pendingPoolProgressBar.set_description_str(
                        f"{pk} - Packing: {rk} with len {len(counts[rk - pcircs[0]])}", refresh=True)

            else:
                warnings.warn(f"Pending pool '{pk}' is empty.")
        # print(f"| Get counts time: {time.time() - begin:.2f}s from {len(pendingPoolProgressBar)} pending pools.")

        begin = time.time()
        distributingProgressBar = qurryProgressBar(
            self.currentMultimanager.beforewards.circuitsMap.items(),
            bar_format=(
                '| {n_fmt}/{total_fmt} - Distributing {desc} - {elapsed} < {remaining}'
            ),
            # leave=False,
        )
        for currentID, idxCircs in distributingProgressBar:
            distributingProgressBar.set_description_str(
                f"{currentID} with {len(idxCircs)} circuits", refresh=True)
            self.expContainer[currentID].reset_counts(
                summonerID=self.currentMultimanager.summonerID)
            for idx in idxCircs:
                self.expContainer[currentID].afterwards.counts.append(
                    coutsTmpContainer[idx])
            self.expContainer[currentID].commons.datetimes[
                retrieveTimesName] = current
            self.currentMultimanager.afterwards.allCounts[
                currentID] = self.expContainer[currentID].afterwards.counts
        # print(f"| Distributing time: {time.time() - begin:.2f}s with {len(distributingProgressBar)} circuits.")

        return self.currentMultimanager.beforewards.jobID
