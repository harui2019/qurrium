from qiskit import QuantumCircuit
from qiskit.providers import Backend
from qiskit.providers.ibmq import IBMQBackend, IBMQJobManager, AccountProvider
from qiskit.providers.ibmq.managed import ManagedJobSet, IBMQJobManagerInvalidStateError
from qiskit.providers.ibmq.exceptions import IBMQError

from typing import Literal, NamedTuple, Hashable, Any

from .multimanager import MultiManager
from ..container import ExperimentContainer


class QurryIBMQPackage(NamedTuple):
    managedJob: ManagedJobSet
    jobID: str
    report: str
    name: str
    type: Literal['pending', 'retrieve']

class IBMQRunner:
    
    currentMultiJob: MultiManager
    backend: Backend

    jobID: str
    report: str
    name: str
    type: Literal['pending', 'retrieve']
    
    JobManager: IBMQJobManager()
    
    def __init__(
        self,
        besummonned: Hashable,
        multiJob: MultiManager, 
        backend: Backend,
        experimentalContainer: ExperimentContainer
    ):
        assert multiJob.summonerID == besummonned
        self.currentMultiJob = multiJob
        self.backend = backend
        self.expContainer = experimentalContainer
        
        self.JobManager = IBMQJobManager()
        self.circWithSerial = {}
        
    def pending(
        self,
        pendingStrategy: str = 'default',
    ):
        for id_exec in self.currentMultiJob.beforewards.configDict:
            circSerialLen = len(self.circWithSerial)
            for idx, circ in enumerate(self.expContainer[id_exec].beforewards.circuit):
                self.circWithSerial[idx+circSerialLen] = circ
                self.currentMultiJob.beforewards.circuitsMap[id_exec].append(idx+circSerialLen)
                
                
        pendingJob01 = self.JobManager.run(
            experiments=list(self.circWithSerial.values()),
            backend=self.backend,
            shots=1024,
            name='qurryV5',
        )
            

def pending(
    ibmqJobManager: IBMQJobManager,
    experiments: list[QuantumCircuit],
    backend: IBMQBackend,
    shots: int = 1024,
    name: str = 'qurryV5',
    managerRunArgs: dict[str, Any] = {},
) -> QurryIBMQPackage:
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

    return QurryIBMQPackage(
        managedJob=pendingJob,
        jobID=jobID,
        report=report,
        name=name,
        type='pending'
    )


def retrieve(
    ibmqJobManager: IBMQJobManager,
    jobID: str,
    provider: AccountProvider,
    refresh: bool = False,
) -> QurryIBMQPackage:
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

    return QurryIBMQPackage(
        managedJob=retrievedJob,
        jobID=jobID,
        report=report,
        name=name,
        type='retrieve'
    )
