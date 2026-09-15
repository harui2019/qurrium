"""Multimanagers Container (:mod:`qurry.qurrium.qurrium.mm_container`)"""

from ..multimanager import MultiManager, _E
from ...capsule import CustomDict, DEFAULT_INDENT


class MultiManagerContainer(CustomDict[str, MultiManager[_E]]):
    """A customized dictionary for storing
    :class:`~qurry.qurrium.multimanager.multimanager.MultiManager` objects."""

    def __repr__(self):
        original_repr = repr({k: v._repr_oneline_no_id() for k, v in self.items()})
        return f"{self.__class__.__name__}(num={len(self)}, {original_repr})"

    def _repr_oneline(self):
        return f"{self.__class__.__name__}(num={len(self)}, " + (r"{...}" if self else r"{}") + ")"

    def _repr_pretty_(self, p, cycle):
        if cycle:
            p.text(self._repr_oneline())
            return

        if not self:
            p.text(f"{self.__class__.__name__}" + "(num=0, {})")
            return

        with p.group(DEFAULT_INDENT, f"{self.__class__.__name__}(num={len(self)}" + ", {", "})"):
            for i, (k, v) in enumerate(self.items()):
                p.breakable()
                p.text(f'"{k}":')
                p.breakable()
                # pylint: disable=protected-access
                p.text(" " * DEFAULT_INDENT + v._repr_oneline_no_id())
                if i < len(self) - 1:
                    p.text(",")
                # pylint: enable=protected-access

    def __str__(self):
        return super().__repr__()
