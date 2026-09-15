"""EchoListenRandomized - Excpetions (:module:`qurry.qurries.echo_randomized.exceptions`)"""

from ..entropy_randomized.exceptions import RandomizedMeasureError
from ...exceptions import QurryWarning


class OverlapArgumentsUnfulfilled(RandomizedMeasureError, ValueError):
    """The arguments for overlap measure are unfulfilled."""


MSG_OVERLAPPING_GIVEN = (
    "When the number of qubits in two circuits is not the same, "
    + "the {} of two circuits should be specified."
)


class OverlapComparisonSizeDifferent(RandomizedMeasureError, ValueError):
    """The sizes between two system that need to be compared are different."""


NSG_OVERLAPPING_SIZE = (
    "The qubits number of {} in two circuits should be the same, "
    + "but got different number of qubits measured."
    + "Got circuit 1: {} {} and circuit 2: {} {}."
)
"""Message for checking the size of qubits measured and unitary located mapping.
This message is used in the function :func:`overlapping_size_check` to raise an exception
if the size of the qubits measured or unitary located mapping in the two circuits are different"""


class SeperatedExecutingOverlapResult(QurryWarning):
    """When the seperated executing overlap the result with the same backend"""
