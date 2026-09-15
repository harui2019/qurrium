"""Test qurry.process.hadamard_test module."""

from typing import TypedDict
from itertools import combinations
import logging
import pytest

from qurry.process.hadamard_test import purity_echo_core_availability
from qurry.process.hadamard_test.purity_echo_core import purity_echo_core

from .utilities import (
    quick_json_read,
    get_dummy_file_path,
    assert_numerical_tolerance_check,
    assert_and_logging_rust_available,
)

logger = logging.getLogger(__name__)


class HadamardTarget(TypedDict):
    """The test target type for hadamard_test purity_echo_core function parameters."""

    shots: int
    """Number of shots."""
    counts: list[dict[str, int]]
    """The counts dictionary list."""


class HadamardCase(TypedDict):
    """The test case type for hadamard_test purity_echo_core function."""

    target: HadamardTarget
    """The target parameters for the purity_echo_core function."""
    answer: float
    """The expected answer from the purity_echo_core function."""
    note: str
    """Additional note for the test case."""


DUMMY_CASE_FILE = get_dummy_file_path("hadamard.json")
DUMMY_CASES_JSON: list[HadamardCase] = quick_json_read(DUMMY_CASE_FILE)
hadamard_cases_entries = [(case["target"], case["answer"]) for case in DUMMY_CASES_JSON]


def test_availability():
    """Test the availability of the Rust backend for the purity_echo_core function."""

    assert_and_logging_rust_available([purity_echo_core_availability], logger)


@pytest.mark.parametrize(["target", "answer"], hadamard_cases_entries)
def test_hadamard(target: HadamardTarget, answer: float):
    """Test the purity_echo_core function."""

    rust_result = purity_echo_core(**target, backend="Rust")
    py_result = purity_echo_core(**target, backend="Python")

    comparison_target: list[tuple[str, float]] = [
        ("Python", py_result),
        ("Rust", rust_result),
        ("Numerical Answer", answer),
    ]
    for (name_1, result_1), (name_2, result_2) in combinations(comparison_target, 2):
        assert_numerical_tolerance_check(
            "purity_echo_core",
            result_1,
            name_1,
            result_2,
            name_2,
            logger,
        )
