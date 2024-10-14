"""
================================================================
ExperimentContainer 
(:mod:`qurry.qurry.qurrium.container.experiments`)
================================================================

"""

from typing import TypeVar

from ..experiment import ExperimentPrototype

_ExpInst = TypeVar("_ExpInst", bound=ExperimentPrototype)


class ExperimentContainer(dict[str, _ExpInst]):
    """A customized dictionary for storing `ExperimentPrototype` objects."""

    __name__ = "ExperimentContainer"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def call(
        self,
        exp_id: str,
    ) -> _ExpInst:
        """Call an experiment by its id.

        Args:
            exp_id: The id of the experiment to be called.

        Returns:
            ExperimentPrototype: The experiment with the given id.
        """

        if exp_id in self:
            return self[exp_id]
        raise KeyError(f"Experiment id: '{exp_id}' not found.")

    def __call__(
        self,
        exp_id: str,
    ) -> _ExpInst:
        return self.call(exp_id=exp_id)

    def __repr__(self):
        original_repr = repr({k: v._repr_no_id() for k, v in self.items()})
        return f"{self.__name__}({original_repr}, num={len(self)})"

    def _repr_oneline(self):
        return f"{self.__name__}(" + "{...}" + f", num={len(self)})"

    def _repr_pretty_(self, p, cycle):
        length = len(self)
        if cycle:
            p.text(f"{self.__name__}(" + "{...}" + f", num={length})")
        else:
            with p.group(2, f"{self.__name__}(num={length}" + ", {", "})"):
                for i, (k, v) in enumerate(self.items()):
                    p.breakable()
                    # pylint: disable=protected-access
                    p.text(f"'{k}': {v._repr_no_id()}")
                    # pylint: enable=protected-access
                    if i < length - 1:
                        p.text(",")

    def __str__(self):
        return super().__repr__()
