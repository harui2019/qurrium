# General Error


class QurecipeError(Exception):
    """Base class for errors raised by Qurecipe."""

    def __init__(self, *message):
        """Set the error message."""
        super().__init__(" ".join(message))
        self.message = " ".join(message)

    def __str__(self):
        """Return the message."""
        return repr(self.message)


# General Warning
class QurecipeWarning(Warning):
    """Base class for warning raised by Qurecipe."""

    def __init__(self, *message):
        """Set the error message."""
        super().__init__(" ".join(message))
        self.message = " ".join(message)

    def __str__(self):
        """Return the message."""
        return repr(self.message)


class QurecipeCaseNotFoundError(QurecipeError):
    """Raised when the case is not found."""


class InitialStateQubitsNumberNotFitting(QurecipeWarning):
    """Raised when the initial state's qubit number is not fitting the number Qurecipe object get."""
