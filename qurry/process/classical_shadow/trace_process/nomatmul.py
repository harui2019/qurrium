"""Post Processing - Classical Shadow - Trace Process - Non-Matrix Multiplication Trace
(:mod:`qurry.process.classical_shadow.trace_process.nomatmul`)

"""

from collections.abc import Sequence, Iterable
from functools import reduce
from itertools import combinations

from ...utils import BaseMethodEnum
from ....tools import make_multiprocess_pool, DEFAULT_POOL_SIZE

# pylint: disable=import-error,no-name-in-module
from ....boorust.shadow import nomatmul_trace_sum_rust  # type: ignore


def rho_elt_compare(
    rho_ai_pauli: int, rho_bi_pauli: int, rho_ai_spin: int, rho_bi_spin: int
) -> float:
    """Calculate the trace of two classical shadows at a specific index.

    1. For random basis (Pauli basis) is not the same,
    the trace value will be `0.5`
    2. For random basis (Pauli basis) is the same,
    and the bitstring (spin) too, the trace value will be `5`
    3. For random basis (Pauli basis) is the same,
    but the bitstring (spin) is different, the trace value will be `-4`

    Args:
        rho_ai_pauli (int): Pauli basis from the first classical shadow. (X: 0, Y: 1, Z: 2)
        rho_bi_pauli (int): Pauli basis from the second classical shadow. (X: 0, Y: 1, Z: 2)
        rho_ai_spin (int): Spin value from the first classical shadow. (1, -1)
        rho_bi_spin (int): Spin value from the second classical shadow. (1, -1)

    Returns:
        float: The trace value calculated from the two shadows at the specified index.
    """
    return 0.5 if rho_ai_pauli != rho_bi_pauli else (5 if rho_ai_spin == rho_bi_spin else -4)


def get_trace(
    rho_a_pauli: Sequence[int],
    rho_a_spin: Sequence[int],
    rho_b_pauli: Sequence[int],
    rho_b_spin: Sequence[int],
    subsystem: Sequence[int],
) -> float:
    """Calculate the trace of two classical shadows.

    Args:
        rho_a_pauli (Sequence[int]): Pauli basis from the first shadow. (X: 0, Y: 1, Z: 2)
        rho_a_spin (Sequence[int]): Spin values from the first shadow. (1, -1)
        rho_b_pauli (Sequence[int]): Pauli basis from the second shadow. (X: 0, Y: 1, Z: 2)
        rho_b_spin (Sequence[int]): Spin values from the second shadow. (1, -1)
        subsystem (Sequence[int]): The subsystems.

    Returns:
        float: The trace value calculated from the two shadows.
    """
    if len(subsystem) == 0:
        return 1.0

    return reduce(
        lambda x, y: x * y,
        [
            rho_elt_compare(rho_a_pauli[i], rho_b_pauli[i], rho_a_spin[i], rho_b_spin[i])
            for i in subsystem
        ],
    )


def trace_calculation_unit(
    pauli_basis: Sequence[Sequence[int]],
    spin_outcome: Sequence[Sequence[int]],
    subsystem: Sequence[int],
    list_of_pairs: Iterable[tuple[int, int]],
) -> float:
    """Calculate the trace for all pairs of classical shadows.

    Args:
        pauli_basis (Sequence[Sequence[int]]):
            The list of Pauli basis measurements. (X: 0, Y: 1, Z: 2)
        spin_outcome (Sequence[Sequence[int]]):
            The list of spin outcomes. (1, -1)
        subsystem (Sequence[int]):
            The subsystems.
        list_of_pairs (Iterable[tuple[int, int]]):
            Pairs of indices for which to calculate the trace.

    Returns:
        float: The total trace value calculated from all pairs.
    """

    return sum(
        get_trace(pauli_basis[m1], spin_outcome[m1], pauli_basis[m2], spin_outcome[m2], subsystem)
        for m1, m2 in list_of_pairs
    )


def trace_calculation_unit_wrapper(
    args: tuple[
        Sequence[Sequence[int]], Sequence[Sequence[int]], Sequence[int], Iterable[tuple[int, int]]
    ],
) -> float:
    """Wrapper function for multiprocessing to calculate trace.

    Args:
        args (tuple[
            Sequence[Sequence[int]], Sequence[Sequence[int]],
            Sequence[int], Iterable[tuple[int, int]]
        ]):
            Tuple containing:
            - pauli_basis: The list of Pauli basis measurements. (X: 0, Y: 1, Z: 2)
            - spin_outcome: The list of spin outcomes. (1, -1)
            - subsystem: The subsystems.
            - list_of_pairs: Pairs of indices for which to calculate the trace.
    Returns:
        float: The trace value calculated from the two shadows.
    """
    return trace_calculation_unit(*args)


def nomatmul_trace_sum_py(
    pauli_basis: Sequence[Sequence[int]],
    spin_outcome: Sequence[Sequence[int]],
    subsystem: Sequence[int],
    multiprocessing: bool = False,
) -> float:
    """Perform the trace calculation for the given data and subsystems using Python.

    Args:
        pauli_basis (Sequence[Sequence[int]]):
            The list of Pauli basis measurements. (X: 0, Y: 1, Z: 2)
        spin_outcome (Sequence[Sequence[int]]):
            The list of spin outcomes. (1, -1)
        subsystem (Sequence[int]):
            The subsystems.
        multiprocessing (bool):
            Whether to use multiprocessing for the calculation.

    Returns:
        float: The result of the trace calculation.
    """

    num_of_samples = len(pauli_basis)

    if not multiprocessing or DEFAULT_POOL_SIZE <= 1:
        return sum(
            get_trace(
                pauli_basis[m1], spin_outcome[m1], pauli_basis[m2], spin_outcome[m2], subsystem
            )
            for m1, m2 in combinations(range(num_of_samples), 2)
        )

    with make_multiprocess_pool() as pool:
        results = pool.imap_unordered(
            trace_calculation_unit_wrapper,
            (
                (
                    pauli_basis,
                    spin_outcome,
                    subsystem,
                    [(i, j) for j in range(i + 1, num_of_samples)],
                )
                for i in range(num_of_samples)
            ),
            chunksize=max(1, num_of_samples // DEFAULT_POOL_SIZE // 2),
        )
        trace_m1_m2 = sum(results)
    return trace_m1_m2


class NonMatMulTraceMethod(BaseMethodEnum):
    """The method to use for the trace calculation without matrix multiplication.

    - "nomatmul_trace_py": Use pure Python implementation without multiprocessing.
    - "nomatmul_trace_py_mp": Use pure Python implementation with multiprocessing.
    - "nomatmul_trace_rust": Use Rust implementation via PyO3.

    The default method is "nomatmul_trace_rust", which is the fastest option.
    """

    NOMATMUL_TRACE_PY = "nomatmul_trace_py"
    """Use pure Python implementation without multiprocessing."""

    NOMATMUL_TRACE_PY_MP = "nomatmul_trace_py_mp"
    """Use pure Python implementation with multiprocessing."""

    NOMATMUL_TRACE_RUST = "nomatmul_trace_rust"
    """Use Rust implementation via PyO3."""

    @classmethod
    def get_default(cls) -> "NonMatMulTraceMethod":
        """Get the default trace calculation method.

        Returns:
            NonMatMulTraceMethod: The default method, which is NOMATMUL_TRACE_RUST.
        """
        return cls.NOMATMUL_TRACE_RUST


NonMatMulTraceMethodType = NonMatMulTraceMethod | str
"""The method to use for the trace calculation without matrix multiplication.

- "nomatmul_trace_py": Use pure Python implementation without multiprocessing.
- "nomatmul_trace_py_mp": Use pure Python implementation with multiprocessing.
- "nomatmul_trace_rust": Use Rust implementation via PyO3.

The default method is "nomatmul_trace_rust", which is the fastest option.
"""

DEFAULT_NONMATMUL_TRACE_METHOD: NonMatMulTraceMethod = NonMatMulTraceMethod.get_default()


def nomatmul_trace_sum(
    pauli_basis: Sequence[Sequence[int]],
    spin_outcome: Sequence[Sequence[int]],
    subsystem: Sequence[int],
    trace_method: NonMatMulTraceMethodType = DEFAULT_NONMATMUL_TRACE_METHOD,
) -> float:
    """Perform the trace calculation for the given data and subsystems.

    Args:
        pauli_basis (Sequence[Sequence[int]]):
            The list of Pauli basis measurements. (X: 0, Y: 1, Z: 2)
        spin_outcome (Sequence[Sequence[int]]):
            The list of spin outcomes. (1, -1)
        subsystem (Sequence[int]):
            The subsystems.
        trace_method (NonMatMulTraceMethodType):
            The method to use for the trace calculation.
            - "nomatmul_trace_py": Use pure Python implementation without multiprocessing.
            - "nomatmul_trace_py_mp": Use pure Python implementation with multiprocessing.
            - "nomatmul_trace_rust": Use Rust implementation via PyO3.
            Default is DEFAULT_NONMATMUL_TRACE_METHOD.

    Returns:
        float: The result of the trace calculation.
    """
    if isinstance(trace_method, str):
        trace_method = NonMatMulTraceMethod.from_string(trace_method)

    if trace_method == NonMatMulTraceMethod.NOMATMUL_TRACE_PY:
        return nomatmul_trace_sum_py(pauli_basis, spin_outcome, subsystem, multiprocessing=False)
    if trace_method == NonMatMulTraceMethod.NOMATMUL_TRACE_PY_MP:
        return nomatmul_trace_sum_py(pauli_basis, spin_outcome, subsystem, multiprocessing=True)
    if trace_method == NonMatMulTraceMethod.NOMATMUL_TRACE_RUST:
        return nomatmul_trace_sum_rust(pauli_basis, spin_outcome, subsystem)

    raise NonMatMulTraceMethod.value_error()


def nomatmul_trace_core(
    pauli_basis: Sequence[Sequence[int]],
    spin_outcome: Sequence[Sequence[int]],
    subsystem: Sequence[int],
    trace_method: NonMatMulTraceMethodType = DEFAULT_NONMATMUL_TRACE_METHOD,
) -> float:
    """Calculate the purity of the quantum state from the measurement data
    in string format without using matrix multiplication.

    Args:
        pauli_basis (Sequence[Sequence[int]]):
            The list of Pauli basis measurements. (X: 0, Y: 1, Z: 2)
        spin_outcome (Sequence[Sequence[int]]):
            The list of spin outcomes. (1, -1)
        subsystem (Sequence[int]):
            The subsystems.
        trace_method (NonMatMulTraceMethodType):
            The method to use for the trace calculation.
            - "nomatmul_trace_py": Use pure Python implementation without multiprocessing.
            - "nomatmul_trace_py_mp": Use pure Python implementation with multiprocessing.
            - "nomatmul_trace_rust": Use Rust implementation via PyO3.
            Default is DEFAULT_NONMATMUL_TRACE_METHOD.

    Returns:
        float: The calculated purity of the quantum state.
    """
    if len(pauli_basis) != len(spin_outcome):
        raise ValueError(
            "Length mismatch: pauli_basis: "
            + f"{len(pauli_basis)} != spin_outcome: {len(spin_outcome)}"
        )
    num_of_samples = len(pauli_basis)
    if num_of_samples < 2:
        raise ValueError("At least two samples are required to calculate purity.")

    trace_m1_m2 = nomatmul_trace_sum(pauli_basis, spin_outcome, subsystem, trace_method)

    return 2 * trace_m1_m2 / (num_of_samples * (num_of_samples - 1))
