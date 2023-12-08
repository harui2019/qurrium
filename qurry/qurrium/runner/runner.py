"""
================================================================
Runner for pending and retrieve jobs from remote backend.
(:mod:`qurry.qurrium.runner.runner`)
================================================================
"""
import warnings
from abc import abstractmethod, ABC
from typing import Optional, Literal
from qiskit.providers import Backend, Provider

from ..container import ExperimentContainer
from ..multimanager import MultiManager
from ...exceptions import QurryDummyRunnerWarning


class Runner(ABC):
    """Pending and Retrieve Jobs from remote backend."""

    current_multimanager: MultiManager
    """The current :cls:`Multimanager` been used."""
    backend: Optional[Backend]
    """The backend been used."""
    provider: Provider
    """The provider used for this backend."""
    experiment_container: ExperimentContainer
    """The experimental container from Qurry instance."""

    reports: dict[str, dict]
    """The reports of jobs."""

    @abstractmethod
    def pending(
        self,
        pending_strategy: Literal["default", "onetime", "each", "tags"],
        backend: Backend,
    ):
        """Pending jobs to remote backend."""

    @abstractmethod
    def retrieve(self):
        """Retrieve jobs from remote backend."""


class DummyRunner(Runner):
    """A dummy runner for testing."""

    def __init__(
        self,
        manager: MultiManager,
        backend: Backend,
    ):
        warnings.warn(
            "You are using a dummy runner, which does not support any jobs.",
            QurryDummyRunnerWarning,
        )
        self.current_multimanager = manager
        self.backend = backend
        self.provider = backend.provider()

        self.reports = {}

    def pending(
        self,
        pending_strategy: Literal["default", "onetime", "each", "tags"],
        backend: Backend,
    ):
        warnings.warn(
            "You are using a dummy runner, which does not support any jobs.",
            QurryDummyRunnerWarning,
        )

    def retrieve(self):
        warnings.warn(
            "You are using a dummy runner, which does not support any jobs.",
            QurryDummyRunnerWarning,
        )


# Using for Third-Party Backend


class ThirdPartyRunner(Runner):
    """Pending and Retrieve Jobs from Third-Parties' backend."""

    @abstractmethod
    def __init__(self, manager: MultiManager, backend: Backend, **kwargs):
        pass


def retrieve_times_namer(retrieve_times: int) -> str:
    """Retrieve times namer.

    Args:
        retrieve_times (int): The retrieve times.

    Returns:
        str: The retrieve times namer.
    """
    return "retrieve." + f"{retrieve_times}".rjust(3, "0")
