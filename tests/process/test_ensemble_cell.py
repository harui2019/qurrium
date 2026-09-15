"""Tests qurry.process.utils.randomized module."""

from typing import TypedDict
from itertools import combinations
import logging
import pytest

from qurry.process.utils import randomized_availability
from qurry.process.utils.randomized import ensemble_cell as ensemble_cell_py, ensemble_cell_rust

from .utilities import (
    quick_json_read,
    get_dummy_file_path,
    assert_numerical_tolerance_check,
    FloatType,
    assert_and_logging_rust_available,
)

logger = logging.getLogger(__name__)


class EnsembleTarget(TypedDict):
    """The test target type for ensemble_cell function parameters."""

    s_i: str
    """First count's qubits arrange."""
    s_i_meas: int
    """Counting value of the first register."""
    s_j: str
    """Second count's qubits arrange."""
    s_j_meas: int
    """Counting value of the second register."""
    a_num: int
    """Number of qubits."""
    shots: int
    """Number of shots."""


class EnsembleCase(TypedDict):
    """The test case type for ensemble_cell function."""

    target: EnsembleTarget
    """The target parameters for the ensemble_cell function."""
    answer: float
    """The expected answer from the ensemble_cell function."""
    note: str
    """Additional note for the test case."""


DUMMY_CASE_FILE = get_dummy_file_path("ensemble_cell.json")
DUMMY_CASES_JSON: list[EnsembleCase] = quick_json_read(DUMMY_CASE_FILE)
ensemble_cases_entries: list[tuple[EnsembleTarget, float]] = [
    (case["target"], case["answer"]) for case in DUMMY_CASES_JSON
]


def test_availability():
    """Test the availability of the Rust backend for the ensemble_cell function."""

    assert_and_logging_rust_available([randomized_availability], logger)


@pytest.mark.parametrize(["target", "answer"], ensemble_cases_entries)
def test_ensemble_cell_rust(target: EnsembleTarget, answer: float):
    """Test the ensemble_cell_rust function."""

    py_result = ensemble_cell_py(**target)
    rust_result = ensemble_cell_rust(**target)

    comparison_target: list[tuple[str, FloatType]] = [
        ("Python", py_result),
        ("Rust", rust_result),
        ("Numerical Answer", answer),
    ]
    for (name_1, result_1), (name_2, result_2) in combinations(comparison_target, 2):
        assert_numerical_tolerance_check(
            "ensemble_cell",
            result_1,
            name_1,
            result_2,
            name_2,
            logger,
        )
