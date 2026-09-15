"""Exception Decorator (:mod:`qurry.tools.except_decorator`)"""

from typing import TypeVar
from collections.abc import Callable
import functools
import warnings
import inspect

from .exceptions import QurryUnprovenFeatureWarning

U = TypeVar("U", bound=Callable)


def unproven_feature(message: str | None = None):
    """The decorator to mark a function or class as an unproven feature.

    .. code-block:: python

        @unproven_feature
        def my_experimental_function():
            pass

        @unproven_feature(message="This is a custom message.")
        class MyExperimentalClass:
            pass

    Args:
        message (str | None, optional):
            The warning message to be displayed.
            If not provided, a default message will be used.
            The default message is:

            .. code-block:: python

                f"This feature '{name}' is unproven, we can not guarantee the correctness."

    Returns:
        The decorated function or class, which will issue a warning when called or instantiated.
    """

    def decorator(func_or_cls: U) -> U:
        """The actual decorator function.
        Args:
            func_or_cls (Callable):
                The function or class to be marked.

        Returns:
            The decorated function or class,
            which will issue a warning when called or instantiated.
        """

        name = func_or_cls.__qualname__

        warn_message = (
            message or f"This feature '{name}' is unproven, we can not guarantee the correctness."
        )

        if inspect.isclass(func_or_cls):
            original_init = func_or_cls.__init__

            @functools.wraps(original_init)
            def wrapped_init(self, *args, **kwargs):
                warnings.warn(warn_message, QurryUnprovenFeatureWarning, stacklevel=2)
                return original_init(self, *args, **kwargs)

            func_or_cls.__init__ = wrapped_init

            func_or_cls.__unproven_feature__ = True

            return func_or_cls  # type: ignore[return-value]

        if inspect.isfunction(func_or_cls):
            warnings.warn(warn_message, QurryUnprovenFeatureWarning, stacklevel=2)
            return func_or_cls  # type: ignore[return-value]

        raise TypeError(
            "The decorator can only be applied to functions or classes."
            + f" Got {type(func_or_cls)}."
        )

    return decorator
