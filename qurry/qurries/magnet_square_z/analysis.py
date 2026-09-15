"""ZDirMagnetSquare - Analysis (:mod:`qurry.qurries.magnet_square_z.analysis`)"""

from typing import Literal, Any
from dataclasses import dataclass
import numpy as np

from .arguments import ZMSArguments
from ...qurrium import (
    Commonparams,
    AnalysisPrototype,
    AnalyzeArgs,
    AnalysisMiddlewarePrototype,
    ProcessEntriesPrototype,
    AnalysisResultsPrototype,
)
from ...process.magnet_square.magnet_square import (
    z_dir_magnetization_square,
    MagnetSquareResult,
    DEFAULT_PROCESS_BACKEND,
    PostProcessingBackendLabel,
)


class ZMSAnalyzeArgs(AnalyzeArgs, total=False):
    """The input of :meth:`~qurry.qurrium.qurrium.QurriumPrototype.multiAnalysis` and
    :meth:`~qurry.qurries.magnet_square_z.experiment.ZMSExperiment.analyze`.

    The post-processing of
    :class:`~qurry.qurries.magnet_square_z.experiment.ZMSExperiment`
    does not need any input.
    """


@dataclass(frozen=True)
class ZMSMiddleware(AnalysisMiddlewarePrototype):
    """The middleware entries between analyze and actual post-processing function."""

    __name__ = "ZMSMiddleware"


@dataclass(frozen=True)
class ZMSProcessEntries(ProcessEntriesPrototype):
    """The entries for post-processing."""

    __name__ = "ZMSProcessEntries"

    num_qubits: int
    """The number of qubits."""


@dataclass(frozen=True)
class ZMSDefaultResult(AnalysisResultsPrototype):
    """The default results of :class:`~qurry.qurries.magnet_square_z.analysis.ZMSAnalysis`."""

    __name__ = "ZMSDefaultResult"

    magnet_square: float | np.float64
    """Magnetic Square."""
    magnet_square_cells: dict[int, float] | dict[int, np.float64]
    """Magnetic Square cells."""
    taking_time: float | None = None
    """Taking time."""

    def side_product_fields(self) -> tuple[str, ...]:
        """The fields that will be stored as side product."""
        return ("magnet_square_cells",)

    def export(self) -> dict[str, Any]:
        """Export the serializable data.

        Returns:
            dict[str, Any]: The serializable data.
        """
        return {
            "magnet_square": float(self.magnet_square),
            "magnet_square_cells": {int(k): float(v) for k, v in self.magnet_square_cells.items()},
            "taking_time": self.taking_time,
        }

    @classmethod
    def ingest(cls, raw_dict: dict[str, Any]):
        """Ingest from a serialized dictionary.

        Args:
            raw_dict (dict[str, Any]): The raw serialized dictionary.

        Returns:
            The class instance created from the raw dictionary.
        """
        missing_fields = set(cls.dataclass_fields()) - set(raw_dict.keys())
        if missing_fields:
            raise ValueError(f"Missing fields for {cls.__name__}: {missing_fields}")

        return cls(
            magnet_square=float(raw_dict["magnet_square"]),
            magnet_square_cells={
                int(k): float(v) for k, v in raw_dict["magnet_square_cells"].items()
            },
            taking_time=raw_dict.get("taking_time"),
        )


class ZMSAnalysis(
    AnalysisPrototype[
        ZMSArguments,
        ZMSAnalyzeArgs,
        ZMSMiddleware,
        ZMSProcessEntries,
        dict[Literal["default"] | str, type[ZMSDefaultResult]],
        dict[str | Literal["default"], ZMSDefaultResult],
    ]
):
    """The container for the analysis of
    :class:`~qurry.qurries.magnet_square_z.experiment.ZMSExperiment`."""

    __name__ = "ZMSAnalysis"

    @classmethod
    def analyze_arguments_type(cls) -> type[ZMSAnalyzeArgs]:
        """The analyze arguments type for this analysis."""
        return ZMSAnalyzeArgs

    @classmethod
    def middleware_entries_type(cls) -> type[ZMSMiddleware]:
        """The middleware entries type for this analysis."""
        return ZMSMiddleware

    @classmethod
    def postprocess_entries_type(cls) -> type[ZMSProcessEntries]:
        """The post-processing entries type for this analysis."""
        return ZMSProcessEntries

    @classmethod
    def available_results_types(cls) -> dict[str | Literal["default"], type[ZMSDefaultResult]]:
        """The results type for this analysis."""
        return {"default": ZMSDefaultResult}

    @classmethod
    def quantities(
        cls,
        shots: int,
        single_counts: dict[str, int],
        num_qubits: int,
        backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    ) -> MagnetSquareResult:
        """Calculate magnet square with more information combined.

        Args:
            shots (int): The number of shots.
            single_counts (dict[str, int]): Single count.
            num_qubits (int): The number of qubits.
            backend (PostProcessingBackendLabel, optional):
                The backend label. Defaults to DEFAULT_PROCESS_BACKEND.

        Returns:
            MagnetSquareResult: The result of the magnet square.
        """

        return z_dir_magnetization_square(
            shots=shots, single_counts=single_counts, num_qubits=num_qubits, backend=backend
        )

    @classmethod
    def generate_entries(
        cls,
        arguments: ZMSArguments,
        commonparams: Commonparams,
        counts: list[dict[str, int]],
        analyze_arguments: ZMSAnalyzeArgs,
    ) -> tuple[ZMSAnalyzeArgs, ZMSMiddleware, ZMSProcessEntries]:
        """Generate the entries for analysis.

        Hint:
            Hadamard test does not need any specific entries.

        Args:
            arguments (ZMSArguments): The arguments for the experiment.
            commonparams (Commonparams): The common parameters for the experiment.
            counts (list[dict[str, int]]): The counts from the experiment.
            analyze_arguments (ZMSAnalyzeArgs): The analyze arguments.

        Returns:
            The generated entries for analysis.
        """
        if len(counts) != 1:
            raise ValueError(
                "The number of counts should be one for ZdirMagnetSquare, "
                + f"but got {len(counts)}."
            )

        middleware_entries = ZMSMiddleware()
        postprocess_entries = ZMSProcessEntries(
            shots=commonparams.shots, num_qubits=arguments.num_qubits
        )

        return analyze_arguments, middleware_entries, postprocess_entries

    @classmethod
    def perform_analysis(
        cls,
        arguments: ZMSArguments,
        commonparams: Commonparams,
        counts: list[dict[str, int]],
        analyze_arguments: ZMSAnalyzeArgs,
        serial: int,
        outfields: dict[str, Any] | None = None,
        datetime: str | None = None,
    ):
        """Perform the analysis for the experiment.

        Args:
            arguments (ZMSArguments): The arguments for the experiment.
            commonparams (Commonparams): The common parameters for the experiment.
            counts (list[dict[str, int]]): The counts from the experiment.
            analyze_arguments (ZMSAnalyzeArgs): The analyze arguments.
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
            single_counts=counts[0],
            num_qubits=postprocess_entries.num_qubits,
        )
        results = ZMSDefaultResult(
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
