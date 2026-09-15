"""The Entries and Result definitions for analysis. (:mod:`qurry.qurrium.analysis.ers`)"""

from typing import Any, TypeVar, ParamSpec, Concatenate
from collections.abc import Callable
from dataclasses import dataclass, fields
import warnings

from ..exceptions import InvalidInherition
from ...capsule import DEFAULT_INDENT, jsonablize
from ...capsule.mori import DataExportableIngestible

_ERABC = TypeVar("_ERABC", bound="AnalysisERABC")
"""Type variable for :class:`AnalysisERABC`."""

P = ParamSpec("P")


def erabc_export(
    func: Callable[Concatenate[_ERABC, P], dict[str, Any]],
) -> Callable[Concatenate[_ERABC, P], dict[str, Any]]:
    """The decorator for export method of :class:`AnalysisERABC` to include class name.

    Args:
        func (Callable): The original export function.
    """

    def wrapper(self: _ERABC, *args: P.args, **kwargs: P.kwargs) -> dict[str, Any]:
        """The wrapped export function including class name."""
        result = {"__class__": self.__class__.__name__}
        result.update(func(self, *args, **kwargs))
        if result["__class__"] != self.__class__.__name__:
            raise InvalidInherition(
                "The exported class name got modified. "
                + f"Expected '{self.__class__.__name__}', got '{result['__class__']}'. "
                + "You should not modify the '__class__' key in export method.",
            )

        missing_fields = set(self.dataclass_fields()) - set(result.keys())
        if missing_fields:
            raise InvalidInherition(
                f"Got some missing fields for '{self.__class__.__name__}': {missing_fields}. "
                + "You should export all fields in export method."
            )

        return result

    # pylint: disable=protected-access
    wrapper._erabc_exported_decorated = True  # type: ignore[attr-defined]
    # pylint: enable=protected-access

    return wrapper


_ERABCIngest = TypeVar("_ERABCIngest", bound=Callable)


def erabc_ingest(func: _ERABCIngest) -> _ERABCIngest:
    """The decorator for ingest method of :class:`AnalysisERABC` to check class name.

    Args:
        func (Callable): The original load function.
    """

    def wrapper(cls: _ERABC, raw_dict: dict[str, Any], *args: P.args, **kwargs: P.kwargs) -> _ERABC:
        """The wrapped load function including class name check."""

        raw_dict_copy = raw_dict.copy()

        classname = raw_dict_copy.pop("__class__", None)
        if classname is None:
            raise ValueError("Data does not contain '__class__' key.")
        if classname != cls.__name__:
            raise ValueError(
                f"Data class '{classname}' does not match expected class '{cls.__name__}'."
            )

        missing_fields = set(cls.dataclass_fields()) - set(raw_dict.keys())
        if missing_fields:
            raise ValueError(f"Missing fields for '{cls.__name__}': {missing_fields}")

        result = func(cls, raw_dict_copy, *args, **kwargs)

        return result

    # pylint: disable=protected-access
    wrapper._erabc_ingested_decorated = True  # type: ignore[attr-defined]
    # pylint: enable=protected-access

    return wrapper  # type: ignore[return-value]


@dataclass(frozen=True)
class AnalysisERABC(DataExportableIngestible):
    """Construct the analyze entries's and results's parameters for specific options,
    which should be overwritable by the inherition class of this base class."""

    __name__ = "AnalysisERABC"

    @property
    def fields(self) -> tuple[str, ...]:
        """The fields of arguments."""
        return self.dataclass_fields()

    @classmethod
    def dataclass_fields(cls) -> tuple[str, ...]:
        """The fields of arguments."""
        return tuple(f.name for f in fields(cls))

    def asdict(self):
        """The arguments as dictionary."""
        return self.__dict__

    def __init_subclass__(cls, **kwargs):
        """Automatically apply decorator to make method."""
        super().__init_subclass__(**kwargs)

        if "export" in cls.__dict__:
            original_export = cls.__dict__.get("export")
            if original_export is None:
                raise InvalidInherition("The 'export' method must be defined.")

            if not hasattr(original_export, "_erabc_exported_decorated"):
                decorated_export = erabc_export(original_export)
                setattr(cls, "export", decorated_export)

        if "ingest" in cls.__dict__:
            original_ingest = cls.__dict__.get("ingest")
            if original_ingest is None or not isinstance(original_ingest, classmethod):
                raise InvalidInherition("The 'ingest' method must be defined and a classmethod.")
            original_func = original_ingest.__func__

            if not hasattr(original_func, "_erabc_ingested_decorated"):
                decorated_ingest = erabc_ingest(original_func)
                setattr(cls, "ingest", classmethod(decorated_ingest))

    def __post_init__(self):
        """Post-initialization to ensure all fields are present."""
        if self.__name__ == "AnalysisERABC":
            warnings.warn(
                "AnalysisERABC is a base class and should be inherited. "
                "Direct instantiation is discouraged. "
                "If you finish the inherition but still see this warning, "
                "then change the __name__ attribute of your derived class.",
                UserWarning,
            )

    @erabc_export
    def export(self) -> dict[str, Any]:
        """Export the serializable data.

        Returns:
            dict[str, Any]: The serializable data.
        """
        return {field: jsonablize(getattr(self, field)) for field in self.fields}

    @classmethod
    @erabc_ingest
    def ingest(cls, raw_dict: dict[str, Any]):
        """Ingest from a serialized dictionary.

        Args:
            raw_dict (dict[str, Any]): The raw serialized dictionary.

        Returns:
            The class instance created from the raw dictionary.
        """
        return cls(**raw_dict)

    def _repr_pretty_(self, p, cycle):
        if cycle:
            p.text(f"{self.__class__.__name__}" + "({...})")
            return

        with p.group(DEFAULT_INDENT, f"{self.__class__.__name__}(" + ", {", "})"):
            for i, (k, v) in enumerate(self.__dict__.items()):
                p.breakable()
                p.pretty(k)
                p.text("=")
                p.pretty(v)
                if i < len(self.__dict__) - 1:
                    p.text(",")


@dataclass(frozen=True)
class AnalysisMiddlewarePrototype(AnalysisERABC):
    """The middleware information between :func:`~qurry.qurrium.qurrium.QurriumPrototype.analyze`
    and actual post-processing function."""


_RM = TypeVar("_RM", bound=AnalysisMiddlewarePrototype)
"""Type variable for :class:`AnalysisMiddlewarePrototype`."""


@dataclass(frozen=True)
class ProcessEntriesPrototype(AnalysisERABC):
    """The entries for post-processing."""

    shots: int
    """The number of shots."""


_PE = TypeVar("_PE", bound=ProcessEntriesPrototype)
"""Type variable for :class:`ProcessEntriesPrototype`."""


def implementation_check_entries(
    middleware_entries: AnalysisMiddlewarePrototype,
    postprocess_entries: ProcessEntriesPrototype,
    analysis_name: str,
) -> None:
    """Check whether the derived class implements all required fields
    from the base class.

    Args:
        middleware_entries (AnalysisMiddlewarePrototype): The middleware entries to check.
        postprocess_entries (ProcessEntriesPrototype): The postprocess entries to check.
        analysis_name (str): The name of the analysis.

    Raises:
        QurryInvalidInherition: If the derived class does not implement all required fields.
    """
    duplicate_fields = (
        set(middleware_entries.fields)
        & set(postprocess_entries.fields)
        & {"serial", "datetime", "log"}
    )
    if len(duplicate_fields) > 0:
        raise InvalidInherition(
            f"{postprocess_entries}, and {middleware_entries} "
            f"should not have same fields: {duplicate_fields} "
            f"for {analysis_name}."
        )


@dataclass(frozen=True, repr=False)
class AnalysisResultsPrototype(AnalysisERABC):
    """The content of the analysis results."""

    def side_product_fields(self) -> tuple[str, ...]:
        """The fields that will be stored as side product."""
        return ()

    def main_and_side_product(self) -> tuple[dict[str, Any], dict[str, Any]]:
        """Export the results as two dictionaries: main results and side products.

        Returns:
            A tuple containing the main results and side products as dictionaries.
        """
        main_result = {}
        side_product = {}
        for field in self.fields:
            if field in self.side_product_fields():
                side_product[field] = getattr(self, field)
            else:
                main_result[field] = getattr(self, field)
        return main_result, side_product

    def __repr__(self) -> str:
        """String representation of the AnalyzeResultsPrototype."""
        field_strs = [
            f"{field}={getattr(self, field)!r}"
            for field in self.fields
            if field not in self.side_product_fields()
        ]
        field_strs += [f"side_product_fields={self.side_product_fields()!r}"]
        return f"{self.__class__.__name__}({', '.join(field_strs)})"

    def _repr_pretty_(self, p, cycle):
        if cycle:
            p.text(f"{self.__class__.__name__}" + "({...})")
            return

        with p.group(DEFAULT_INDENT, f"{self.__class__.__name__}(" + ", {", "})"):
            field_no_side_products = [
                field for field in self.fields if field not in self.side_product_fields()
            ]
            for k in field_no_side_products:
                p.breakable()
                p.pretty(k)
                p.text("=")
                p.pretty(getattr(self, k))
                p.text(",")
            p.breakable()
            p.text("side_product_fields=")
            p.pretty(self.side_product_fields())


_RR = TypeVar("_RR", bound=AnalysisResultsPrototype)
"""Type variable for :class:`AnalyzeResultsPrototype` during transformation."""


def implementation_check_results(
    results: dict[str, _RR],
    available_results_types: dict[str, type[_RR]],
    analysis_name: str,
) -> None:
    """Check whether the derived class implements all required fields
    from the base class.

    Args:
        results (dict[str, AnalyzeResultsPrototype]):
            The results to check.
        available_results_types (dict[str, type[AnalyzeResultsPrototype]]):
            The available results types to check.
        analysis_name (str): The name of the analysis.

    Raises:
        QurryInvalidInherition: If the derived class does not implement all required fields.
    """
    if any(
        rt_name not in available_results_types
        or not isinstance(results[rt_name], available_results_types[rt_name])
        for rt_name in results
    ):
        raise TypeError(
            f"Results types mismatch for {analysis_name}: "
            f"expected {list(available_results_types.keys())}, "
            f"got {list(results.keys())}."
        )
