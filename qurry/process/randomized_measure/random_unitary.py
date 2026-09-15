"""Random Unitary Toolkit for Randomized Measurement
(:mod:`qurry.process.randomized_measure.random_unitary`)

We also make a short import path for :func:`~qiskit.quantum_info.random_unitary`
as :func:`~qurry.process.utils.randomized.random_unitary`,
due to Qiskit usually relocate its module.

"""

import numpy as np

from qiskit.quantum_info import random_unitary, Operator

from ..utils import density_matrix_to_bloch_vector


def generate_random_unitary(
    times: int,
    unitary_located: list[int],
    random_unitary_seeds: dict[int, dict[int, int]] | None,
) -> dict[int, dict[int, Operator]]:
    """Generate a dictionary of local random unitary operators.

    Args:
        times (int): The number of random unitary operators to generate.
        unitary_located (list[int]): The location of unitary operator.
        random_unitary_seeds (dict[int, dict[int, int]] | None):
            The seeds for random unitary operator generation.

    Returns:
        dict[int, list[list[complex]]]:
            The dictionary of unitary operators in :class:`list[list[complex]]`.
    """

    if random_unitary_seeds is None:
        return {
            n_u_i: {n_u_qi: random_unitary(2) for n_u_qi in unitary_located}
            for n_u_i in range(times)
        }

    return {
        n_u_i: {
            n_u_qi: random_unitary(2, random_unitary_seeds[n_u_i][seed_i])
            for seed_i, n_u_qi in enumerate(unitary_located)
        }
        for n_u_i in range(times)
    }


def local_unitary_op_to_list(
    single_unitary_op_dict: dict[int, Operator],
) -> dict[int, list[list[complex]]]:
    """Transform a dictionary of local unitary operators
    in :class:`~qiskit.quantum_info.operator.Operator`
    with the qubit index as key to a dictionary of unitary operators
    in :class:`list[list[complex]]`.

    Args:
        single_unitary_op_dict (dict[int, Operator]): The dictionary of unitary operators.

    Returns:
        dict[int, list[list[complex]]]:
            The dictionary of unitary operators in :class:`list[list[complex]]`.
    """
    return {i: np.array(op).tolist() for i, op in single_unitary_op_dict.items()}


def local_unitary_op_to_bloch_vector(
    single_unitary_op_list_dict: dict[int, list[list[complex]]],
) -> dict[int, tuple[float, float, float]]:
    """Transform a dictionary of local unitary operators in :class:`list[list[complex]]`
    with the qubit index as key to a dictionary of pauli coefficients.

    Args:
        single_unitary_dict (dict[int, Operator]): The dictionary of unitary operators.

    Returns:
        The dictionary of pauli coefficients.
    """
    return {
        i: density_matrix_to_bloch_vector(np.array(op))
        for i, op in single_unitary_op_list_dict.items()
    }
