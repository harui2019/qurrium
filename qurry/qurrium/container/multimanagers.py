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
        original_repr = repr({k: v._repr_oneline() for k, v in self.items()})
        return f"{self.__name__}({original_repr}, num={len(self)})"

    def _repr_oneline(self):
        return f"{self.__name__}(" + "{...}" + f", num={len(self)})"

    def _repr_pretty_(self, p, cycle):
        # pylint: disable=protected-access
        original = repr({k: v._repr_oneline() for k, v in self.items()})
        # pylint: enable=protected-access
        length = len(self)

        if cycle:
            p.text(f"{self.__name__}(" + "{...}" + f", num={length})")
        else:
            with p.group(2, f"{self.__name__}(num={length}" + ", {", "})"):
                for i, (item_id, item) in enumerate(original):
                    p.breakable()
                    p.text(f"{item_id}: ")
                    p.breakable()
                    p.pretty(f"  {item}")
                    if i < length - 1:
                        p.text(",")

    def __str__(self):
        return super().__repr__()
