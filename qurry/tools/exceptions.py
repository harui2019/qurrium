"""Exceptions for Qurrium (:mod:`qurry.qurrium.exceptions`)"""

from ..exceptions import QurryError, QurryWarning


class RequiredDependenciesFailureError(QurryError, ImportError):
    """The dependencies of Qurrium like Qiskit raise some error."""


class ParallelManagerRuntimeError(QurryError, RuntimeError):
    """The error for ParallelManager during runtime."""


class OptionalDependenciesNotWorking(QurryWarning):
    """Some function from the dependencies of Qurry
    like Qiskit will not working for some reason."""


class WrongWorkerNumReplaced(QurryWarning):
    """The number of workers is replaced
    because the given number is not suitable."""


class QurryUnprovenFeatureWarning(QurryWarning):
    """Unproven feature warning.
    This feature is not proven to be working or not.
    Please report if you find any issue with this feature.
    """


class QurryDeprecatedWarning(QurryWarning, DeprecationWarning):
    """Deprecated warning."""
