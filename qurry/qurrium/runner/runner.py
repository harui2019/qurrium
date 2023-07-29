from qiskit.providers import Backend, Provider

from abc import abstractmethod
from typing import Optional

from ..multimanager import MultiManager


class Runner:
    """Pending and Retrieve Jobs from remote backend."""

    currentMultimanager: MultiManager
    """The current :cls:`Multimanager` been used."""
    backend: Optional[Backend]
    """The backend been used."""
    provider: Provider
    """The provider used for this backend."""

    pendingIDs: str
    reports: dict[str, dict]

    @abstractmethod
    def pending(self, *args, **kwargs):
        pass

    @abstractmethod
    def retrieve(self, *args, **kwargs):
        pass


# Using for Third-Party Backend

class ThirdPartyRunner(Runner):
    """Pending and Retrieve Jobs from Third-Parties' backend."""

    currentMultimanager: MultiManager
    backend: Optional[Backend]
    provider: Provider

    pendingIDs: str
    reports: dict[str, dict]

    def __init__(
        self,
        manager: MultiManager,
        backend: Backend,

        max_experiments: int = 200,
        **otherArgs: any
    ):
        self.currentMultimanager = manager
        self.backend = backend
        self.circWithSerial = {}

    @abstractmethod
    def pending(self, *args, **kwargs):
        pass

    @abstractmethod
    def retrieve(self, *args, **kwargs):
        pass