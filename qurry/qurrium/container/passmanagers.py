"""
================================================================
Pass Manager Container 
(:mod:`qurry.qurrium.container.passmanagers`)
================================================================

"""

from qiskit.transpiler.passmanager import PassManager


class PassManagerContainer(dict[str, PassManager]):
    """A customized dictionary for storing `PassManager` objects."""

    __name__ = "PassManagerContainer"

    def __repr__(self):
        original_repr = repr({k: v for k, v in self.items()})
        return f"{self.__name__}({original_repr}, num={len(self)})"

    def _repr_oneline(self):
        return f"{self.__name__}(" + "{...}" + f", num={len(self)})"

    def _repr_pretty_(self, p, cycle):
        # pylint: disable=protected-access
        original_repr = repr({k: v for k, v in self.items()})
        # pylint: enable=protected-access
        original_repr_split = original_repr[1:-1].split(", ")
        length = len(original_repr_split)

        if cycle:
            p.text(f"{self.__name__}(" + "{...}" + f", num={length})")
        else:
            with p.group(2, f"{self.__name__}(num={length}" + ", {", "})"):
                for i, item in enumerate(original_repr_split):
                    p.breakable()
                    p.text(item)
                    if i < length - 1:
                        p.text(",")

    def __str__(self):
        return super().__repr__()
