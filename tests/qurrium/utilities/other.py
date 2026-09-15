"""Miscellaneous utilities for testing. (:mod:`utilities.other`)"""

from typing import Generic, cast, TypeVar
import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
import logging
import numpy as np

from qurry.qurrium import QurriumPrototype
from qurry.qurrium.container import _MA
from qurry.qurrium.analysis import _RA, AnalysisResultsPrototype
from qurry.process.utils import NUMERICAL_ERROR_TOLERANCE

FloatType = float | np.float64
"""The type alias for :class:`float` and :class:`~numpy.float64`."""


def get_test_export_dir() -> Path:
    """Get the export directory for test outputs.

    Returns:
        Path: The export directory path
    """

    current_dir = os.path.dirname(__file__)
    tests_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
    if os.path.basename(os.path.abspath(tests_root)) != "tests":
        raise RuntimeError("The tests root directory could not be determined.")
    return Path(tests_root) / "exports"


EXPORT_DIR = get_test_export_dir()
"""The export directory for test outputs."""


@dataclass(frozen=True)
class CaseEntries(Generic[_MA, _RA]):
    """The case entries tuple for testing."""

    tags: tuple[str, ...]
    """The tags associated with the test item."""
    measure_entries: _MA
    """The measurement input draft."""
    analyze_entries: _RA
    """The analysis input."""
    expect_answer: dict[str, tuple[str, float]]
    """The expected answer on respecting results and fields."""

    def measure_entries_with_tags(self, *more_tags: str) -> _MA:
        """Get the measurement input.

        Args:
            more_tags (str):
                Additional tags to include.

        Returns:
            _MA: The measurement input.
        """
        return cast(_MA, {**self.measure_entries, "tags": self.tags + more_tags})

    @property
    def name(self) -> str:
        """Get the item name from the tags.

        Returns:
            str: The item name.
        """
        return tags_to_name(self.tags)


@dataclass(frozen=True)
class AnalysisResultChecker:
    """The analysis result check report."""

    name: str
    """The name of the test item."""
    result_name: str
    """The name of the analysis result."""
    target_field: str
    """The name of the target field."""
    got_answer: float
    """The answer from the quantity."""
    expect_answer: float
    """The expected answer to compare against."""
    diff: float
    """The difference between the answer and the expected answer."""
    threshold: float
    """The threshold for the check."""

    @property
    def is_correct(self) -> bool:
        """Check if the answer is correct within the threshold.

        Returns:
            bool: True if the answer is correct, False otherwise.
        """
        return self.diff < self.threshold

    def make_logger(self, logger: logging.Logger, extra_msg: str | None = None) -> str:
        """Make logger string for the report.

        Args:
            logger (logging.Logger): The logger to use.
            extra_msg (str | None, optional):
                Extra message to include. Defaults to None.

        Returns:
            str: The logger string.
        """
        status = "PASS" if self.is_correct else "FAIL"
        msg = (
            f"{status} - {self.name} - {self.result_name}.{self.target_field} | "
            + f"Got: {self.got_answer}, Expect: {self.expect_answer}, "
            + f"Diff: {self.diff} < Threshold: {self.threshold}"
        )
        if extra_msg is not None:
            msg += f" | {extra_msg}"
        if self.is_correct:
            logger.info(msg)
        else:
            logger.error(msg)

        return msg

    def assert_correct(self) -> None:
        """Assert that the answer is correct.

        Raises:
            AssertionError: If the answer is not correct.
        """
        assert self.is_correct, (
            f"{self.name} | The result of '{self.target_field}' is not correct: "
            + f"{self.diff} !< {self.threshold}, {self.got_answer} != {self.expect_answer}."
        )


def check_analysis_result(
    result: AnalysisResultsPrototype,
    result_name: str,
    target_field: str,
    expect_answer: float,
    name: str,
    threshold: float = NUMERICAL_ERROR_TOLERANCE,
    other_fields: list[str] | None = None,
) -> AnalysisResultChecker:
    """Check the analysis result for a specific field.

    Args:
        result (AnalysisResultsPrototype): The analysis result to check.
        result_name (str): The name of the analysis result.
        target_field (str): The name of the target field to check.
        expect_answer (float): The expected answer to compare against.
        name (str): The name of the test item.
        threshold (float, optional): The threshold for the check.
            Defaults to NUMERICAL_ERROR_TOLERANCE.
        other_fields (list[str] | None, optional):
            Other fields to check for existence. Defaults to None.

    Returns:
        AnalysisResultCheckReport: The report of the analysis result check.
    """

    assert target_field in result.fields, (
        f"{name} | The necessary quantities '{target_field}' "
        + f" not found in quantity. Quantity: {result.fields}"
    )
    if other_fields is not None:
        assert all(k in result.fields for k in other_fields), (
            f"{name} | The other fields '{other_fields}' "
            + f" not found in quantity. Quantity: {result.fields}"
        )

    diff = np.abs(getattr(result, target_field) - expect_answer)

    return AnalysisResultChecker(
        name=name,
        result_name=result_name,
        target_field=target_field,
        got_answer=float(getattr(result, target_field)),
        expect_answer=expect_answer,
        diff=float(diff),
        threshold=threshold,
    )


def tags_to_name(iterable: Iterable[str]) -> str:
    """Make an item name from an iterable of strings.

    Args:
        iterable (Iterable[str]): The iterable of strings.

    Returns:
        str: The item name.
    """
    item_name = ".".join(iterable)
    if item_name:
        return item_name
    raise ValueError("The iterable is empty, cannot create an item name.")


def make_config_list_and_tagged_case(
    case_entries_list: list[CaseEntries[_MA, _RA]],
) -> tuple[list[_MA], dict[tuple[str, ...], CaseEntries[_MA, _RA]]]:
    """Create configuration list and tagged case entries from a list of case entries.

    Args:
        case_entries_list (list[CaseEntriesTuple[_MA, _RA]]):
            The list of case entries.

    Returns:
        A tuple containing the configuration list and the tagged case entries.
    """
    config_list = []
    cases_with_tags: dict[tuple[str, ...], CaseEntries[_MA, _RA]] = {}

    for i, case_entries in enumerate(case_entries_list):
        config = case_entries.measure_entries_with_tags(f"index_{i}")
        if "tags" not in config:
            config["tags"] = (f"index_{i}",)
        config_list.append(config)
        cases_with_tags[config["tags"]] = case_entries  # type: ignore

    return config_list, cases_with_tags


_CET = TypeVar("_CET", bound=CaseEntries)
"""The type variable for CaseEntriesTuple."""


def make_specific_analysis_args(
    exp_method: QurriumPrototype,
    summoner_id: str,
    analysis_entries_dict: dict[tuple[str, ...], _CET],
):
    """Create specific analysis arguments for a given experiment method and summoner ID.

    Args:
        exp_method (QurriumPrototype): The experiment method.
        summoner_id (str): The ID of the summoner.
        analysis_args (dict[tuple[str, ...], dict[str, Any]]): The analysis arguments.

    Returns:
        dict[str, dict[str, Any]]:
            A dictionary mapping experiment IDs to their specific analysis arguments.
    """

    return {
        exp_id: analysis_entries_dict[config["tags"]].analyze_entries
        for exp_id, config in exp_method.multimanagers[summoner_id].beforewards.exps_config.items()
    }


def multi_read_tests_exported_files(
    exp_method: QurriumPrototype, summoner_id: str, save_location: Path
) -> None:
    """Multi-read the exported files for testing.

    Args:
        exp_method (QurriumPrototype): The experiment method.
        summoner_id (str): The ID of the summoner.
        save_location (Path): The location where the files are saved.
    """

    read_summoner_id = exp_method.multiRead(
        summoner_name=exp_method.multimanagers[summoner_id].summoner_name,
        save_location=save_location,
    )
    assert read_summoner_id == summoner_id, (
        f"The read summoner id is wrong: {read_summoner_id} != {summoner_id}."
    )
