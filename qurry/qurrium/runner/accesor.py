"""
================================================================
Extra backend accessor (:mod:`qurry.qurrium.runner.accesor`)
================================================================

"""
from typing import Literal, Union
from qiskit.providers import Backend

from .runner import Runner, DummyRunner
from ..multimanager import MultiManager
from ..container import ExperimentContainer
from ...capsule.hoshi import Hoshi
from ...exceptions import QurryExtraPackageRequired, QurryInvalidArgument

BackendChoiceLiteral = Literal["IBMQ", "IBM", "Qulacs", "AWS_Bracket", "Azure_Q"]
BackendChoice = [
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
    result: dict[BackendChoiceLiteral, bool] = dict.fromkeys(BackendChoice, False)

    # pylint: disable=import-outside-toplevel, unused-import
    try:
        from .ibmqrunner import IBMQRunner

        result["IBMQ"] = True
    except QurryExtraPackageRequired:
        result["IBMQ"] = False

    try:
        from .ibmrunner import IBMRunner

        result["IBM"] = True
    except QurryExtraPackageRequired:
        result["IBM"] = False

    # try:
    #     from .qulacsrunner import QulacsRunner
    #     result['Qulacs'] = True
    # except QurryExtraPackageRequired:
    #     ...
    # pylint: enable=import-outside-toplevel, unused-import

    return result


BACKEND_AVAILABLE: dict[Union[str, BackendChoiceLiteral], bool] = acessibility()
"""Acessibility of extra backend.

If you want to use extra backend, you should install the extra package first.
But if you install them but still get `False` in this dict,
it may be caused by the current version of Qurry is not yet supported it.

More information or question about this, please contact the developer of Qurry.
You can find the contact information in https://github.com/harui2019/qurry.

"""

BACKEND_AVAILABLE_MESSAGE = Hoshi(
    [
        ("h1", "Acessibility of extra backend"),
        *[("itemize", str(k), str(v), "", 2) for k, v in BACKEND_AVAILABLE.items()],
        ("txt", "If you install them but still get `False` in this dict, "),
        (
            "txt",
            "it may be caused by the current version of Qurry is not yet supported it.",
        ),
        (
            "txt",
            "More information or question about this, please contact the developer of Qurry.",
        ),
    ],
    name="BACKEND_AVAILABLE_MESSAGE",
)


class ExtraBackendAccessor:
    """Accessor for extra backend."""

    multirunner: Runner = None
    """The excutor of extra backend."""
    jobs: list[tuple[str, str]] = None
    """The list of pending jobs or retrieving jobs."""
    jobs_info: Hoshi = None
    """The information of pending jobs or retrieving jobs."""

    backend_type: BackendChoiceLiteral = None
    """The backend type been used."""

    def __init__(
        self,
        multimanager: MultiManager,
        experiment_container: ExperimentContainer,
        backend: Backend,
        backend_type: BackendChoiceLiteral,
    ):
        # pylint: disable=import-outside-toplevel
        if backend_type == "IBMQ":
            if not BACKEND_AVAILABLE["IBMQ"]:
                raise QurryExtraPackageRequired(
                    "Backend 'IBMQ' is not available, please install 'qiskit_ibmq_provider' first."
                )
            from .ibmqrunner import IBMQRunner, IBMQBackend

            if not isinstance(backend, IBMQBackend):
                raise ValueError(
                    "You must use 'IBMQBackend' from 'qiskit_ibmq_provider' "
                    + "which imports from 'qiskit.providers.ibmq' for 'IBMQ' jobsType. "
                    + "If you import backend or provider from 'qiskit_ibm_provider', "
                    + "it used 'IBMBackend' for 'IBM' jobsType, "
                    + "which is different from 'IBMQBackend'."
                )

            self.multirunner: IBMQRunner = IBMQRunner(
                besummonned=multimanager.summonerID,
                multimanager=multimanager,
                backend=backend,
                experimental_container=experiment_container,
            )

        elif backend_type == "IBM":
            if not BACKEND_AVAILABLE["IBM"]:
                raise QurryExtraPackageRequired(
                    "Backend 'IBM' is not available, please install 'qiskit_ibm_provider' first."
                )
            from .ibmrunner import IBMRunner

            self.multirunner: IBMRunner = IBMRunner(
                besummonned=multimanager.summonerID,
                multimanager=multimanager,
                backend=backend,
                experimental_container=experiment_container,
            )

        else:
            self.multirunner = DummyRunner(
                manager=multimanager,
                backend=backend,
            )
            self.jobs = []

            print(BACKEND_AVAILABLE_MESSAGE)
            raise QurryInvalidArgument(f"{backend_type} which is not supported.")
        # pylint: enable=import-outside-toplevel

        self.backend_type = backend_type

    def pending(
        self,
        pending_strategy: Literal["default", "onetime", "each", "tags"] = "default",
    ) -> tuple[str, list[tuple[str, str]]]:
        """Pending jobs to remote backend."""

        self.jobs = self.multirunner.pending(
            pending_strategy=pending_strategy,
        )
        self.jobs_info = Hoshi(
            [
                (
                    "h1",
                    (
                        "Pending info for "
                        + f"'{self.multirunner.current_multimanager.summonerID}'"
                        + f"by '{self.backend_type}'"
                    ),
                ),
                *[("itemize", jobTag, jobID, "", 2) for jobID, jobTag in self.jobs],
            ]
        )
        if len(self.jobs) == 0:
            self.jobs_info.newline(("txt", "No pending job."))

        return self.multirunner.current_multimanager.summonerID, self.jobs

    def retrieve(
        self, overwrite: bool = False, **otherArgs: any
    ) -> tuple[str, list[tuple[str, str]]]:
        """Retrieve jobs from remote backend."""

        self.jobs = self.multirunner.retrieve(overwrite=overwrite, **otherArgs)
        self.jobs_info = Hoshi(
            [
                (
                    "h1",
                    (
                        "Retriving info  for"
                        + f"'{self.multirunner.current_multimanager.summonerID}'"
                        + f"by '{self.backend_type}'"
                    ),
                ),
                *[("itemize", jobTag, jobID, "", 2) for jobID, jobTag in self.jobs],
            ]
        )
        if len(self.jobs) == 0:
            self.jobs_info.newline(("txt", "No pending job."))

        return self.multirunner.current_multimanager.summonerID, self.jobs
