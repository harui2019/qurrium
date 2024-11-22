"""
================================================================
Representation modification for Hoshi CapSule
(:mod:`qurry.capsule.hoshi.repr_modify`)
================================================================

I write this class just for having better representation for the functions
:func:`internet_is_fxxking_awesome`. :3

"""

from typing import Any, Callable, Union, Optional


class EasyReprModify:
    """Easy representation modification for Hoshi CapSule."""

    def __init__(
        self,
        fn: Callable[..., Any],
        repr_content: Optional[Union[str, Callable[..., str]]] = None,
    ):
        self._fn = fn
        if isinstance(repr_content, str):
            self._repr = lambda: repr_content
        elif isinstance(repr_content, Callable):
            self._repr = repr_content
        else:
            self._repr = self._fn.__repr__

    @property
    def __doc__(self) -> Optional[str]:
        return self._fn.__doc__

    @__doc__.setter
    def __doc__(self, val: Optional[str]) -> None:
        self._fn.__doc__ = val

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._fn(*args, **kwargs)

    def __repr__(self):
        return self._repr()


def easy_repr_modify_wrapper(
    repr_content: Optional[Union[str, Callable[..., str]]]
) -> Callable[..., Any]:
    """Wrapper for easy representation modification.

    Args:
        repr_content (Optional[Union[str, Callable[..., str]]]):
            The content of the representation.
            If it is a string, it will be the representation.
            If it is a function, it will be the representation function.

    Returns:
        Callable[..., Any]: The wrapper function for the representation modification.
    """

    def wrapper_fn(
        fn: Callable[..., Any],
    ) -> Callable[..., Any]:
        """The wrapper function for the representation modification.

        Args:
            fn (Callable[..., Any]): The function to be modified.

        Returns:
            Callable[..., Any]: The modified function.
        """
        return EasyReprModify(fn, repr_content)

    return wrapper_fn
