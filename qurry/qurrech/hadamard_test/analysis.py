"""
================================================================
Wave Function Overlap - Hadamard Test Analysis
(:mod:`qurry.qurrech.hadamard_test.analysis`)
================================================================

"""

from typing import NamedTuple, Iterable

from ...qurrium.analysis import AnalysisPrototype
from ...process.hadamard_test import hadamard_overlap_echo as overlap_echo


class EchoListenHadamardAnalysis(AnalysisPrototype):
    """The analysis for calculating entangled entropy with more information combined."""

    __name__ = "qurrechHadamard.Analysis"
    shortName = "qurrech_hadamard.report"

    class AnalysisInput(NamedTuple):
        """To set the analysis."""

    input: AnalysisInput

    class AnalysisContent(NamedTuple):
        """The content of the analysis."""

        echo: float
        """The purity of the system."""

        def __repr__(self):
            return f"AnalysisContent(echo={self.echo}, and others)"

    content: AnalysisContent

    @property
    def side_product_fields(self) -> Iterable[str]:
        """The fields that will be stored as side product."""
        return []

    @classmethod
    def quantities(
        cls,
        shots: int,
        counts: list[dict[str, int]],
    ) -> dict[str, float]:
        """Calculate entangled entropy with more information combined.

        Args:
            shots (int): Shots of the experiment on quantum machine.
            counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
            degree (Union[tuple[int, int], int]): Degree of the subsystem.
            measure (tuple[int, int], optional):
                Measuring range on quantum circuits. Defaults to None.
            workers_num (Optional[int], optional):
                Number of multi-processing workers,
                if sets to 1, then disable to using multi-processing;
                if not specified, the use 3/4 of cpu counts by `round(cpu_count*3/4)`.
                Defaults to None.

        Returns:
            dict[str, float]: A dictionary contains
                purity, entropy.
        """

        result = overlap_echo(
            shots=shots,
            counts=counts,
        )
        return result
