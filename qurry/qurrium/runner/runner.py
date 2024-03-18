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

from ..experiment import ExperimentPrototype
from ..container import ExperimentContainer
from ..multimanager import MultiManager
from ...tools import DatetimeDict
from ...exceptions import QurryDummyRunnerWarning


def retrieve_counter(datetimes_dict: DatetimeDict):
    """Count the number of retrieve jobs in the datetimes_dict.""

    Args:
        datetimes_dict (DatetimeDict): The datetimes_dict from Qurry instance.

    Returns:
        int: The number of retrieve jobs in the datetimes_dict.
    """
    return len(
        [datetime_tag for datetime_tag in datetimes_dict if "retrieve" in datetime_tag]
    )


class Runner(ABC):
    """Pending and Retrieve Jobs from remote backend."""

    current_multimanager: MultiManager
    """The current :cls:`Multimanager` been used."""
    backend: Optional[Backend]
    """The backend been used."""
    provider: Optional[Provider]
    """The provider used for this backend."""
    experiment_container: ExperimentContainer[ExperimentPrototype]
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
    def retrieve(self, overwrite: bool = False):
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
        self.provider = None

        self.reports = {}

    def pending(
        self,
        pending_strategy: Literal["default", "onetime", "each", "tags"],
        backend: Optional[Backend] = None,
    ):
        warnings.warn(
            "You are using a dummy runner, which does not support any jobs.",
            QurryDummyRunnerWarning,
        )
        return []

    def retrieve(self, overwrite: bool = False):
        print("Dummy runner does not support retrieve.", overwrite)
        warnings.warn(
            "You are using a dummy runner, which does not support any jobs.",
            QurryDummyRunnerWarning,
        )
        return []


# Using for Third-Party Backend


class ThirdPartyRunner(Runner):
    """Pending and Retrieve Jobs from Third-Parties' backend."""

    @abstractmethod
    def __init__(self, manager: MultiManager, backend: Backend, **kwargs):
        pass
