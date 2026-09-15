"""Post Processing - Utils - Counts Process (:mod:`qurry.process.utils.counts_process`)"""

from collections.abc import Iterable

from ..availability import availability, default_postprocessing_backend, PostProcessingBackendLabel

# pylint: disable=import-error,no-name-in-module
from ...boorust.counts_process import (  # type: ignore
    single_counts_recount_rust,
    counts_list_recount_rust,
    shot_counts_selected_clreg_checker as shot_counts_selected_clreg_checker_rust,
    counts_list_vectorize_rust,
    rho_m_flatten_counts_list_vectorize_rust,
)


BACKEND_AVAILABLE = availability("utils.counts_process", [("Rust", True, None)])
DEFAULT_PROCESS_BACKEND = default_postprocessing_backend(True, False)


def check_invalid_counts(shots: int, counts: list[dict[str, int]]):
    """Check whether the counts are valid.

    Args:
        shots (int): The number of shots.
        counts (list[dict[str, int]]): The list of the counts.

    Raises:
        ValueError: If the counts are invalid, which some of them mismatch shots number.
    """
    invalid_counts = list(
        filter(lambda i_and_c: sum(i_and_c[1].values()) != shots, enumerate(counts))
    )
    if len(invalid_counts) > 0:
        raise ValueError(
            "The counts must be equal to the number of shots, "
            + f"but following counts are invalid, index: {invalid_counts}"
        )


def single_counts_recount_proto(
    single_counts: dict[str, int],
    num_classical_register: int,
    select_clregs_sort_rev: list[int],
) -> dict[str, int]:
    """Calculate the counts under the degree.

    Args:
        single_counts (dict[str, int]):
            Counts measured from the single quantum circuit.
        num_classical_register (int):
            The number of classical registers.
        select_clregs_sort_rev (list[int]):
            The reversed sorted list of **the index of the selected_classical_registers**.

    Returns:
        dict[str, int]: The counts under the degree.
    """

    single_counts_recounted = {}
    for bitstring_all, num_counts_all in single_counts.items():
        bitstring = "".join(
            bitstring_all[num_classical_register - q_i - 1] for q_i in select_clregs_sort_rev
        )
        if bitstring in single_counts_recounted:
            single_counts_recounted[bitstring] += num_counts_all
        else:
            single_counts_recounted[bitstring] = num_counts_all

    return single_counts_recounted


def single_counts_recount_pyrust(
    single_counts: dict[str, int],
    num_classical_register: int,
    selected_classical_registers: list[int],
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> dict[str, int]:
    """Calculate the counts under the degree.

    Args:
        single_counts (dict[str, int]):
            Counts measured from the single quantum circuit.
        num_classical_register (int):
            The number of classical registers.
        selected_classical_registers_sorted (list[int]):
            The list of **the index of the selected_classical_registers**.
        backend (PostProcessingBackendLabel, optional):
            Backend for the process. Defaults to "Rust".

    Returns:
        dict[str, int]: The counts under the degree.
    """

    if backend == "Rust":
        return single_counts_recount_rust(
            single_counts, num_classical_register, selected_classical_registers
        )

    select_clregs_sort_rev = sorted(selected_classical_registers, reverse=True)
    return single_counts_recount_proto(
        single_counts, num_classical_register, select_clregs_sort_rev
    )


def counts_list_recount_pyrust(
    counts_list: list[dict[str, int]],
    num_classical_register: int,
    selected_classical_registers: list[int],
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> list[dict[str, int]]:
    """Calculate the counts under the degree.

    Args:
        counts_list (list[dict[str, int]]):
            The list of counts measured from the single quantum circuit.
        num_classical_register (int):
            The number of classical registers.
        selected_classical_registers (list[int]):
            The list of **the index of the selected_classical_registers**.
        backend (PostProcessingBackendLabel, optional):
            Backend for the process. Defaults to "Rust".

    Returns:
        list[dict[str, int]]: The counts under the degree.
    """
    if backend == "Rust":
        return counts_list_recount_rust(
            counts_list, num_classical_register, selected_classical_registers
        )

    select_clregs_sort_rev = sorted(selected_classical_registers, reverse=True)
    return [
        single_counts_recount_proto(single_counts, num_classical_register, select_clregs_sort_rev)
        for single_counts in counts_list
    ]


def selected_clregs_to_optlist(
    selected_classical_registers: Iterable[int] | None = None,
) -> list[int] | None:
    """Convert selected classical registers to a list.
    This usually uses for Rust binding
    which can not handle :class:`~typing.Iterable` but only :class:`list`.

    Args:
        selected_classical_registers (Iterable[int] | None, optional):
            The selected classical registers.

    Returns:
        list[int] | None: The list of selected classical registers or None.
    """

    if isinstance(selected_classical_registers, Iterable):
        selected_classical_registers = list(selected_classical_registers)
    elif selected_classical_registers is not None:
        raise TypeError(
            "selected_classical_registers must be an Iterable or None"
            + f", but got {type(selected_classical_registers)}"
        )

    return selected_classical_registers


def shot_counts_selected_clreg_checker(
    shots: int,
    counts: list[dict[str, int]],
    selected_classical_registers: Iterable[int] | None = None,
) -> tuple[int, list[int]]:
    """Check whether the selected classical registers are valid.

    Args:
        shots (int):
            The number of shots.
        counts (list[dict[str, int]]):
            The list of the counts.
        selected_classical_registers (Iterable[int] | None, optional):
            The selected classical registers. Defaults to None.
        backend (PostProcessingBackendLabel, optional):
            Backend for the process. Defaults to "Rust".

    Returns:
        tuple[int, list[int]]:
            The size of the total system and the selected classical registers.
    """

    check_invalid_counts(shots, counts)

    total_system_size = len(next(iter(counts[0].keys())))

    if selected_classical_registers is None:
        selected_classical_registers = list(range(total_system_size))
    elif not isinstance(selected_classical_registers, Iterable):
        raise ValueError(
            "selected_classical_registers should be Iterable, "
            + f"but get {type(selected_classical_registers)}"
        )
    else:
        selected_classical_registers = list(selected_classical_registers)
    assert all(0 <= q_i < total_system_size for q_i in selected_classical_registers), (
        f"Invalid selected classical registers: {selected_classical_registers}"
    )

    return total_system_size, selected_classical_registers


def shot_counts_selected_clreg_checker_pyrust(
    shots: int,
    counts: list[dict[str, int]],
    selected_classical_registers: Iterable[int] | None = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> tuple[int, list[int]]:
    """Check whether the selected classical registers are valid.
    This function wraps the implementation of Python and Rust.

    Args:
        shots (int):
            The number of shots.
        counts (list[dict[str, int]]):
            The list of the counts.
        selected_classical_registers (Iterable[int] | None, optional):
            The selected classical registers. Defaults to None.
        backend (PostProcessingBackendLabel, optional):
            Backend for the process. Defaults to "Rust".

    Returns:
        tuple[int, list[int]]:
            The size of the total systemsize and the selected classical registers.
    """
    if backend == "Rust":
        selected_classical_registers = selected_clregs_to_optlist(selected_classical_registers)
        return shot_counts_selected_clreg_checker_rust(shots, counts, selected_classical_registers)

    return shot_counts_selected_clreg_checker(shots, counts, selected_classical_registers)


def counts_list_vectorize_pyrust(
    counts_list: list[dict[str, int]],
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> list[tuple[list[list[int]], list[int]]]:
    """Vectorized counts.

    Args:
        counts_list (list[dict[str, int]]):
            The list of counts measured from the single quantum circuit.

    Returns:
        list[tuple[list[list[int]], list[int]]]: The counts under the degree.
    """
    if backend == "Rust":
        return counts_list_vectorize_rust(counts_list)

    vectorized_counts = []
    for single_counts in counts_list:
        keys_int_array: list[list[int]] = [list(map(int, k)) for k in single_counts.keys()]
        values_int_array: list[int] = list(single_counts.values())

        vectorized_counts.append((keys_int_array, values_int_array))
    return vectorized_counts


def process_vectorize_single_counts(
    single_counts: dict[str, int],
    um_data: list[int],
    selected_cregs_sorted: list[int],
    num_qubits: int,
) -> tuple[list[list[int]], list[int]]:
    """Process single counts to vectorized format.

    Args:
        single_counts (dict[str, int]):
            Counts measured from the single quantum circuit.
        um_data (list[int]):
            The shadow direction of the unitary operators.
        selected_cregs_sorted (list[int]):
            The sorted list of **the index of the selected_classical_registers**.
        num_qubits (int):
            The number of qubits.

    Returns:
        tuple[list[list[int]], list[int]]: The vectorized counts.
    """

    len_nomatch_bitstrings = [
        bitstring for bitstring in single_counts.keys() if len(bitstring) != num_qubits
    ]
    if len(len_nomatch_bitstrings) > 0:
        raise ValueError(
            "The length of bitstring must be equal to the number of qubits, "
            + f"but following bitstrings are invalid: {len_nomatch_bitstrings}"
        )

    keys_int_array = [
        [
            (ord(c) - 48 + 10 * um_data[selected_cregs_sorted[q_idx]])
            for q_idx, c in enumerate(bit_string)
        ]
        for bit_string in single_counts.keys()
    ]
    values_int_array = list(single_counts.values())

    return keys_int_array, values_int_array


def rho_m_flatten_counts_list_vectorize_pyrust(
    counts_list: list[dict[str, int]],
    random_unitary_array: list[list[int]],
    selected_cregs_sorted: list[int],
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> list[tuple[list[list[int]], list[int]]]:
    """Dedicated function for rho_m_flatten counts list vectorized.

    Args:
        counts_list (list[dict[str, int]]):
            The list of counts measured from the single quantum circuit.
        random_unitary_array (list[list[int]]):
            The shadow direction of the unitary operators.
        selected_cregs_sorted (list[int]):
            The sorted list of **the index of the selected_classical_registers**.
        backend (PostProcessingBackendLabel, optional):
            Backend for the process. Defaults to "Rust".

    Returns:
        list[tuple[list[list[int]], list[int]]]: The counts under the degree.
    """
    if backend == "Rust":
        return rho_m_flatten_counts_list_vectorize_rust(
            counts_list, random_unitary_array, selected_cregs_sorted
        )

    num_qubits = len(selected_cregs_sorted)

    return [
        process_vectorize_single_counts(
            single_counts, random_unitary_array[um_idx], selected_cregs_sorted, num_qubits
        )
        for um_idx, single_counts in enumerate(counts_list)
    ]
