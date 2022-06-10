import warnings

# General Error


class QurryError(Exception):
    """Base class for errors raised by Qurry."""

    def __init__(
        self,
        *message
    ):
        """Set the error message."""
        super().__init__(" ".join(message))
        self.message = " ".join(message)

    def __str__(self):
        """Return the message."""
        return repr(self.message)

# General Warning


class QurryWarning(Warning):
    """Base class for warning raised by Qurry."""

    def __init__(
        self,
        *message
    ):
        """Set the error message."""
        super().__init__(" ".join(message))
        self.message = " ".join(message)

    def __str__(self):
        """Return the message."""
        return repr(self.message)


class UnconfiguredWarning(QurryWarning):
    "For dummy function in qurrium has been activated."
