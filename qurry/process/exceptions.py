"""
================================================================
Qurry Process Exceptions 
(:mod:`qurry.process.exceptions`)
================================================================

"""


class QurryPostProcessingError(Exception):
    """Base class for errors raised by Qurry."""

    def __init__(self, *message):
        """Set the error message."""
        super().__init__(" ".join(message))
        self.message = " ".join(message)

    def __str__(self):
        """Return the message."""
        return repr(self.message)


class PostProcessingCythonImportError(QurryPostProcessingError, ImportError):
    """Cython import error."""


class PostProcessingRustImportError(QurryPostProcessingError, ImportError):
    """Rust import error."""


# General Warning
class QurryPostProcessingWarning(Warning):
    """Base class for warning raised by Qurry."""

    def __init__(self, *message):
        """Set the error message."""
        super().__init__(" ".join(message))
        self.message = " ".join(message)

    def __str__(self):
        """Return the message."""
        return repr(self.message)


class PostProcessingCythonUnavailableWarning(QurryPostProcessingWarning):
    """Cython unavailable warning."""


class PostProcessingRustUnavailableWarning(QurryPostProcessingWarning):
    """Rust unavailable warning."""


class PostProcessingBackendDeprecatedWarning(QurryPostProcessingWarning):
    """Post-processing backend is deprecated."""
