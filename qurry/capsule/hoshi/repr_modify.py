"""Representation modification for Hoshi CapSule (:mod:`qurry.capsule.hoshi.repr_modify`)

I write this module just for having better representation for the functions
:func:`~qurry.capsule.internet_is_fxxking_awesome`. :3

"""

from typing import Any
from collections.abc import Callable
from functools import wraps


class EasyReprModify:
    """Easy representation modification."""

    def __init__(
        self, fn: Callable[..., Any], repr_content: Callable[..., str] | str | None = None
    ):
        """Initialize the :class:`EasyReprModify`.

        Args:
            fn (Callable[..., Any]): The function to be modified.
            repr_content (Callable[..., str] | str | None, optional):
                The content of the representation.
                If it is a string, it will be the representation.
                If it is a function, it will be the representation function.
                Defaults to None, which means it will use the function's `__repr__`.
        """

        wraps(fn)(self)
        self._fn = fn

        if isinstance(repr_content, str):
            self._repr = lambda: repr_content
        elif isinstance(repr_content, Callable):
            self._repr = repr_content
        else:
            self._repr = self._fn.__repr__

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._fn(*args, **kwargs)

    def __repr__(self):
        return self._repr()


def easy_repr_modify_wrapper(repr_content: Callable[..., str] | str | None) -> Callable[..., Any]:
    """Wrapper for easy representation modification.

    Args:
        repr_content (Callable[..., str] | str | None):
            The content of the representation.
            If it is a string, it will be the representation.
            If it is a function, it will be the representation function.

    Returns:
        Callable[..., Any]: The wrapper function for the representation modification.
    """

    def wrapper_fn(fn: Callable[..., Any]) -> Callable[..., Any]:
        """The wrapper function for the representation modification.

        Args:
            fn (Callable[..., Any]): The function to be modified.

        Returns:
            Callable[..., Any]: The modified function.
        """
        return EasyReprModify(fn, repr_content)

    return wrapper_fn
