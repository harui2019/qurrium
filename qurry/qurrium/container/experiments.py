"""
================================================================
ExperimentContainer 
(:mod:`qurry.qurry.qurrium.container.experiments`)
================================================================

"""
from typing import Union, Optional, Hashable, TypeVar

ExperimentInstance = TypeVar("ExperimentInstance")


class ExperimentContainer(dict[Hashable, ExperimentInstance]):
    """A customized dictionary for storing `ExperimentPrototype` objects."""

    __name__ = "ExperimentContainer"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def call(
        self,
        exp_id: Optional[Hashable] = None,
    ) -> ExperimentInstance:
        """Call an experiment by its id.

        Args:
            exp_id: The id of the experiment to be called.

        Returns:
            ExperimentPrototype: The experiment with the given id.
        """

        if exp_id in self:
            return self[exp_id]
        raise KeyError(f'Experiment id: "{exp_id}" not found in {self}')

    def __call__(
        self,
        exp_id: Union[Hashable, None] = None,
    ) -> ExperimentInstance:
        return self.call(exp_id=exp_id)

    def __repr__(self):
        inner_lines = "\n".join(f"    {k}: ..." for k in self.keys())
        inner_lines2 = "{\n%s\n}" % inner_lines
        return (
            f"<{self.__name__}={inner_lines2} with {len(self)} "
            + "experiments load, a customized dictionary>"
        )
