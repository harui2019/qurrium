"""EntropyMeasureRandomized - Exceptions (:mod:`qurry.qurries.entropy_randomized.exceptions`)"""

from ...exceptions import QurryError


class RandomizedMeasureError(QurryError):
    """The error for randomized measure."""


class UnitaryOperatorNotFullCovering(RandomizedMeasureError, ValueError):
    """Randomized measure unitary operator warning
    for not full covering the measure range."""


MSG_FULL_COVER = (
    "Some qubits {} are measured "
    + "but not random unitary located in {} circuit. {}: {}, {}: {} "
    + "If you are sure about this, "
    + "you can set `unitary_loc_not_cover_measure=True` "
    + "to close this warning."
)
"""Message for checking whether the unitary operator covers the measurement.
This message is used in the function :func:`unitary_full_cover_check` to raise an exception
if the unitary operator does not cover the measurement 
and `unitary_loc_not_cover_measure` is False."""
