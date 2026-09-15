"""ExperimentContainerWrapper (:mod:`qurry.qurrium.qurrium.exps_wrapper`)"""

from typing import Generic, Any

from ..multimanager import MultiManager, ExperimentContainer, _E
from ...capsule import DEFAULT_INDENT


class ExperimentContainerWrapper(Generic[_E]):
    """A wrapper for :class:`~qurry.qurrium.container.experiments.ExperimentContainer`
    for :class:`~qurry.qurrium.qurrium.QurriumPrototype.`.
    and its corresponding :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`."""

    __name__ = "ExperimentContainerWrapper"
    __slots__ = ("_orphan_exps", "_multimanagers", "_all_exps_container")
    _orphan_exps: ExperimentContainer[_E]
    _multimanagers: dict[str, MultiManager[_E]]

    def __init__(
        self,
        orphan_exps: ExperimentContainer[_E],
        multimanagers: dict[str, MultiManager[_E]],
    ):
        """Initialize the wrapper with orphan experiments and their corresponding
        multimanagers.

        Args:
            orphan_exps: The orphan experiments container to be wrapped.
            multimanagers: The dictionary of multimanagers in QurriumPrototype.

        """
        self._orphan_exps = orphan_exps
        self._multimanagers = multimanagers
        self._all_exps_container = {}

    @property
    def all_exps_container(self) -> dict[str, ExperimentContainer[_E]]:
        """Get all experiment containers.

        Returns:
            dict[str, ExperimentContainer[_ExpInst]]: The dictionary of all experiment containers.

        """
        if list(self._all_exps_container.keys()) == (
            ["orphan_exps"] + list(self._multimanagers.keys())
        ):
            return self._all_exps_container

        all_exps_container = {"orphan_exps": self._orphan_exps}

        for current_multimanager_id, current_multimanager in self._multimanagers.items():
            all_exps_container[current_multimanager_id] = current_multimanager.exps

        self._all_exps_container = all_exps_container

        return all_exps_container

    def __getitem__(self, key: str) -> _E:
        """Get the experiments from the container by key.

        Args:
            key (str): The key of the experiment to be retrieved.

        Returns:
            ExperimentContainer[_ExpInst]: The experiment container with the given key.

        """
        for container in self.all_exps_container.values():
            if key in container:
                return container[key]

        raise KeyError(f"Experiment id: '{key}' not found in any container.")

    def where(self, key: str) -> str:
        """Get the experiment container where the experiment is located.

        Args:
            key (str): The key of the experiment to be retrieved.

        Returns:
            str: The container where the experiment is located.

        """
        for container_id, container in self.all_exps_container.items():
            if key in container:
                return container_id

        raise KeyError(f"Experiment id: '{key}' not found in any container.")

    def __setitem__(self, key: str, value: Any):
        """Set the experiment in the container by key.

        Args:
            key (str): The key of the experiment to be set.
            value (Any): The value to be set.

        Raises:
            ValueError: If the key is found in any container.
            ValueError: If the key is found in orphan_exps.
            KeyError: If the key is not found in any container.

        """
        which_container = None
        for container_id, container in self.all_exps_container.items():
            if key in container:
                which_container = container_id
                break

        if which_container == "orphan_exps":
            raise ValueError(
                f"You cannot set the experiment '{key}' in orphan_exps. "
                + "Please set it in the orphan_exps container."
            )
        if which_container is not None:
            raise ValueError(
                f"You cannot set the experiment '{key}' in experiment container wrapper. "
                + "But you can set it in the experiment container "
                + f"from multimanagers id: {which_container}."
            )
        raise KeyError(f"Experiment id: '{key}' not found in any container.")

    def items(self):
        """Get all experiments from all experiment containers.

        Returns:
            dict[str, _ExpInst]: A dictionary of all experiments in the container.

        """
        all_exps = {}
        for container in self.all_exps_container.values():
            all_exps.update(container.items())

        return all_exps

    def __repr__(self):
        """Return the string representation of the wrapper.

        Returns:
            str: The string representation of the wrapper.

        """
        num_exps = sum(len(container) for container in self.all_exps_container.values())

        return f"{self.__name__}(num_exps={num_exps}, num_container={len(self.all_exps_container)})"

    def _repr_oneline(self):
        num_exps = sum(len(container) for container in self.all_exps_container.values())

        return f"{self.__name__}(num_exps={num_exps}, num_container={len(self.all_exps_container)})"

    def _repr_pretty_(self, p, cycle):
        length = len(self.all_exps_container)
        if cycle:
            p.text(f"{self.__name__}(" + "{...}" + f", num={length})")
        else:
            with p.group(DEFAULT_INDENT, f"{self.__name__}(num={length}" + ", {", "})"):
                for i, (k, v) in enumerate(self.all_exps_container.items()):
                    p.breakable()
                    # pylint: disable=protected-access
                    p.text(f"'{k}': {v._repr_oneline()}")
                    # pylint: enable=protected-access
                    if i < length - 1:
                        p.text(",")
