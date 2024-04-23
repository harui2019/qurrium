"""
================================================================
Exceptions (:mod:`qurry.exceptions`)
================================================================

"""


class QurryError(Exception):
    """Base class for errors raised by Qurry."""

    def __init__(self, *message):
        """Set the error message."""
        super().__init__(" ".join(message))
        self.message = " ".join(message)

    def __str__(self):
        """Return the message."""
        return repr(self.message)


class QurryInvalidInherition(QurryError):
    """Invalid inherition class making by Qurry."""


class QurryExperimentCountsNotCompleted(QurryError):
    """Experiment is not completed."""


class QurryExtraPackageRequired(QurryError, ImportError):
    """Extra package required for Qurry."""


class QurryInvalidArgument(QurryError):
    """Invalid argument for Qurry."""


class QurryPositionalArgumentNotSupported(QurryError, ValueError):
    """Positional argument is not supported."""


class QurryCountLost(QurryError):
    """Count lost error."""


# General Warning
class QurryWarning(Warning):
    """Base class for warning raised by Qurry."""

    def __init__(self, *message):
        """Set the error message."""
        super().__init__(" ".join(message))
        self.message = " ".join(message)

    def __str__(self):
        """Return the message."""
        return repr(self.message)


class UnconfiguredWarning(QurryWarning):
    "For dummy function in qurrium has been activated."


class QurryInheritionNoEffect(QurryWarning):
    "This configuration method has no effect."


class QurryUnrecongnizedArguments(QurryWarning):
    "This argument is not recognized but may be kept at somewhere."


class QurryMemoryOverAllocationWarning(QurryWarning):
    "Automatically shutdown experiment to protect RAM for preventing crashing."


class QurryImportWarning(QurryWarning):
    "Warning for qurry trying to import something."


class QurryResetSecurityActivated(QurryWarning):
    "Warning for reset class security."


class QurryResetAccomplished(QurryWarning):
    "Warning for class reset."


class QurryProtectContent(QurryWarning):
    "Warning for protect content."


class QurrySummonerInfoIncompletion(QurryWarning):
    """Warning for summoner info incompletion.
    The summoner is the instance of :cls:`QurryMultiManager`."""


class QurryDummyRunnerWarning(QurryWarning):
    """Dummy runner warning."""


class QurryHashIDInvalid(QurryWarning):
    """Hash ID invalid warning."""


class QurryArgumentsExpectedNotNone(QurryWarning):
    """Arguments expected not None warning."""
