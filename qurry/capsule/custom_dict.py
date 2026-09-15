"""The template of customed dict (:mod:`qurry.capsule.custom_dict`)"""

from typing import TypeVar

try:
    # only for type hint
    from IPython.lib.pretty import RepresentationPrinter
except ImportError:
    ...

from .utils import DEFAULT_INDENT

_K = TypeVar("_K")
_V = TypeVar("_V")


class CustomDict(dict[_K, _V]):
    """A customized dictionary template with predefined pretty printing methods.

    This is a template for customized dictionary. You can inherit this class
    to create your own customized dictionary.

    Example:
        .. code-block:: python

            class MyCustomDict(CustomDict[str, int]):
                pass

            my_dict = MyCustomDict({"a": 1, "b": 2})
            print(my_dict["a"])  # Output: 1
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"{self.__class__.__name__}({super().__repr__()})"

    def _repr_pretty_(self, p: "RepresentationPrinter", cycle: bool):
        if cycle:
            p.text(f"{self.__class__.__name__}" + "({...})")
            return

        if not self:
            p.text(f"{self.__class__.__name__}" + "({})")
            return

        with p.group(DEFAULT_INDENT, f"{self.__class__.__name__}(" + "{", "})"):
            for i, (k, v) in enumerate(self.items()):
                p.breakable()
                p.pretty(k)
                p.text(": ")
                p.pretty(v)
                if i < len(self) - 1:
                    p.text(",")

    def __str__(self):
        return super().__repr__()
