"""SamplingExecuter - Analysis (:mod:`qurry.qurries.samplingqurry.analysis`))"""

from typing import Any, Literal
from dataclasses import dataclass

from ...qurrium import (
    Commonparams,
    AnalysisPrototype,
    AnalyzeArgs,
    AnalysisMiddlewarePrototype,
    ProcessEntriesPrototype,
    AnalysisResultsPrototype,
)
from ...qurrium.arguments import _A


class DummyAnalyzeArgs(AnalyzeArgs, total=False):
    """The input of :meth:`~qurry.qurrium.qurrium.QurriumPrototype.multiAnalysis`,
    :meth:`~qurry.qurries.samplingqurry.experiment.SEExperiment.analyze` and
    :meth:`~qurry.qurries.wavesqurry.experiment.WEExperiment.analyze`
    """

    ultimate_question: str | None
    """ULtImAte QueStIoN."""


@dataclass(frozen=True)
class DummyMiddleware(AnalysisMiddlewarePrototype):
    """The middleware entries between analyze and actual post-processing function."""

    __name__ = "DummyMiddleware"


@dataclass(frozen=True)
class DummyProcessEntries(ProcessEntriesPrototype):
    """The entries for post-processing."""

    __name__ = "DummyProcessEntries"

    ultimate_question: str | None
    """ULtImAte QueStIoN."""


@dataclass(frozen=True)
class DummyDefaultResults(AnalysisResultsPrototype):
    """The default results of :class:`~qurry.qurries.samplingqurry.analysis.SEAnalysis`."""

    __name__ = "DummyDefaultResults"

    ultimate_answer: int
    """~The Answer to the Ultimate Question of Life, The Universe, and Everything.~"""


class DummyAnalysis(
    AnalysisPrototype[
        _A,
        DummyAnalyzeArgs,
        DummyMiddleware,
        DummyProcessEntries,
        dict[Literal["default"] | str, type[DummyDefaultResults]],
        dict[
            str | Literal["default"],
            DummyDefaultResults,
        ],
    ]
):
    """A dummy analysis that always returns the ultimate answer."""

    __name__ = "DummyAnalysis"

    @classmethod
    def analyze_arguments_type(cls) -> type[DummyAnalyzeArgs]:
        """The analyze arguments type for this analysis."""
        return DummyAnalyzeArgs

    @classmethod
    def middleware_entries_type(cls) -> type[DummyMiddleware]:
        """The middleware entries type for this analysis."""
        return DummyMiddleware

    @classmethod
    def postprocess_entries_type(cls) -> type[DummyProcessEntries]:
        """The post-processing entries type for this analysis."""
        return DummyProcessEntries

    @classmethod
    def available_results_types(cls) -> dict[str | Literal["default"], type[DummyDefaultResults]]:
        """The results type for this analysis."""
        return {"default": DummyDefaultResults}

    @classmethod
    def quantities(cls) -> dict[str, int]:
        """Get the ultimate answer.

        Returns:
            dict[str, int]: The ultimate answer.
        """
        return {"ultimate_answer": 42}

    @classmethod
    def generate_entries(
        cls,
        arguments: _A,
        commonparams: Commonparams,
        counts: list[dict[str, int]],
        analyze_arguments: DummyAnalyzeArgs,
    ) -> tuple[DummyAnalyzeArgs, DummyMiddleware, DummyProcessEntries]:
        """Generate the entries for analysis.

        Hint:
            Hadamard test does not need any specific entries.

        Args:
            arguments (EMHArguments): The arguments for the experiment.
            commonparams (Commonparams): The common parameters for the experiment.
            counts (list[dict[str, int]]): The counts from the experiment.
            analyze_arguments (EMHAnalyzeArgs): The analyze arguments.

        Returns:
            The generated entries for analysis.
        """
        middleware_entries = DummyMiddleware()
        postprocess_entries = DummyProcessEntries(
            shots=commonparams.shots,
            ultimate_question=analyze_arguments.get("ultimate_question", "Just ask something."),
        )

        return analyze_arguments, middleware_entries, postprocess_entries

    @classmethod
    def perform_analysis(
        cls,
        arguments: _A,
        commonparams: Commonparams,
        counts: list[dict[str, int]],
        analyze_arguments: DummyAnalyzeArgs,
        serial: int,
        outfields: dict[str, Any] | None = None,
        datetime: str | None = None,
    ):
        """Perform the analysis for the experiment.

        Args:
            arguments (EMHArguments): The arguments for the experiment.
            commonparams (Commonparams): The common parameters for the experiment.
            counts (list[dict[str, int]]): The counts from the experiment.
            analyze_arguments (EMHAnalyzeArgs): The analyze arguments.
            serial (int): The serial number of the analysis.
            outfields (dict[str, Any] | None, optional):
                The unused arguments of the analysis. Defaults to None.
            datetime (str | None, optional):
                The datetime of the analysis. Defaults to None.

        Returns:
            AnalysisPrototype: The result of the analysis.
        """

        analyze_arguments, middleware_entries, postprocess_entries = cls.generate_entries(
            arguments, commonparams, counts, analyze_arguments
        )
        the_ultimatic_answer = cls.quantities()
        results = DummyDefaultResults(ultimate_answer=the_ultimatic_answer["ultimate_answer"])

        return cls(
            analyze_arguments=analyze_arguments,
            middleware_entries=middleware_entries,
            postprocess_entries=postprocess_entries,
            results={"default": results},
            serial=serial,
            outfields=outfields,
            datetime=datetime,
        )
