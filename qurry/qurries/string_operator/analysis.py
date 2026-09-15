"""StringOperator - Analysis (:mod:`qurry.qurries.string_operator.analysis`)"""

from typing import Literal, Any
from dataclasses import dataclass
import numpy as np

from .arguments import SOArguments
from .utils import StringOperatorLibType, StringOperatorDirection
from ...qurrium import (
    Commonparams,
    AnalysisPrototype,
    AnalyzeArgs,
    AnalysisMiddlewarePrototype,
    ProcessEntriesPrototype,
    AnalysisResultsPrototype,
)
from ...process.string_operator.string_operator import (
    string_operator_order,
    StringOperatorResult,
    DEFAULT_PROCESS_BACKEND,
    PostProcessingBackendLabel,
)


class SOAnalyzeArgs(AnalyzeArgs, total=False):
    """The input of :meth:`~qurry.qurrium.qurrium.QurriumPrototype.multiAnalysis` and
    :meth:`~qurry.qurries.string_operator.experiment.SOxperiment.analyze`.
    """


@dataclass(frozen=True)
class SOMiddleware(AnalysisMiddlewarePrototype):
    """The middleware entries between analyze and actual post-processing function."""

    __name__ = "SOMiddleware"

    num_qubits: int
    """The number of qubits."""
    i: int
    """The index of beginning qubits in the quantum circuit."""
    k: int
    """The index of ending qubits in the quantum circuit."""
    length: int
    """The length of the string operator, which is k - i + 1."""
    str_op: StringOperatorLibType = "i"
    """The string operator."""
    on_dir: StringOperatorDirection = "x"
    """The direction of the string operator, either 'x' or 'y'."""


@dataclass(frozen=True)
class SOProcessEntries(ProcessEntriesPrototype):
    """The entries for post-processing."""

    __name__ = "SOProcessEntries"


@dataclass(frozen=True)
class SODefaultResult(AnalysisResultsPrototype):
    """The default results of :class:`~qurry.qurries.string_operator.analysis.SOAnalysis`."""

    __name__ = "SODefaultResult"

    order: float | np.float64
    """The order of the string operator."""

    def export(self) -> dict[str, Any]:
        """Export the result to a dictionary.

        Returns:
            dict[str, Any]: The exported dictionary.
        """
        return {"order": float(self.order)}


class SOAnalysis(
    AnalysisPrototype[
        SOArguments,
        SOAnalyzeArgs,
        SOMiddleware,
        SOProcessEntries,
        dict[Literal["default"] | str, type[SODefaultResult]],
        dict[Literal["default"] | str, SODefaultResult],
    ]
):
    """The container for the analysis of
    :class:`~qurry.qurries.string_operator.experiment.SOExperiment`."""

    __name__ = "SOAnalysis"

    @classmethod
    def analyze_arguments_type(cls) -> type[SOAnalyzeArgs]:
        """The analyze arguments type for this analysis."""
        return SOAnalyzeArgs

    @classmethod
    def middleware_entries_type(cls) -> type[SOMiddleware]:
        """The middleware entries type for this analysis."""
        return SOMiddleware

    @classmethod
    def postprocess_entries_type(cls) -> type[SOProcessEntries]:
        """The post-processing entries type for this analysis."""
        return SOProcessEntries

    @classmethod
    def available_results_types(cls) -> dict[str | Literal["default"], type[SODefaultResult]]:
        """The results type for this analysis."""
        return {"default": SODefaultResult}

    @classmethod
    def quantities(
        cls,
        shots: int,
        counts: list[dict[str, int]],
        backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    ) -> StringOperatorResult:
        """Calculate the string operator.

        Args:
            shots (int): The number of shots.
            counts (list[dict[str, int]]): The counts of the experiment.
            backend (PostProcessingBackendLabel, optional):
                The backend label. Defaults to DEFAULT_PROCESS_BACKEND.

        Returns:
            StringOperatorResult: The result of the magnet square.
        """

        return string_operator_order(shots=shots, counts=counts, backend=backend)

    @classmethod
    def generate_entries(
        cls,
        arguments: SOArguments,
        commonparams: Commonparams,
        counts: list[dict[str, int]],
        analyze_arguments: SOAnalyzeArgs,
    ) -> tuple[SOAnalyzeArgs, SOMiddleware, SOProcessEntries]:
        """Generate the entries for analysis.

        Hint:
            Hadamard test does not need any specific entries.

        Args:
            arguments (SOArguments): The arguments for the experiment.
            commonparams (Commonparams): The common parameters for the experiment.
            counts (list[dict[str, int]]): The counts from the experiment.
            analyze_arguments (SOAnalyzeArgs): The analyze arguments.

        Returns:
            The generated entries for analysis.
        """
        if len(counts) != 1:
            raise ValueError(
                "The number of counts should be one for StringOperator, "
                + f"but got {len(counts)}."
            )

        middleware_entries = SOMiddleware(
            num_qubits=arguments.num_qubits,
            i=arguments.i,
            k=arguments.k,
            length=arguments.k - arguments.i + 1,
            str_op=arguments.str_op,
            on_dir=arguments.on_dir,
        )
        postprocess_entries = SOProcessEntries(shots=commonparams.shots)

        return analyze_arguments, middleware_entries, postprocess_entries

    @classmethod
    def perform_analysis(
        cls,
        arguments: SOArguments,
        commonparams: Commonparams,
        counts: list[dict[str, int]],
        analyze_arguments: SOAnalyzeArgs,
        serial: int,
        outfields: dict[str, Any] | None = None,
        datetime: str | None = None,
    ):
        """Perform the analysis for the experiment.

        Args:
            arguments (SOArguments): The arguments for the experiment.
            commonparams (Commonparams): The common parameters for the experiment.
            counts (list[dict[str, int]]): The counts from the experiment.
            analyze_arguments (SOAnalyzeArgs): The analyze arguments.
            serial (int): The serial number of the analysis.
            outfields (dict[str, Any] | None, optional):
                The unused arguments of the analysis. Defaults to None.
            datetime (str | None, optional):
                The datetime of the analysis. Defaults to None.

        Returns:
            The result of the analysis.
        """
        analyze_arguments, middleware_entries, postprocess_entries = cls.generate_entries(
            arguments, commonparams, counts, analyze_arguments
        )

        ms_result_dict = cls.quantities(shots=postprocess_entries.shots, counts=counts)
        results = SODefaultResult(order=ms_result_dict["order"])

        return cls(
            analyze_arguments=analyze_arguments,
            middleware_entries=middleware_entries,
            postprocess_entries=postprocess_entries,
            results={"default": results},
            serial=serial,
            outfields=outfields,
            datetime=datetime,
        )
