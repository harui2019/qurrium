"""Boorust - Classical Shadow (:mod:`qurry.boorust.shadow`)"""

from collections.abc import Sequence

def nomatmul_trace_sum_rust(
    pauli_basis: Sequence[Sequence[int]],
    spin_outcome: Sequence[Sequence[int]],
    subsystem: Sequence[int],
) -> float:
    """Perform the trace calculation for the given data and subsystems using Python.

    Args:
        pauli_basis (Sequence[Sequence[int]]):
            The list of Pauli basis measurements. (X: 0, Y: 1, Z: 2)
        spin_outcome (Sequence[Sequence[int]]):
            The list of spin outcomes. (1, -1)
        subsystem (Sequence[int]):
            The subsystems.

    Returns:
        float: The result of the trace calculation.
    """
