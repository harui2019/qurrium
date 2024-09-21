"""
================================================================
SamplingExecuter - Analysis
(:mod:`qurry.qurrium.samplingqurry.analysis`)
================================================================

It is only for pendings and retrieve to remote backend.
"""

from typing import NamedTuple, Iterable

from ..analysis import AnalysisPrototype


class QurryAnalysis(AnalysisPrototype):
    """Example of QurryAnalysis."""

    __name__ = "QurryAnalysis"

    class AnalysisInput(NamedTuple):
        """To set the analysis."""

        ultimate_question: str
        """ULtImAte QueStIoN."""

    input: AnalysisInput

    class AnalysisContent(NamedTuple):
        """Analysis content."""

        utlmatic_answer: int
        """~The Answer to the Ultimate Question of Life, The Universe, and Everything.~"""
        dummy: int
        """Just a dummy field."""

    content: AnalysisContent

    @property
    def side_product_fields(self) -> Iterable[str]:
        """The fields that will be stored as side product."""
        return ["dummy"]
