"""Post Processing - Classical Shadow - Trace Process - Core
(:mod:`qurry.process.classical_shadow.trace_process.trace_core`)

"""

import time
from typing import Literal
import warnings
import numpy as np
import numpy.typing as npt

from .nomatop_core import NonMatMulTraceMethod, trace_nomatop_core
from .rho_core import RhoTraceMethod, trace_rho_square_core
from ..utils import convert_to_basis_spin
from ...utils import NUMERICAL_ERROR_TOLERANCE, BaseMethodEnum, FloatType


class TraceMethod(BaseMethodEnum):
    """The method to calculate the trace of rho.

    - Matrix operation methods:
        For the matrix operation methods, it will require rho has been calculated first.
        - "trace_of_matmul": Use `np.trace(np.matmul(rho_m1, rho_m2))`
            to calculate the each summation item in `rho_m_list`.
        - "einsum_ij_ji": Use `np.einsum("ij,ji", rho_m1, rho_m2)`
            to calculate the each summation item in `rho_m_list`.
        - "einsum_aij_bji_to_ab_numpy": Use
            `np.einsum("aij,bji->ab", rho_m_list, rho_m_list)` to calculate the trace.
            This is the fastest implementation to calculate the trace of Rho.

    - Non-matrix operation methods:
        - "nomatmul_trace_py": Use pure Python implementation without multiprocessing.
        - "nomatmul_trace_rust": Use Rust implementation via PyO3.

    - Skip calculation of trace:
        - "skip_trace": Skip the trace calculation and return NaN.

    For the non-matrix operation methods, it will directly calculate the trace from
    the counts and random basis.
    """

    # Matrix operation methods
    TRACE_OF_MATMUL = RhoTraceMethod.TRACE_OF_MATMUL.value
    """Use `np.trace(np.matmul(rho_m1, rho_m2))` to calculate
    the each summation item in `rho_m_list`."""
    EINSUM_IJ_JI = RhoTraceMethod.EINSUM_IJ_JI.value
    """Use `np.einsum("ij,ji", rho_m1, rho_m2)` to calculate
    the each summation item in `rho_m_list`."""
    EINSUM_AIJ_BJI_TO_AB_NUMPY = RhoTraceMethod.EINSUM_AIJ_BJI_TO_AB_NUMPY.value
    """Use `np.einsum("aij,bji->ab", rho_m_list, rho_m_list)` to calculate the trace."""

    # Non-matrix operation methods
    NOMATMUL_TRACE_PY = NonMatMulTraceMethod.NOMATMUL_TRACE_PY.value
    """Use pure Python implementation without multiprocessing."""
    NOMATMUL_TRACE_RUST = NonMatMulTraceMethod.NOMATMUL_TRACE_RUST.value
    """Use Rust implementation via PyO3."""

    SKIP_TRACE = "skip_trace"
    """Skip the trace calculation and return NaN."""

    @classmethod
    def get_default(cls) -> "TraceMethod":
        """Get the default method.

        Returns:
            TraceMethod: The default method.
        """
        return cls.NOMATMUL_TRACE_RUST

    def is_singleshots_method(self) -> bool:
        """Whether it is a singleshots method.

        Returns:
            bool: True if it is a singleshots method, False otherwise.
        """
        return self in [self.NOMATMUL_TRACE_PY, self.NOMATMUL_TRACE_RUST]

    @classmethod
    def get_single_methods(cls) -> list[str]:
        """Get a list of all avaialble non-matrix operation methods.

        Returns:
            list[str]: A list of avaialble non-matrix operation methods.
        """
        return [cls.NOMATMUL_TRACE_PY.value, cls.NOMATMUL_TRACE_RUST.value]

    def is_nomatop_method(self) -> bool:
        """Whether it is a nomatmul method.

        Returns:
            bool: True if it is a nomatmul method, False otherwise.
        """
        return self.is_singleshots_method()

    def is_skip_method(self) -> bool:
        """Whether it is a skip method.

        Returns:
            bool: True if it is a skip method, False otherwise.
        """
        return self == self.SKIP_TRACE

    @classmethod
    def get_nomatop_methods(cls) -> list[str]:
        """Get a list of all avaialble nomatmul methods.

        Returns:
            list[str]: A list of avaialble nomatmul methods.
        """
        return cls.get_single_methods()

    def to_nomatop_enum(self) -> NonMatMulTraceMethod:
        """Convert to NonMatMulTraceMethod enum.

        Raises:
            ValueError: If the method is not a nomatmul method.

        Returns:
            NonMatMulTraceMethod: The corresponding NonMatMulTraceMethod enum.
        """
        if not self.is_nomatop_method():
            raise ValueError(f"{self.value} is not a nomatmul method")
        return NonMatMulTraceMethod.from_string(self.value)

    def is_matrixop_method(self) -> bool:
        """Whether it is a matrix operation method.

        Returns:
            bool: True if it is a matrix operation method, False otherwise.
        """
        return self in [
            self.TRACE_OF_MATMUL,
            self.EINSUM_IJ_JI,
            self.EINSUM_AIJ_BJI_TO_AB_NUMPY,
        ]

    @classmethod
    def get_all_matrixop_methods(cls) -> list[str]:
        """Get a list of all avaialble matrix operation methods.

        Returns:
            list[str]: A list of avaialble matrix operation methods.
        """
        return [
            cls.TRACE_OF_MATMUL.value,
            cls.EINSUM_IJ_JI.value,
            cls.EINSUM_AIJ_BJI_TO_AB_NUMPY.value,
        ]

    def to_matrixop_enum(self) -> RhoTraceMethod:
        """Convert to RhoTraceMethod enum.

        Raises:
            ValueError: If the method is not a matrix operation method.

        Returns:
            RhoTraceMethod: The corresponding RhoTraceMethod enum.
        """
        if not self.is_matrixop_method():
            raise ValueError(f"{self.value} is not a matrix operation method")
        return RhoTraceMethod.from_string(self.value)


TraceMethodType = TraceMethod | str
"""The method to calculate the trace of rho.

- Matrix operation methods:
    For the matrix operation methods, it will require rho has been calculated first.
    - "trace_of_matmul": Use `np.trace(np.matmul(rho_m1, rho_m2))`
        to calculate the each summation item in `rho_m_list`.
    - "einsum_ij_ji": Use `np.einsum("ij,ji", rho_m1, rho_m2)`
        to calculate the each summation item in `rho_m_list`.
    - "einsum_aij_bji_to_ab_numpy": Use
        `np.einsum("aij,bji->ab", rho_m_list, rho_m_list)` to calculate the trace.
        This is the fastest implementation to calculate the trace of Rho.

- Non-matrix operation methods:
    - "nomatmul_trace_py": Use pure Python implementation without multiprocessing.
    - "nomatmul_trace_rust": Use Rust implementation via PyO3.

- Skip calculation of trace:
    - "skip_trace": Skip the trace calculation and return NaN.

For the non-matrix operation methods, it will directly calculate the trace from
the counts and random basis.
"""


DEFAULT_TRACE_METHOD: TraceMethod = TraceMethod.get_default()
"""The default method for the trace calculation of rho."""


def all_trace_core(
    shots: int,
    counts: list[dict[str, int]],
    random_basis_array: list[list[Literal[0, 1, 2] | int]],
    rho_m_list: list[npt.NDArray[np.complex128]],
    selected_classical_registers_sorted: list[int],
    trace_method: TraceMethodType = DEFAULT_TRACE_METHOD,
) -> tuple[FloatType, FloatType, float]:
    """Calculate the trace by all given methods.

    Args:
        shots (int):
            The number of shots.
        counts (list[dict[str, int]]):
            The list of the counts.
        random_basis_array (list[list[Literal[0, 1, 2] | int]]):
            The random basis for classical shadow.
        rho_m_list (list[npt.NDArray[np.complex128]]):
            The list of Rho M.
            It should be a list of 2-dimensional arrays.
        selected_classical_registers_sorted (list[int]):
            The **sorted** list of the index of the selected classical registers.

        trace_method (TraceMethodType, optional):
            The method to calculate the trace of rho.

            - Matrix operation methods:
                For the matrix operation methods, it will require rho has been calculated first.
                - "trace_of_matmul": Use `np.trace(np.matmul(rho_m1, rho_m2))`
                    to calculate the each summation item in `rho_m_list`.
                - "einsum_ij_ji": Use `np.einsum("ij,ji", rho_m1, rho_m2)`
                    to calculate the each summation item in `rho_m_list`.
                - "einsum_aij_bji_to_ab_numpy": Use
                    `np.einsum("aij,bji->ab", rho_m_list, rho_m_list)` to calculate the trace.
                    This is the fastest implementation to calculate the trace of Rho.

            - Non-matrix operation methods:
                - "nomatmul_trace_py": Use pure Python implementation without multiprocessing.
                - "nomatmul_trace_rust": Use Rust implementation via PyO3.

            - Skip calculation of trace:
                - "skip_trace": Skip the trace calculation and return NaN.

            For the non-matrix operation methods, it will directly calculate the trace from
            the counts and random basis.

            Default to DEFAULT_TRACE_METHOD.

    Returns:
        tuple[FloatType, FloatType, float]:
            The purity, the second Renyi entropy, and the time taken (in seconds).
    """

    if isinstance(trace_method, str):
        trace_method = TraceMethod.from_string(trace_method)

    begin = time.time()

    if trace_method == TraceMethod.SKIP_TRACE:
        return np.nan, np.nan, 0.0

    if trace_method.is_nomatop_method():
        selected_clreg_sorted = sorted(selected_classical_registers_sorted)
        pauli_basis, spin_outcome = convert_to_basis_spin(shots, counts, random_basis_array)

        purity = trace_nomatop_core(
            pauli_basis=pauli_basis,
            spin_outcome=spin_outcome,
            subsystem=selected_clreg_sorted,
            trace_method=trace_method.to_nomatop_enum(),
        )
        return purity, -np.log2(purity), time.time() - begin

    trace_rho_sum = trace_rho_square_core(
        rho_m_list=rho_m_list, trace_method=trace_method.to_matrixop_enum()
    )
    if np.abs(trace_rho_sum.imag) > NUMERICAL_ERROR_TOLERANCE:
        warnings.warn(
            "The imaginary part of the trace of Rho square is not zero. "
            f"The imaginary part is {trace_rho_sum.imag}. method: {trace_method}",
            RuntimeWarning,
        )
    return trace_rho_sum.real, -np.log2(trace_rho_sum.real), time.time() - begin
