"""Post Processing - Classical Shadow - Utilities - Method Enum
(:mod:`qurry.process.classical_shadow.utils.method_enum`)

The abstract base class for method enums with utility functions.
"""

from typing import TypeVar
from abc import abstractmethod, ABCMeta
from enum import EnumMeta, Enum

T = TypeVar("T", bound="BaseMethodEnum")


class EnumABCMeta(EnumMeta, ABCMeta):
    """A metaclass that combines EnumMeta and ABCMeta."""


class BaseMethodEnum(Enum, metaclass=EnumABCMeta):
    """Base class for method enums with utility functions."""

    @classmethod
    def get_all_methods(cls: type[T]) -> list[str]:
        """Get a list of all available methods.

        Returns:
            list[str]: A list of method names.
        """
        return [method.value for method in cls]

    @classmethod
    def unknown_method_error_msg(cls: type[T], method_str: str | None = None) -> str:
        """Generate a ValueError for an unknown method.

        Args:
            method_str (str | None): The unknown method string. Default is None.

        Returns:
            str: The error message.
        """
        return (
            "Unknown method"
            + (f": '{method_str}'" if method_str is not None else "")
            + f". Supported methods are: {', '.join(cls.get_all_methods())}"
        )

    @classmethod
    def value_error(cls, method_str: str | None = None) -> ValueError:
        """Generate a ValueError for an unknown method.

        Args:
            method_str (str | None): The unknown method string. Default is None.

        Returns:
            ValueError: The ValueError with the error message.
        """
        return ValueError(cls.unknown_method_error_msg(method_str))

    @classmethod
    def from_string(cls: type[T], method_str: str) -> T:
        """Convert a string to a enum member.

        Args:
            method_str (str): The string representation of the method.

        Returns:
            The corresponding enum member.

        Raises:
            ValueError: If the string does not correspond to any enum member.
        """

        for method in cls:
            if method.value == method_str:
                return method
        raise cls.value_error(method_str)

    @classmethod
    @abstractmethod
    def get_default(cls: type[T]) -> T:
        """Get the default method.

        Returns:
            The default method.
        """
        raise NotImplementedError(f"{cls.__name__} must implement get_default()")
