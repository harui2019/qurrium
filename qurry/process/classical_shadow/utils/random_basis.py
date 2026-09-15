"""Post Processing - Classical Shadow - Utilities - Random Basis
(:mod:`qurry.process.classical_shadow.utils.random_basis`)

"""

import numpy as np

from ...exceptions import QurryPostProcessingError


def generate_random_basis(
    snapshots: int,
    unitary_located: list[int],
    random_unitary_seeds: dict[int, dict[int, int]] | None = None,
) -> dict[int, dict[int, int]]:
    """Generate the random basis for the classical shadow.

    Args:
        snapshots (int): The number of snapshots.
        unitary_located (list[int]): The list of selected qubits.
        random_unitary_seeds (dict[int, dict[int, int]] | None):
            The random unitary seeds.
            This argument only takes input as type of `dict[int, dict[int, int]]`.
            The first key is the index for the random unitary operator.
            The second key is the index for the qubit.

            .. code-block:: python

                {
                    0: {0: 1234, 1: 5678},
                    1: {0: 2345, 1: 6789},
                    2: {0: 3456, 1: 7890},
                }

            If you want to generate the seeds for all random unitary operator,
            you can use the function :func:`generate_random_unitary_seeds`
            in :mod:`qurry.process.randomized_measure.utils`.

            .. code-block:: python

                from qurry import generate_random_unitary_seeds

                random_unitary_seeds = generate_random_unitary_seeds(100, 2)

    Returns:
        dict[int, dict[int, int]]: The random basis.
    """
    if any(not isinstance(qi, int) for qi in unitary_located):
        raise ValueError("All qubits in unitary_located should be integers.")

    random_basis_placeholder = np.random.randint(
        0, 3, size=(snapshots, len(unitary_located))
    ).tolist()
    return {
        n_u_i: {
            n_u_qi: (
                random_basis_placeholder[n_u_i][seed_i]
                if random_unitary_seeds is None
                else int(np.random.default_rng(random_unitary_seeds[n_u_i][seed_i]).integers(0, 3))
            )
            for seed_i, n_u_qi in enumerate(unitary_located)
        }
        for n_u_i in range(snapshots)
    }


class RandomBasisGenerationError(QurryPostProcessingError):
    """Exception raised for errors in the random basis generation."""


MAX_QUBITS_FOR_BASIS_GENERATION = 16
"""The maximum number of qubits allowed for basis generation."""

MSG_GENERATE_BASIS_EXCEED_MAX_QUBITS = (
    "For safety reason, generating all possible basis is limited to "
    + "{} qubits ON PURPOSE. "
    + "If you really want to generate all possible basis for more qubits, "
    + "please consider the memory and time consumption, "
    + "then modify the 'max_qubits' argument accordingly. "
    + "This function 'generate_all_possible_basis' located in "
    + "'qurry.process.classical_shadow.utils.random_basis'."
)


def generate_all_possible_basis_array(
    num_qubits: int,
    *,
    max_qubits: int = MAX_QUBITS_FOR_BASIS_GENERATION,
    _basis: list[list[int]] | None = None,
) -> list[list[int]]:
    """Make a list of contains all possible basis.

    Args:
        num_qubits (int): The number of qubits.
        max_qubits (int):
            The maximum number of qubits allowed. Default is MAX_QUBITS_FOR_BASIS_GENERATION.
        _basis (list[list[int]] | None): The input basis. If None, use [[0], [1], [2]].

    Raise:
        RandomBasisGenerationError: If num_qubits exceeds max_qubits.

    Returns:
        list[str]: The list of bit strings.
    """

    if num_qubits == 0:
        raise ValueError("basis must not be empty.")
    if not isinstance(num_qubits, int):
        raise TypeError("num_qubits must be an integer.")
    if num_qubits < 1:
        raise ValueError("num_qubits must be greater than 0.")
    if num_qubits > max_qubits:
        raise RandomBasisGenerationError(MSG_GENERATE_BASIS_EXCEED_MAX_QUBITS.format(max_qubits))

    if num_qubits == 1:
        return [[0], [1], [2]]

    recursive_basis = generate_all_possible_basis_array(
        num_qubits - 1,
        max_qubits=max_qubits,
        _basis=([[0], [1], [2]] if _basis is None else _basis),
    )

    return [item + b for item in recursive_basis for b in [[0], [1], [2]]]


def make_evenly_basis_array(num_qubits: int, duplication: int = 1):
    """Make a list of contains evenly basis.

    Args:
        num_qubits (int): The number of qubits.
        duplication (int): The number of duplication for each basis.

    Raise:
        RandomBasisGenerationError: If num_qubits exceeds max_qubits.

    Returns:
        list[list[int]]: The list of bit strings.
    """

    try:
        return generate_all_possible_basis_array(num_qubits) * duplication
    except RandomBasisGenerationError as e:
        raise RandomBasisGenerationError(
            "Failed to generate evenly basis due to exceeding the maximum qubits. "
            + "See the original exception for more details."
        ) from e


def make_evenly_basis(
    num_qubits: int, duplication: int = 1, unitary_located: list[int] | None = None
) -> dict[int, dict[int, int]]:
    """Make a dictionary of contains evenly basis.

    Args:
        num_qubits (int): The number of qubits.
        duplication (int): The number of duplication for each basis.
        unitary_located (list[int] | None): The list of selected qubits. If None, use all qubits.

    """

    basis_array = make_evenly_basis_array(num_qubits, duplication)
    if unitary_located is None:
        unitary_located = list(range(num_qubits))

    return {
        n_u_i: {n_u_qi: basis_array[n_u_i][seed_i] for seed_i, n_u_qi in enumerate(unitary_located)}
        for n_u_i in range(len(basis_array))
    }


def validate_random_basis(
    index: int, basis: dict[int, int], unitary_located: list[int]
) -> str | None:
    """Validate the iteration of the random basis.

    Args:
        index (int): The index of the random basis item.
        basis (dict[int, int]): The random basis item.
        unitary_located (list[int]): The list of selected qubits.

    Returns:
        str | None: The validation result.
    """
    if not isinstance(index, int):
        return f"Index '{index}' is not an integer, but '{type(index)}'."
    if not isinstance(basis, dict):
        return f"'{basis}' is not a dictionary."
    if not set(unitary_located).issubset(basis.keys()):
        return f"'selected_qubits' {unitary_located} are not in the random basis."
    if not all((isinstance(qi, int) and (0 <= q_basis < 3)) for qi, q_basis in basis.items()):
        return "All values should be integers in the range [0, 3) in the dictionary."
    return None


def check_random_basis(random_basis: dict[int, dict[int, int]], unitary_located: list[int]) -> bool:
    """Check if the random basis is valid.

    Args:
        random_basis (dict[int, dict[int, int]]): The random basis.
        unitary_located (list[int]): The list of selected qubits.

    Returns:
        bool: True if the random basis is valid.

    Raise:
        ValueError: If the random basis is invalid.
    """
    if not isinstance(random_basis, dict):
        raise ValueError("random_basis should be a dictionary.")
    if any(not isinstance(qi, int) for qi in unitary_located):
        raise ValueError("All qubits in unitary_located should be integers.")

    invalid_found = [
        (k, validate_random_basis(k, v, unitary_located)) for k, v in random_basis.items()
    ]
    invalid_dict = {k: v for k, v in invalid_found if v is not None}
    if invalid_dict:
        raise ValueError(f"Invalid random_basis: {invalid_dict}")

    return True


def check_random_basis_array(
    random_basis_array: list[list[int]], snapshot: int, system_size: int
) -> bool:
    """Check if the random basis array is valid.

    Args:
        random_basis_array (list[list[int]]): The random basis array.
        snapshot (int): The number of snapshots.
        system_size (int): The size of the system.

    Returns:
        bool: True if the random basis array is valid.

    Raise:
        ValueError: If the random basis array is invalid.
    """
    random_basis_array_np = np.array(random_basis_array)
    if random_basis_array_np.shape != (snapshot, system_size):
        raise ValueError(
            "The shape of random_basis_array should be "
            + f"({snapshot}, {system_size}), but {random_basis_array_np.shape}."
        )

    random_basis_array_np_check = (0 <= random_basis_array_np) & (random_basis_array_np < 3)

    is_validate = random_basis_array_np_check.all()
    if not is_validate:
        raise ValueError("All values should be integers in the range [0, 3) in the array.")

    return True
