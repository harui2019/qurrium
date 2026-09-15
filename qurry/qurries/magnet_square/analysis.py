"""MagnetSquare - Analysis (:mod:`qurry.qurries.magnet_square.analysis`)"""

from typing import Literal, Any
from dataclasses import dataclass
import numpy as np
import numpy.typing as npt

from .arguments import MSArguments
from ..magnet_square_z.analysis import (
    ZMSAnalyzeArgs,
    ZMSMiddleware,
    ZMSProcessEntries,
    ZMSDefaultResult,
)
from ...qurrium import Commonparams, AnalysisPrototype
from ...process.magnet_square.magnet_square import (
    magnetization_square,
    MagnetSquareResult,
    DEFAULT_PROCESS_BACKEND,
    PostProcessingBackendLabel,
)


class MSAnalyzeArgs(ZMSAnalyzeArgs, total=False):
    """The input of :meth:`~qurry.qurrium.qurrium.QurriumPrototype.multiAnalysis` and
    :meth:`~qurry.qurries.magnet_square.experiment.MSExperiment.analyze`.

    The post-processing of
    :class:`~qurry.qurries.magnet_square.experiment.MSExperiment`
    does not need any input.
    """


@dataclass(frozen=True)
class MSMiddleware(ZMSMiddleware):
    """The middleware entries between analyze and actual post-processing function."""

    __name__ = "MSMiddleware"

    unitary_operator: Literal["x", "y", "z"] | str | npt.NDArray[np.complex128]
    """The numpy array of the unitary operator or a string representing the axis of rotation."""

    def export(self) -> dict[str, Any]:
        """Export the middleware entries to a dictionary.

        Returns:
            dict[str, Any]: The exported dictionary.
        """
        if isinstance(self.unitary_operator, str):
            return {"unitary_operator": self.unitary_operator}
        if not isinstance(self.unitary_operator, np.ndarray):
            raise TypeError(
                f"Field 'unitary_operator' expected type 'np.ndarray' or 'str', "
                f"but received '{type(self.unitary_operator)}'."
            )

        return {"unitary_operator": np.array(self.unitary_operator, dtype=str).tolist()}

    @classmethod
    def ingest(cls, raw_dict: dict[str, Any]):
        """Ingest the middleware entries from a dictionary.

        Args:
            raw_dict (dict[str, Any]): The raw dictionary.

        Returns:
            MSMiddleware: The ingested middleware entries.
        """
        if "unitary_operator" not in raw_dict:
            raise ValueError("Missing field 'unitary_operator' for MSMiddleware.")
        unitary_operator = raw_dict["unitary_operator"]
        if isinstance(unitary_operator, list):
            unitary_operator = np.array(unitary_operator, dtype=np.complex128)

        return cls(unitary_operator=unitary_operator)


@dataclass(frozen=True)
class MSProcessEntries(ZMSProcessEntries):
    """The entries for post-processing."""

    __name__ = "MSProcessEntries"

    num_qubits: int
    """The number of qubits."""


@dataclass(frozen=True)
class MSDefaultResult(ZMSDefaultResult):
    """The default results of :class:`~qurry.qurries.magnet_square.analysis.MSAnalysis`."""

    __name__ = "MSDefaultResult"


class MSAnalysis(
    AnalysisPrototype[
        MSArguments,
        MSAnalyzeArgs,
        MSMiddleware,
        MSProcessEntries,
        dict[Literal["default"] | str, type[MSDefaultResult]],
        dict[str | Literal["default"], MSDefaultResult],
    ]
):
    """The container for the analysis of
    :class:`~qurry.qurries.magnet_square.experiment.MSExperiment`."""

    __name__ = "MSAnalysis"

    @classmethod
    def analyze_arguments_type(cls) -> type[MSAnalyzeArgs]:
        """The analyze arguments type for this analysis."""
        return MSAnalyzeArgs

    @classmethod
    def middleware_entries_type(cls) -> type[MSMiddleware]:
        """The middleware entries type for this analysis."""
        return MSMiddleware

    @classmethod
    def postprocess_entries_type(cls) -> type[MSProcessEntries]:
        """The post-processing entries type for this analysis."""
        return MSProcessEntries

    @classmethod
    def available_results_types(cls) -> dict[str | Literal["default"], type[MSDefaultResult]]:
        """The results type for this analysis."""
        return {"default": MSDefaultResult}

    @classmethod
    def quantities(
        cls,
        shots: int,
        counts: list[dict[str, int]],
        num_qubits: int,
        backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    ) -> MagnetSquareResult:
        """Calculate magnet square with more information combined.

        Args:
            shots (int): The number of shots.
            counts (list[dict[str, int]]): The counts of the experiment.
            num_qubits (int): The number of qubits.
            backend (PostProcessingBackendLabel, optional):
                The backend label. Defaults to DEFAULT_PROCESS_BACKEND.

        Returns:
            MagnetSquareResult: The result of the magnet square.
        """

        return magnetization_square(
            shots=shots, counts=counts, num_qubits=num_qubits, backend=backend
        )

    @classmethod
    def generate_entries(
        cls,
        arguments: MSArguments,
        commonparams: Commonparams,
        counts: list[dict[str, int]],
        analyze_arguments: MSAnalyzeArgs,
    ) -> tuple[MSAnalyzeArgs, MSMiddleware, MSProcessEntries]:
        """Generate the entries for analysis.

        Hint:
            Hadamard test does not need any specific entries.

        Args:
            arguments (MSArguments): The arguments for the experiment.
            commonparams (Commonparams): The common parameters for the experiment.
            counts (list[dict[str, int]]): The counts from the experiment.
            analyze_arguments (MSAnalyzeArgs): The analyze arguments.

        Returns:
            The generated entries for analysis.
        """
        unitary_operator_converted = (
            arguments.unitary_operator
            if isinstance(arguments.unitary_operator, str)
            else np.array(arguments.unitary_operator, dtype=np.complex128)
        )

        middleware_entries = MSMiddleware(unitary_operator=unitary_operator_converted)
        postprocess_entries = MSProcessEntries(
            shots=commonparams.shots, num_qubits=arguments.num_qubits
        )

        return analyze_arguments, middleware_entries, postprocess_entries

    @classmethod
    def perform_analysis(
        cls,
        arguments: MSArguments,
        commonparams: Commonparams,
        counts: list[dict[str, int]],
        analyze_arguments: MSAnalyzeArgs,
        serial: int,
        outfields: dict[str, Any] | None = None,
        datetime: str | None = None,
    ):
        """Perform the analysis for the experiment.

        Args:
            arguments (MSArguments): The arguments for the experiment.
            commonparams (Commonparams): The common parameters for the experiment.
            counts (list[dict[str, int]]): The counts from the experiment.
            analyze_arguments (MSAnalyzeArgs): The analyze arguments.
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

        ms_result_dict = cls.quantities(
            shots=postprocess_entries.shots,
            counts=counts,
            num_qubits=postprocess_entries.num_qubits,
        )
        results = MSDefaultResult(
            magnet_square=ms_result_dict["magnet_square"],
            magnet_square_cells=ms_result_dict["magnet_square_cells"],
            taking_time=ms_result_dict["taking_time"],
        )

        return cls(
            analyze_arguments=analyze_arguments,
            middleware_entries=middleware_entries,
            postprocess_entries=postprocess_entries,
            results={"default": results},
            serial=serial,
            outfields=outfields,
            datetime=datetime,
        )
