from qiskit.providers import Backend

from typing import Literal, Union

from .runner import Runner
from ..multimanager import MultiManager
from ..container import ExperimentContainer
from ...hoshi import Hoshi
from ...exceptions import QurryExtraPackageRequired, QurryInvalidArgument

backendChoiceLiteral = Literal[
    "IBMQ",
    "IBM",
    "Qulacs",
    "AWS_Bracket",
    "Azure_Q"
]
backendChoice = [
    "IBMQ",
    "IBM",
    # "Qulacs",
    # "AWS_Bracket",
    # "Azure_Q"
]


def acessibility() -> dict[str, bool]:
    """Return the acessibility of extra backend.

    Returns:
        dict[str, bool]: The acessibility of extra backend.
    """
    result: dict[backendChoiceLiteral, bool] = dict.fromkeys(
        backendChoice, False)

    try:
        from .ibmqrunner import IBMQRunner
        result['IBMQ'] = True
    except QurryExtraPackageRequired:
        ...

    try:
        from .ibmqrunner import IBMQRunner
        result['IBM'] = True
    except QurryExtraPackageRequired:
        ...

    # try:
    #     from .qulacsrunner import QulacsRunner
    #     result['Qulacs'] = True
    # except QurryExtraPackageRequired:
    #     ...

    return result


BACKEND_AVAILABLE: dict[
    Union[str, backendChoiceLiteral], 
    bool
] = dict.fromkeys(acessibility())
"""Acessibility of extra backend.

If you want to use extra backend, you should install the extra package first.
But if you install them but still get `False` in this dict,
it may be caused by the current version of Qurry is not yet supported it.

More information or question about this, please contact the developer of Qurry.
You can find the contact information in https://github.com/harui2019/qurry.

"""

BACKEND_AVAILABLE_MESSAGE = Hoshi(
    [
        ('h1', "Acessibility of extra backend"),
        *[
            ('itemize', str(k), str(v), '', 2)
            for k, v in BACKEND_AVAILABLE.items()],
        (
            'txt',
            "If you install them but still get `False` in this dict, "
        ),
        (
            'txt',
            "it may be caused by the current version of Qurry is not yet supported it."
        ),
        (
            'txt',
            "More information or question about this, please contact the developer of Qurry."
        )
    ],
    name='BACKEND_AVAILABLE_MESSAGE',
)


class ExtraBackendAccessor:

    multirunner: Runner = None
    """The excutor of extra backend."""
    jobs: list[tuple[str, str]] = None
    """The list of pending jobs or retrieving jobs."""
    jobs_info: Hoshi = None
    """The information of pending jobs or retrieving jobs."""

    backendType: backendChoiceLiteral = None
    """The backend type been used."""

    def __init__(
        self,
        multimanager: MultiManager,
        experimentContainer: ExperimentContainer,
        backend: Backend,
        backendType: backendChoiceLiteral,
    ):

        if backendType == 'IBMQ':
            if not BACKEND_AVAILABLE['IBMQ']:
                raise QurryExtraPackageRequired(
                    "Backend 'IBMQ' is not available, please install 'qiskit_ibmq_provider' first.")
            from .ibmqrunner import IBMQRunner, IBMQBackend

            if not isinstance(backend, IBMQBackend):
                raise ValueError(
                    "You must use 'IBMQBackend' from 'qiskit_ibmq_provider' " +
                    "which imports from 'qiskit.providers.ibmq' for 'IBMQ' jobsType. " +
                    "If you import backend or provider from 'qiskit_ibm_provider', " +
                    "it used 'IBMBackend' for 'IBM' jobsType, " +
                    "which is different from 'IBMQBackend'.")

            self.multirunner: IBMQRunner = IBMQRunner(
                besummonned=multimanager.summonerID,
                multimanager=multimanager,
                backend=backend,
                experimentalContainer=experimentContainer,
            )

        elif backendType == 'IBM':
            if not BACKEND_AVAILABLE['IBM']:
                raise QurryExtraPackageRequired(
                    "Backend 'IBM' is not available, please install 'qiskit_ibm_provider' first.")
            from .ibmrunner import IBMRunner, IBMBackend

            self.multirunner: IBMRunner = IBMRunner(
                besummonned=multimanager.summonerID,
                multimanager=multimanager,
                backend=backend,
                experimentalContainer=experimentContainer,
            )

        else:
            self.multirunner = Runner()
            self.jobs = []

            print(BACKEND_AVAILABLE_MESSAGE)
            raise QurryInvalidArgument(
                f"{backendType} which is not supported.")

        self.backendType = backendType

    def pending(
        self,
        pendingStrategy: Literal[
            'default', 'onetime', 'each', 'tags'] = 'default',
    ) -> tuple[str, list[tuple[str, str]]]:
        """Pending jobs to remote backend."""

        self.jobs = self.multirunner.pending(
            pendingStrategy=pendingStrategy,
        )
        self.jobs_info = Hoshi(
            [
                ('h1', "Pending info for '{}' by '{}'".format(
                    self.multirunner.currentMultimanager.summonerID, self.backendType)),
                *[('itemize', jobTag, jobID, '', 2)
                  for jobID, jobTag in self.jobs],
            ]
        )
        if len(self.jobs) == 0:
            self.jobs_info.newline(('txt', "No pending job."))

        return self.multirunner.currentMultimanager.summonerID, self.jobs

    def retrieve(
        self,
        overwrite: bool = False,
        **otherArgs: any
    ) -> tuple[str, list[tuple[str, str]]]:
        """Retrieve jobs from remote backend."""

        self.jobs = self.multirunner.retrieve(
            overwrite=overwrite,
            **otherArgs
        )
        self.jobs_info = Hoshi(
            [
                ('h1', "Retriving info for '{}' by '{}'".format(
                    self.multirunner.currentMultimanager.summonerID, self.backendType)),
                *[('itemize', jobTag, jobID, '', 2)
                  for jobID, jobTag in self.jobs],
            ]
        )
        if len(self.jobs) == 0:
            self.jobs_info.newline(('txt', "No pending job."))

        return self.multirunner.currentMultimanager.summonerID, self.jobs
