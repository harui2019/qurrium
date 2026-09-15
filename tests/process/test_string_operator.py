"""Test qurry.process.string_operator module."""

from typing import TypedDict, Literal
from itertools import combinations
import logging
import pytest

from qurry.process.string_operator import (
    string_operator_availability,
    string_operator_order,
    StringOperatorResult,
)

from .utilities import (
    quick_json_read,
    get_dummy_file_path,
    assert_numerical_tolerance_check,
    FloatType,
    assert_and_logging_rust_available,
)


logger = logging.getLogger(__name__)


class StringOperatorTarget(TypedDict):
    """The test target type for string_operator_core function parameters."""

    shots: int
    """Number of shots."""
    counts: list[dict[str, int]]
    """The counts dictionary list."""
    str_op: Literal["i", "zy"]
    """The string operator to be applied."""
    i: int
    """The start index for measurement range."""
    k: int
    """The end index for measurement range."""


class StringOperatorCase(TypedDict):
    """The test case type for string_operator_core function."""

    target: StringOperatorTarget
    """The target parameters for the string_operator_core function."""
    answer: StringOperatorResult
    """The expected answer from the string_operator_core function."""
    case_tags: tuple[Literal["i", "zy"], str]
    """String operator and circuit name tags."""


def process_json_read(raw_read_item: dict) -> StringOperatorCase:
    """Process the raw JSON read case into StringOperatorCase."""
    return {
        "target": raw_read_item["target"],
        "answer": raw_read_item["answer"],
        "case_tags": tuple(raw_read_item["case_tags"][:2]),
    }


DUMMY_CASE_FILE = get_dummy_file_path("string_operator.json")
DUMMY_CASES_JSON = [process_json_read(case) for case in quick_json_read(DUMMY_CASE_FILE)]
string_operator_cases_entries = [
    (case["target"], case["answer"], case["case_tags"]) for case in DUMMY_CASES_JSON
]


ANSWERS = {
    "i": {
        "trivial_5": 1.0,
        "trivial_6": 1.0,
        "trivial_7": 1.0,
        "trivial_8": 1.0,
        "trivial_9": 1.0,
        "topological_6": 0.0,
        "topological_8": 0.0,
    },
    "zy": {
        "trivial_7": 0.0,
        "trivial_8": 0.0,
        "trivial_9": 0.0,
        "topological_8": 1.0,
    },
}

ANSWERS_ERROR = 0.05


def test_availability():
    """Test the availability of the Rust backend for the string_operator function."""

    assert_and_logging_rust_available([string_operator_availability], logger)


@pytest.mark.parametrize(["target", "answer", "case_tags"], string_operator_cases_entries)
def test_string_operator(
    target: StringOperatorTarget,
    answer: StringOperatorResult,
    case_tags: tuple[Literal["i", "zy"], str],
):
    """Test the string_operator_core function."""

    assert len(target["counts"]) == 1, (
        "The counts should be a single item for the string_operator_core function."
    )

    py_result = string_operator_order(
        shots=target["shots"],
        counts=target["counts"],
        backend="Python",
    )
    rust_result = string_operator_order(
        shots=target["shots"],
        counts=target["counts"],
        backend="Rust",
    )

    comparison_target: list[tuple[str, FloatType]] = [
        ("Python", py_result["order"]),
        ("Rust", rust_result["order"]),
        ("Numerical Answer", answer["order"]),
    ]
    for (name_1, result_1), (name_2, result_2) in combinations(comparison_target, 2):
        assert_numerical_tolerance_check(
            "string_operator_core",
            result_1,
            name_1,
            result_2,
            name_2,
            logger,
        )
    for name_1, result_1 in comparison_target:
        assert_numerical_tolerance_check(
            "string_operator_core",
            result_1,
            name_1,
            ANSWERS[case_tags[0]][case_tags[1]],
            "Answer",
            logger,
            ANSWERS_ERROR
        )
