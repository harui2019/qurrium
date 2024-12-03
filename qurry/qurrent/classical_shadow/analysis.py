"""
===========================================================
ShadowUnveil - Analysis
(:mod:`qurry.qurrent.classical_shadow.analysis`)
===========================================================

"""

from typing import Optional, NamedTuple, Iterable, Literal
import numpy as np

from ...qurrium.analysis import AnalysisPrototype


class ShadowUnveilAnalysis(AnalysisPrototype):
    """The container for the analysis of :cls:`EntropyRandomizedExperiment`."""

    __name__ = "ShadowUnveilAnalysis"

    class AnalysisInput(NamedTuple):
        """To set the analysis."""

        num_qubits: int
        """The number of qubits."""
        selected_qubits: list[int]
        """The selected qubits."""
        registers_mapping: dict[int, int]
        """The mapping of the classical registers with quantum registers.

        .. code-block:: python
            {
                0: 0, # The quantum register 0 is mapped to the classical register 0.
                1: 1, # The quantum register 1 is mapped to the classical register 1.
                5: 2, # The quantum register 5 is mapped to the classical register 2.
                7: 3, # The quantum register 7 is mapped to the classical register 3.
            }

        The key is the index of the quantum register with the numerical order.
        The value is the index of the classical register with the numerical order.
        """
        shots: int
        """The number of shots."""
        unitary_located: Optional[list[int]] = None
        """The range of the unitary operator."""

    input: AnalysisInput

    class AnalysisContent(NamedTuple):
        """The content of the analysis."""

        expect_rho: np.ndarray[tuple[int, int], np.dtype[np.complex128]]
        """The expectation value of Rho."""
        purity: float
        """The purity calculated by classical shadow."""
        entropy: float
        """The entropy calculated by classical shadow."""

        rho_m_dict: dict[int, np.ndarray[tuple[int, int], np.dtype[np.complex128]]]
        """The dictionary of Rho M."""
        rho_m_i_dict: dict[
            int, dict[int, np.ndarray[tuple[Literal[2], Literal[2]], np.dtype[np.complex128]]]
        ]
        """The dictionary of Rho M I."""
        classical_registers_actually: list[int]
        """The list of the selected_classical_registers."""
        taking_time: float
        """The time taken for the calculation."""

        def __repr__(self):
            return f"AnalysisContent(purity={self.purity}, entropy={self.entropy}, and others)"

    @property
    def side_product_fields(self) -> Iterable[str]:
        """The fields that will be stored as side product."""
        return [
            "rho_m_dict",
            "rho_m_i_dict",
        ]

    content: AnalysisContent
