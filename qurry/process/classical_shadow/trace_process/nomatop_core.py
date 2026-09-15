"""Post Processing - Classical Shadow - Trace Process - Non-Matrix Operation Core
(:mod:`qurry.process.classical_shadow.trace_process.nomatop_core`)

"""

from collections.abc import Sequence

from .nomatmul import (
    nomatmul_trace_core,
    NonMatMulTraceMethod,
    NonMatMulTraceMethodType,
    DEFAULT_NONMATMUL_TRACE_METHOD,
)


def trace_nomatop_core(
    pauli_basis: Sequence[Sequence[int]],
    spin_outcome: Sequence[Sequence[int]],
    subsystem: Sequence[int],
    trace_method: NonMatMulTraceMethodType = DEFAULT_NONMATMUL_TRACE_METHOD,
) -> float:
    """Calculate the trace using non-matrix operation methods.

    Args:
        pauli_basis (Sequence[Sequence[int]]):
            The list of Pauli basis measurements. (X: 0, Y: 1, Z: 2)
        spin_outcome (Sequence[Sequence[int]]):
            The list of spin outcomes. (1, -1)
        subsystem (Sequence[int]):
            The subsystems.
        trace_method (NonMatMulTraceMethodType | str, optional):
            The method to use for the trace calculation without matrix multiplication.
            - "nomatmul_trace_py": Use pure Python implementation without multiprocessing.
            - "nomatmul_trace_rust": Use Rust implementation via PyO3.
            Default is DEFAULT_NONMATMUL_TRACE_METHOD.

    Returns:
        float: The purity.
    """

    if isinstance(trace_method, str):
        trace_method = NonMatMulTraceMethod.from_string(trace_method)

    return nomatmul_trace_core(pauli_basis, spin_outcome, subsystem, trace_method=trace_method)
