"""
================================================================
Multimanagers Container
(:mod:`qurry.qurrium.container.multimanagers`)
================================================================

"""

from ..multimanager import MultiManager


class MultiManagerContainer(dict[str, MultiManager]):
    """A customized dictionary for storing `MultiManager` objects."""

    __name__ = "MultiManagerContainer"

    def __repr__(self):
        original_repr = repr({k: v._repr_oneline_no_id() for k, v in self.items()})
        return f"{self.__name__}(num={len(self)}, {original_repr})"

    def _repr_oneline(self):
        return f"{self.__name__}(num={len(self)}, " + "{...}" + ")"

    def _repr_pretty_(self, p, cycle):
        # pylint: disable=protected-access
        original = {k: v._repr_oneline_no_id() for k, v in self.items()}
        # pylint: enable=protected-access

        if cycle:
            p.text(f"{self.__name__}(num={len(self)}, " + "{...}" + ")")
        else:
            with p.group(0, f"{self.__name__}(num={len(self)}" + ", {", "})"):
                for i, (item_id, item) in enumerate(original.items()):
                    p.breakable()
                    p.text(f'  "{item_id}":')
                    p.breakable()
                    p.text(f"    {item},")
                    if i == len(original) - 1:
                        p.breakable()

    def __str__(self):
        return super().__repr__()
