"""

================================================================
CapSule Exceptions (:mod:`qurry.capsule.exception`)
================================================================
"""


class CapSuleError(Exception):
    """Base class for errors raised by :module:`capsule`."""

    def __init__(self, *message):
        """Set the error message."""
        super().__init__(" ".join(message))
        self.message = " ".join(message)

    def __str__(self):
        """Return the message."""
        return repr(self.message)


class CapSuleValuedError(CapSuleError, ValueError):
    """ValueErrors raised by :module:`capsule."""


# General Warning
class CapSuleWarning(Warning):
    """Base class for warning raised by :module:`capsule."""

    def __init__(self, *message):
        """Set the error message."""
        super().__init__(" ".join(message))
        self.message = " ".join(message)

    def __str__(self):
        """Return the message."""
        return repr(self.message)


class TagListTakeNotIterableWarning(CapSuleWarning):
    """Warning raised when the input of `TagList.take` is not iterable."""
