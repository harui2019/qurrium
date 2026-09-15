"""Analysis Instance (:mod:`qurry.qurrium.analysis.analysis`)"""

from typing import Any, Generic, TypeVar, cast
from abc import abstractmethod

from .declare import _RA
from .ers import _RR, implementation_check_results, _RM, _PE, implementation_check_entries
from ..arguments import _A, Commonparams
from ..exceptions import InvalidInherition
from ...capsule import jsonablize, Hoshi
from ...capsule.mori import DataExportableIngestible
from ...tools.datetime import current_time


ResultTypeDictBase = dict[str, type[_RR]]
"""The type alias for result type dictionary base."""

_RTD = TypeVar("_RTD", bound=ResultTypeDictBase)
"""The type variable for result type dictionary."""

ResultInstanceDictBase = dict[str, _RR]
"""The type alias for result dictionary base."""

_RID = TypeVar("_RID", bound=ResultInstanceDictBase)
"""The type alias for result dictionary type."""


class AnalysisPrototype(Generic[_A, _RA, _RM, _PE, _RTD, _RID], DataExportableIngestible):
    """The base instance for the analysis of
    :class:`~qurry.qurrium.experiment.experiment.ExperimentPrototype`."""

    __name__ = "AnalysisPrototype"

    serial: int
    """Serial Number of analysis."""
    datetime: str
    """Written time of analysis."""
    log: dict[str, Any]
    """Other info will be recorded."""

    analyze_arguments: _RA
    """The analyze arguments of the analysis."""
    middleware_entries: _RM
    """The middleware entries of the analysis."""
    postprocess_entries: _PE
    """The postprocess entries of the analysis."""

    outfields: dict[str, Any]
    """The unused arguments of the analysis."""

    results: _RID
    """The results of the analysis."""

    def __eq__(self, other) -> bool:
        """Check if two analysis instances are equal."""
        if not isinstance(other, self.__class__):
            raise TypeError("Can only compare with the same AnalysisPrototype subclass.")
        return (
            self.middleware_entries == other.middleware_entries
            and self.postprocess_entries == other.postprocess_entries
        )

    @classmethod
    @abstractmethod
    def analyze_arguments_type(cls) -> type[_RA]:
        """The input type of the analysis."""
        raise NotImplementedError("input_type must be implemented in subclass.")

    @classmethod
    @abstractmethod
    def middleware_entries_type(cls) -> type[_RM]:
        """The input type of the analysis."""
        raise NotImplementedError("input_type must be implemented in subclass.")

    @classmethod
    @abstractmethod
    def postprocess_entries_type(cls) -> type[_PE]:
        """The content type of the analysis."""
        raise NotImplementedError("content_type must be implemented in subclass.")

    @classmethod
    @abstractmethod
    def available_results_types(cls) -> _RTD:
        """The available results types of the analysis."""
        raise NotImplementedError("available_results_types must be implemented in subclass.")

    @classmethod
    def is_auto_analysis(cls) -> bool:
        """Check if the analysis is an auto analysis,
        which means no any analyze inputs are needed.

        Returns:
            bool: True if the analysis is an auto analysis, False otherwise.
        """
        return (
            len(cls.analyze_arguments_type().__required_keys__)
            + len(cls.analyze_arguments_type().__optional_keys__)
        ) == 0

    def __init__(
        self,
        analyze_arguments: _RA,
        middleware_entries: _RM,
        postprocess_entries: _PE,
        results: _RID,
        outfields: dict[str, Any] | None = None,
        *,
        serial: int,
        datetime: str | None = None,
    ):
        if not hasattr(self, "quantities") and not callable(getattr(self, "quantities", None)):
            raise InvalidInherition(
                f"{self.__name__} must have 'quantities' function defined in the subclass."
            )
        implementation_check_entries(middleware_entries, postprocess_entries, self.__name__)
        implementation_check_results(results, self.available_results_types(), self.__name__)

        self.serial = serial
        self.datetime = current_time() if datetime is None else datetime

        self.analyze_arguments = analyze_arguments
        self.middleware_entries = middleware_entries
        self.postprocess_entries = postprocess_entries
        self.results = results

        self.outfields = outfields if isinstance(outfields, dict) else {}

    @classmethod
    @abstractmethod
    def generate_entries(
        cls,
        arguments: _A,
        commonparams: Commonparams,
        counts: list[dict[str, int]],
        analyze_arguments: _RA,
    ) -> tuple[_RA, _RM, _PE] | tuple[_RA, _RM, _PE, Any]:
        """Generate the middleware and input values for the analysis.

        Args:
            arguments (_A): The arguments of the experiment.
            commonparams (Commonparams): The common parameters of the experiment.
            counts (list[dict[str, int]]): The counts data from the experiment.
            analyze_arguments (_RA): The analyze arguments of the analysis.

        Returns:
            A tuple containing the analyze arguments, middleware entries,
            and postprocess entries for the analysis.
        """
        raise NotImplementedError("generate_input_values must be implemented in subclass.")

    @classmethod
    def perform_analysis(
        cls,
        arguments: _A,
        commonparams: Commonparams,
        counts: list[dict[str, int]],
        analyze_arguments: _RA,
        serial: int,
        outfields: dict[str, Any] | None = None,
        datetime: str | None = None,
    ) -> "AnalysisPrototype":
        """Perform the analysis with the given arguments and common parameters.

        Args:
            arguments (_A): The arguments of the experiment.
            commonparams (Commonparams): The common parameters of the experiment.
            counts (list[dict[str, int]]): The counts data from the experiment.
            analyze_arguments (_RA): The analyze arguments of the analysis.
            serial (int): The serial number of the analysis.
            outfields (dict[str, Any] | None, optional):
                The unused arguments of the analysis. Defaults to None.
            datetime (str | None, optional):
                The datetime of the analysis. Defaults to None.

        Returns:
            AnalysisPrototype: The analysis instance.
        """
        raise NotImplementedError("analyze must be implemented in subclass.")

    def __repr__(self) -> str:
        contents = [
            f"serial={self.serial}",
            f"{self.postprocess_entries}",
            f"unused_args_num={len(self.outfields)}",
        ]
        return f"<{self.__name__}({', '.join(contents)})"

    def statesheet(self, hoshi: bool = False) -> Hoshi:
        """Generate the state sheet of the analysis.

        Args:
            hoshi (bool, optional):
                If True, show Hoshi name in statesheet. Defaults to False.
        Returns:
            Hoshi: The state sheet of the analysis.
        """
        info = Hoshi(
            [
                ("h1", f"{self.__name__} with serial={self.serial}"),
            ],
            name="Hoshi" if hoshi else "QurryAnalysisSheet",
        )
        info.newline(("itemize", "serial", self.serial, "", 1))
        info.newline(("itemize", "datetime", self.datetime, "", 1))

        info.newline(("itemize", "analyze_arguments"))
        for k, v in self.analyze_arguments.items():
            info.newline(("itemize", str(k), str(v), (), 2))

        info.newline(("itemize", "middleware_entries"))
        for k in self.middleware_entries.fields:
            info.newline(("itemize", str(k), getattr(self.middleware_entries, k), "", 2))

        info.newline(("itemize", "postprocess_entries"))
        for k in self.postprocess_entries.fields:
            info.newline(("itemize", str(k), getattr(self.postprocess_entries, k), "", 2))
        info.newline(("itemize", "results"))
        for k, v in self.results.items():
            info.newline(("itemize", str(k)))
            for field in v.fields:
                if field in v.side_product_fields():
                    info.newline(("itemize", str(field), str(getattr(v, field)), "", 4))

        info.newline(
            ("itemize", "outfields", len(self.outfields), "Number of unused arguments.", 1)
        )
        for k, v in self.outfields.items():
            info.newline(("itemize", str(k), str(v), "", 2))

        info.newline(("itemize", "log"))
        for k, v in self.log.items():
            info.newline(("itemize", str(k), str(v), "", 2))

        return info

    def export(self) -> dict[str, Any]:
        """Export the analysis for file writing.

        Returns:
            dict[str, Any]: The analysis as a dictionary for file writing.
        """

        return {
            "__class__": self.__class__.__name__,
            "header": {"serial": self.serial, "datetime": self.datetime},
            "analyze_arguments": jsonablize(self.analyze_arguments),
            "postprocess_entries": self.postprocess_entries.export(),
            "middleware_entries": self.middleware_entries.export(),
            "results": {k: v.export() for k, v in self.results.items()},
            "outfields": jsonablize(self.outfields),
        }

    @classmethod
    def ingest(cls, raw_dict: dict[str, Any]):
        """Load the analysis from a raw read dictionary.

        Args:
            raw_dict (dict[str, Any]): The raw read dictionary.

        Returns:
            The analysis instance.
        """
        missing_keys = {
            "__class__",
            "header",
            "analyze_arguments",
            "postprocess_entries",
            "middleware_entries",
            "results",
        } - set(raw_dict.keys())
        if missing_keys:
            raise ValueError(f"Missing fields for {cls.__name__}: {', '.join(missing_keys)}")
        if raw_dict["__class__"] != cls.__name__:
            raise ValueError(
                f"The raw read dictionary class '{raw_dict['__class__']}' does not match "
                f"the expected class '{cls.__name__}'."
            )

        postprocess_entries = cls.postprocess_entries_type().ingest(raw_dict["postprocess_entries"])
        middleware_entries = cls.middleware_entries_type().ingest(raw_dict["middleware_entries"])
        results = cast(
            _RID,
            {k: cls.available_results_types()[k].ingest(v) for k, v in raw_dict["results"].items()},
        )
        outfields = raw_dict.get("outfields", {})

        return cls(
            raw_dict["analyze_arguments"],
            middleware_entries,
            postprocess_entries,
            results,
            outfields,
            serial=raw_dict["header"]["serial"],
            datetime=raw_dict["header"].get("datetime", None),
        )

    def results_fields(self) -> tuple[tuple[str, str], ...]:
        """Get the fields of results.

        Returns:
            tuple[str, ...]: The fields of results.
        """
        result_key_with_fields = [
            [(key, field) for field in result.fields] for key, result in self.results.items()
        ]

        return tuple(sum(result_key_with_fields, []))

    def results_items(self, serialized: bool = False) -> tuple[tuple[tuple[str, str], Any], ...]:
        """Get the items of results.

        Args:
            serialized (bool, optional):
                If True, return the serialized items. Defaults to False.

        Returns:
            tuple[tuple[tuple[str, str], Any], ...]: The items of results.
        """
        if serialized:
            serialized_results = {k: v.export() for k, v in self.results.items()}
            for result_exports in serialized_results.values():
                result_exports.pop("__class__", None)
            result_key_with_serialized_values = [
                [((key, field), result[field]) for field in result.keys()]
                for key, result in serialized_results.items()
            ]
            return tuple(sum(result_key_with_serialized_values, []))

        result_key_with_values = [
            [((key, field), getattr(result, field)) for field in result.fields]
            for key, result in self.results.items()
        ]
        return tuple(sum(result_key_with_values, []))

    def __getitem__(self, key_and_field: tuple[str, str]) -> Any:
        """Get the result by key and field.
        Args:
            key_and_field (tuple[str, str]): The key and field of the result.
        Returns:
            Any: The result value.
        """
        key, field = key_and_field
        if key not in self.results:
            raise KeyError(f"Key '{key}' not found in results.")
        if field not in self.results[key].fields:
            raise KeyError(f"Field '{field}' not found in results for key '{key}'.")
        return getattr(self.results[key], field)


_R = TypeVar("_R", bound=AnalysisPrototype)
"""Type variable for :class:`~qurry.qurrium.analysis.AnalysisPrototype`."""
