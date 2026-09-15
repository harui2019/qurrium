"""Test qurry.process.magnet_square module."""

from typing import TypedDict, Literal
from itertools import combinations
import logging
import pytest

from qurry.process.magnet_square import (
    magnet_square_availability,
    magnetization_square,
    z_dir_magnetization_square,
    MagnetSquareResult,
)

from .utilities import (
    quick_json_read,
    get_dummy_file_path,
    assert_numerical_tolerance_check,
    FloatType,
    assert_and_logging_rust_available,
)

logger = logging.getLogger(__name__)


class MagnetSquareZdirTarget(TypedDict):
    """TypedDict for magnet square answer from JSON."""

    shots: int
    """Number of shots."""
    counts: list[dict[str, int]]
    """The counts dictionary list."""
    num_qubits: int
    """Number of qubits."""


class MagnetSquareTarget(MagnetSquareZdirTarget):
    """TypedDict for magnet square answer from JSON."""

    unitary_operator: Literal["x", "y", "z"] | str
    """The unitary operator used."""


class MagnetSquareZdirCase(TypedDict):
    """The raw read magnet square z direction unit type."""

    target: MagnetSquareZdirTarget
    """The target parameters for the z_dir_magnetization_square function."""
    answer: MagnetSquareResult
    """The expected answer from the z_dir_magnetization_square function."""
    case_name: str
    """The case name."""


class MagnetSquareCase(TypedDict):
    """The raw read magnet square unit type."""

    target: MagnetSquareTarget
    """The target parameters for the magnet_square function."""
    answer: MagnetSquareResult
    """The expected answer from the magnet_square function."""
    case_name: str
    """The case name."""


ANSWERS = {
    "cat_2": 1,
    "cat_4": 1,
    "cat_6": 1,
    "cat_8": 1,
    "trivialPM_2": 1 / 2,
    "trivialPM_4": 1 / 4,
    "trivialPM_6": 1 / 6,
    "trivialPM_8": 1 / 8,
}

ANSWERS_ERROR = 0.05


DUMMY_CASE_FILE_MSZDIR = get_dummy_file_path("magnet_square_zdir.json")
DUMMY_CASES_JSON_MSZDIR: list[MagnetSquareZdirCase] = quick_json_read(DUMMY_CASE_FILE_MSZDIR)
mszdir_cases_entries = [
    (case["target"], case["answer"], case["case_name"]) for case in DUMMY_CASES_JSON_MSZDIR
]


DUMMY_CASE_FILE_MS = get_dummy_file_path("magnet_square.json")
DUMMY_CASES_JSON_MS: list[MagnetSquareCase] = quick_json_read(DUMMY_CASE_FILE_MS)
ms_cases_entries = [
    (case["target"], case["answer"], case["case_name"]) for case in DUMMY_CASES_JSON_MS
]


def test_availability():
    """Test the availability of the Rust backend for the magnet_square function."""

    assert_and_logging_rust_available([magnet_square_availability], logger)


@pytest.mark.parametrize(["target", "answer", "case_name"], mszdir_cases_entries)
def test_magnet_square_zdir(
    target: MagnetSquareZdirTarget, answer: MagnetSquareResult, case_name: str
):
    """Test the z_dir_magnetic_square_core function."""

    assert len(target["counts"]) == 1, (
        "The counts should be a single item for the z_dir_magnetic_square_core function."
    )

    py_result = z_dir_magnetization_square(
        shots=target["shots"],
        single_counts=target["counts"][0],
        num_qubits=target["num_qubits"],
        backend="Python",
    )
    rust_result = z_dir_magnetization_square(
        shots=target["shots"],
        single_counts=target["counts"][0],
        num_qubits=target["num_qubits"],
        backend="Rust",
    )

    comparison_target: list[tuple[str, FloatType]] = [
        ("Python", py_result["magnet_square"]),
        ("Rust", rust_result["magnet_square"]),
        ("Numerical Answer", answer["magnet_square"]),
    ]
    for (name_1, result_1), (name_2, result_2) in combinations(comparison_target, 2):
        assert_numerical_tolerance_check(
            "z_dir_magnetization_square",
            result_1,
            name_1,
            result_2,
            name_2,
            logger,
        )
    for name_1, result_1 in comparison_target:
        assert_numerical_tolerance_check(
            "z_dir_magnetization_square",
            result_1,
            name_1,
            ANSWERS[case_name],
            "Answer",
            logger,
            ANSWERS_ERROR,
        )


@pytest.mark.parametrize(["target", "answer", "case_name"], ms_cases_entries)
def test_magnet_square(target: MagnetSquareTarget, answer: MagnetSquareResult, case_name: str):
    """Test the z_dir_magnetic_square_core function."""

    predict_counts_num = target["num_qubits"] * (target["num_qubits"] - 1)
    assert len(target["counts"]) == predict_counts_num, (
        f"The counts should have {predict_counts_num} items, "
        + f"but got {len(target['counts'])} for {case_name}"
    )

    py_result = magnetization_square(
        shots=target["shots"],
        counts=target["counts"],
        num_qubits=target["num_qubits"],
        backend="Python",
    )
    rust_result = magnetization_square(
        shots=target["shots"],
        counts=target["counts"],
        num_qubits=target["num_qubits"],
        backend="Rust",
    )

    comparison_target: list[tuple[str, FloatType]] = [
        ("Python", py_result["magnet_square"]),
        ("Rust", rust_result["magnet_square"]),
        ("Known numerical answer", answer["magnet_square"]),
    ]
    for (name_1, result_1), (name_2, result_2) in combinations(comparison_target, 2):
        assert_numerical_tolerance_check(
            "magnet_square",
            result_1,
            name_1,
            result_2,
            name_2,
            logger,
        )
    for name_1, result_1 in comparison_target:
        assert_numerical_tolerance_check(
            "magnet_square",
            result_1,
            name_1,
            ANSWERS[case_name],
            "Answer",
            logger,
            ANSWERS_ERROR,
        )
