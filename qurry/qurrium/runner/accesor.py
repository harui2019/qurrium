"""
================================================================
Extra backend accessor (:mod:`qurry.qurrium.runner.accesor`)
================================================================

"""

from typing import Union, Optional
from qiskit.providers import Backend

from .runner import DummyRunner
from ..multimanager import (
    MultiManager,
    PendingTargetProviderLiteral,
    PENDING_TARGET_PROVIDER,
    PendingStrategyLiteral,
    TagListKeyable,
)
from ..container import ExperimentContainer
from ...capsule.hoshi import Hoshi
from ...exceptions import QurryExtraPackageRequired, QurryInvalidArgument


def acessibility() -> dict[PendingTargetProviderLiteral, bool]:
    """Return the acessibility of extra backend.

    Returns:
        dict[str, bool]: The acessibility of extra backend.
    """
    result: dict[PendingTargetProviderLiteral, bool] = dict.fromkeys(PENDING_TARGET_PROVIDER, False)

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


BACKEND_AVAILABLE: dict[PendingTargetProviderLiteral, bool] = acessibility()
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

    # """The excutor of extra backend."""
    jobs: list[tuple[Optional[str], TagListKeyable]]
    """The list of pending jobs or retrieving jobs."""
    jobs_info: Hoshi
    """The information of pending jobs or retrieving jobs."""

    backend_type: PendingTargetProviderLiteral
    """The backend type been used."""

    def __init__(
        self,
        multimanager: MultiManager,
        experiment_container: ExperimentContainer,
        backend: Backend,
        backend_type: Union[PendingTargetProviderLiteral, str],
    ):
        # pylint: disable=import-outside-toplevel
        if backend_type == "IBMQ":
            if not BACKEND_AVAILABLE["IBMQ"]:
                raise QurryExtraPackageRequired(
                    "Backend 'IBMQ' is not available, please install 'qiskit_ibmq_provider' first."
                )
            from .ibmqrunner import IBMQRunner, IBMQBackend  # type: ignore

            if not isinstance(backend, IBMQBackend):
                raise ValueError(
                    "You must use 'IBMQBackend' from 'qiskit_ibmq_provider' "
                    + "which imports from 'qiskit.providers.ibmq' for 'IBMQ' jobstype. "
                    + "If you import backend or provider from 'qiskit_ibm_provider', "
                    + "it used 'IBMBackend' for 'IBM' jobstype, "
                    + "which is different from 'IBMQBackend'."
                )

            self.multirunner = IBMQRunner(
                besummonned=multimanager.summoner_id,
                multimanager=multimanager,
                backend=backend,
                experimental_container=experiment_container,
            )

        elif backend_type == "IBM":
            if not BACKEND_AVAILABLE["IBM"]:
                raise QurryExtraPackageRequired(
                    "Backend 'IBM' is not available, please install 'qiskit_ibm_provider' first."
                )
            from .ibmrunner import IBMRunner, IBMBackend

            if not isinstance(backend, IBMBackend):
                raise TypeError(
                    "You must use 'IBMBackend' from 'qiskit_ibm_provider' "
                    + "which imports from 'qiskit.providers.ibm' for 'IBM' jobstype. "
                    + "If you import backend or provider from 'qiskit_ibmq_provider', "
                    + "it used 'IBMQBackend' for 'IBMQ' jobstype, "
                    + "which is different from 'IBMBackend'."
                )

            self.multirunner = IBMRunner(
                besummonned=multimanager.summoner_id,
                multimanager=multimanager,
                backend=backend,
                experimental_container=experiment_container,
            )

        else:
            self.multirunner = DummyRunner(
                manager=multimanager,
                backend=backend,
            )

            print(BACKEND_AVAILABLE_MESSAGE)
            raise QurryInvalidArgument(f"{backend_type} which is not supported.")
        # pylint: enable=import-outside-toplevel

        self.jobs = []
        self.backend_type = backend_type

    def pending(
        self,
        pending_strategy: PendingStrategyLiteral = "tags",
    ) -> tuple[str, list[tuple[Optional[str], TagListKeyable]]]:
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
                        + f"'{self.multirunner.current_multimanager.summoner_id}'"
                        + f"by '{self.backend_type}'"
                    ),
                ),
                *[("itemize", jobTag, job_id, "", 2) for job_id, jobTag in self.jobs],
            ]
        )
        if len(self.jobs) == 0:
            self.jobs_info.newline(("txt", "No pending job."))

        return self.multirunner.current_multimanager.summoner_id, self.jobs

    def retrieve(
        self, overwrite: bool = False, **other_kwargs: any
    ) -> tuple[str, list[tuple[Optional[str], TagListKeyable]]]:
        """Retrieve jobs from remote backend."""

        self.jobs = self.multirunner.retrieve(overwrite=overwrite, **other_kwargs)
        self.jobs_info = Hoshi(
            [
                (
                    "h1",
                    (
                        "Retriving info  for"
                        + f"'{self.multirunner.current_multimanager.summoner_id}'"
                        + f"by '{self.backend_type}'"
                    ),
                ),
                *[("itemize", jobTag, job_id, "", 2) for job_id, jobTag in self.jobs],
            ]
        )
        if len(self.jobs) == 0:
            self.jobs_info.newline(("txt", "No pending job."))

        return self.multirunner.current_multimanager.summoner_id, self.jobs
