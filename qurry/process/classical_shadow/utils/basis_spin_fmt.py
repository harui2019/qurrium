"""Post Processing - Classical Shadow - Utilities - Basis/Spin Format
(:mod:`qurry.process.classical_shadow.utils.basis_spin_fmt`)

This module provides utility functions to convert the format of basis and spin outcomes
which use in `Predicting Properties of Quantum Many-Body Systems
<https://github.com/hsinyuan-huang/predicting-quantum-properties>`_ ,
between different representations used in counts and random basis.

And export the format to a text file that can be read by
`Predicting Properties of Quantum Many-Body Systems
<https://github.com/hsinyuan-huang/predicting-quantum-properties>`_ .

"""

from typing import Literal
from collections.abc import Sequence
from pathlib import Path


def convert_to_basis_spin(
    shots: int,
    counts: list[dict[str, int]],
    random_basis_array: list[list[Literal[0, 1, 2] | int]],
) -> tuple[list[list[int]], list[list[int]]]:
    """Convert counts to single shots basis-spin format.

    Args:
        shots (int):
            The number of shots.
        counts (list[dict[str, int]]):
            The list of the counts.
        random_basis_array (list[list[Literal[0, 1, 2] | int]]):
            The random basis for classical shadow.

    Returns:
        A tuple containing a list of pauli basis and a list of spin outcomes.
    """
    pauli_basis, spin_outcome = [], []
    for idx, (single_counts, single_random_basis) in enumerate(zip(counts, random_basis_array)):
        partial_pauli_basis = [single_random_basis for _ in range(shots)]
        partial_spin_outcome = []

        for bitstring, count in single_counts.items():
            spin_values = [1 if bits == "1" else -1 for bits in reversed(bitstring)]
            partial_spin_outcome.extend(spin_values for _ in range(count))

        if len(partial_spin_outcome) != shots:
            raise ValueError(
                "The single counts should only contain one bitstring with count equal to shots. "
                + f"Counts: {single_counts}. Index: {idx}."
            )
        if len(partial_pauli_basis) != len(partial_spin_outcome):
            raise ValueError(
                "The length of the partial_pauli_basis should be equal to "
                + "the length of the partial_spin_outcome. "
                + f"Index: {idx}."
            )
        pauli_basis.extend(partial_pauli_basis)
        spin_outcome.extend(partial_spin_outcome)

    return pauli_basis, spin_outcome


def measurements_export(
    pauli_basis: Sequence[Sequence[int]],
    spin_outcome: Sequence[Sequence[int]],
    system_size: int,
    filename: str | Path,
) -> str | Path:
    """Export the measurement data of Single shots basis-spin Output format (for PQP).

    Args:
        pauli_basis (Sequence[Sequence[int]]):
            The list of Pauli basis measurements. (X: 0, Y: 1, Z: 2)
        spin_outcome (Sequence[Sequence[int]]):
            The list of spin outcomes. (1, -1)
        system_size (int):
            The size of the quantum system, which is the number of qubits.
        filename (str | Path):
            The path to the output file.

    Returns:
        The path to the output file.
    """

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"{system_size}\n")
        for single_pauli, single_spin in zip(pauli_basis, spin_outcome):
            f.writelines(
                " ".join(
                    (f"{chr(88 + pauli)} {spin}" for pauli, spin in zip(single_pauli, single_spin))
                )
                + "\n"
            )

    return filename


VALID_RANDOM_BASIS = {"X", "Y", "Z"}
"""Valid random basis for measurements."""
VALID_BITS = {"-1", "1"}
"""Valid bits for measurement outcomes."""


def validate_pqp_result_per_row(
    row: Sequence[str], len_row: int, index: int
) -> tuple[list[int], list[int]]:
    """Validate a single row of the PQP result data,
    then return pauli basis and spin outcome in the list of integer.

    Args:
        row (Sequence[str]): The row to validate.
        len_row (int): The length of row, which is the number of qubits multiplied by 2.
        row_index (int): The row index (0-based) for error reporting.

    Raises:
        ValueError: If the row is invalid.

    Returns:
        tuple[list[int], list[int]]: The validated Pauli basis and spin outcome.
    """
    if len(row) != len_row:
        raise ValueError(
            f"Invalid line length at line index {index}. "
            f"Expected: {len_row}, Got: {len(row)}. row: '{row}'"
        )

    pauli_values = row[0::2]
    invalid_pauli = set(pauli_values) - VALID_RANDOM_BASIS
    if invalid_pauli:
        raise ValueError(f"Invalid Pauli operator at row index {index}: {invalid_pauli}")

    outcome_values = row[1::2]
    invalid_outcomes = set(outcome_values) - VALID_BITS
    if invalid_outcomes:
        raise ValueError(f"Invalid measurement outcome at row index {index}: {invalid_outcomes}")

    return (
        [ord(pauli[0]) - ord("X") for pauli in pauli_values],  # (X=0, Y=1, Z=2)
        [int(outcome) for outcome in outcome_values],
    )


def measurements_read(filename: str | Path) -> tuple[list[list[int]], list[list[int]], int]:
    """Read the measurement data file of Single shots basis-spin Output format (for PQP).

    Args:
        filename (str | Path): The path to the input file.

    Returns:
        A tuple containing a list of pauli basis, a list of spin outcomes, and the system size.
    """
    pauli_basis = []
    spin_outcome = []

    with open(filename, "r", encoding="utf-8") as f:
        first_line = f.readline().strip()  # This will iterate first line.
        if not first_line:
            raise ValueError("The input file is empty.")

        system_size = int(first_line)
        expect_length = system_size * 2

        for row_num, line in enumerate(f):  # So here begins from second line.
            single_pauli, single_spin = validate_pqp_result_per_row(
                line.strip().split(), expect_length, row_num
            )
            pauli_basis.append(single_pauli)
            spin_outcome.append(single_spin)

    return pauli_basis, spin_outcome, system_size
