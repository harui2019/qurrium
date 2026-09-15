"""Test qurry.process.randomized_measure module."""

from typing import TypedDict, Any
from itertools import combinations
import pytest
import logging
import numpy as np

from qurry.process.utils import cycling_slice, randomized_availability
from qurry.process.randomized_measure.entangled_entropy_v1.entangled_entropy import (
    entangled_entropy_core,
)
from qurry.process.randomized_measure.entangled_entropy.entangled_entropy_2 import (
    entangled_entropy_core_2,
)
from qurry.process.randomized_measure.wavefunction_overlap_v1.wavefunction_overlap import (
    overlap_echo_core,
)
from qurry.process.randomized_measure.wavefunction_overlap.wavefunction_overlap_2 import (
    overlap_echo_core_2,
)
from qurry.process.randomized_measure import (
    entangled_availability,
    entangled_v1_availability,
    overlap_availability,
    overlap_v1_availability,
)

from .utilities import (
    quick_json_read,
    get_dummy_file_path,
    assert_numerical_tolerance_check,
    assert_and_logging_rust_available,
)

logger = logging.getLogger(__name__)


class RandomizedMeasureTarget(TypedDict):
    """TypedDict for randomized measurement answer from JSON."""

    shots: int
    """Number of shots."""
    selected_range: int | tuple[int, int] | None
    """The selected classical registers range or a single integer."""
    absolute_range: tuple[int, int]
    """The absolute range of classical registers."""


class RandomizedMeasureCase(TypedDict):
    """The raw read randomized measurement unit type."""

    target: RandomizedMeasureTarget
    """The target parameters for the randomized_measure function."""
    easy_dummy_usage: list[int]
    """The usage indexes of the easy dummy."""


EASY_DUMMY_PATH = get_dummy_file_path("easy_dummy.json")
easy_dummy_raw: dict[str, dict[str, int]] = quick_json_read(EASY_DUMMY_PATH)
easy_dummy: dict[int, dict[str, int]] = {int(k): v for k, v in easy_dummy_raw.items()}


def process_json_read(raw_read_item: dict[str, Any]) -> RandomizedMeasureCase:
    """Process the raw read item from JSON to RandomizedMeasureCase.

    Args:
        raw_read_item (dict[str, Any]): The raw read item from JSON.

    Returns:
        RandomizedMeasureCase: The processed RandomizedMeasureCase.
    """
    return {
        "target": {
            "shots": raw_read_item["target"]["shots"],
            "selected_range": tuple(raw_read_item["target"]["selected_range"])
            if isinstance(raw_read_item["target"]["selected_range"], list)
            else raw_read_item["target"]["selected_range"],
            "absolute_range": tuple(raw_read_item["target"]["absolute_range"]),
        },
        "easy_dummy_usage": raw_read_item["easy_dummy_usage"],
    }


DUMMY_CASE_FILE = get_dummy_file_path("randomized.json")
DUMMY_CASES_JSON = [process_json_read(case) for case in quick_json_read(DUMMY_CASE_FILE)]
randomized_cases_entries = [
    (case["target"], [easy_dummy[idx] for idx in case["easy_dummy_usage"]])
    for case in DUMMY_CASES_JSON
]


def selected_and_cycling_selected_making(
    absolute_range: tuple[int, int],
    selected_range: int | tuple[int, int] | None,
) -> tuple[list[int], list[int]]:
    """Make selected classical registers based on the range
    and selected classical registers by cycling.

    Args:
        absolute_range (tuple[int, int]):
            The absolute range of classical registers, where the first element is the start
            and the second element is the end (exclusive).
        selected_range (int | tuple[int, int] | None):
            The selected classical registers range or a single integer.
            If None, all registers in the absolute range are selected.
            If an integer, it selects that many registers from the end of the absolute range.
            If a tuple, it selects registers in the specified range.

    Returns:
        tuple[list[int], list[int]]:
            A tuple containing two lists:

            - The first list contains the selected classical registers.
            - The second list contains the selected classical registers by cycling.
    """
    return sorted(
        list(range(*absolute_range))
        if selected_range is None
        else (
            [
                absolute_range[1] - i % absolute_range[1] - 1
                for i in range(
                    *(
                        selected_range
                        if selected_range[0] < selected_range[1]
                        else tuple(ci % absolute_range[1] for ci in selected_range)
                    )
                )
            ]
            if isinstance(selected_range, tuple)
            else list(range(selected_range))
        )
    ), sorted(
        list(range(absolute_range[1] - 1, absolute_range[0] - 1, -1))
        if selected_range is None
        else (
            cycling_slice(
                list(range(absolute_range[1] - 1, absolute_range[0] - 1, -1)),
                selected_range[0],
                selected_range[1],
            )
            if isinstance(selected_range, tuple)
            else list(range(selected_range))
        )
    )


def v1_ranging_info(partition_range: tuple[int, int], measuring_range: tuple[int, int]) -> str:
    """Get the ranging info string for v1 functions.

    Args:
        partition_range (tuple[int, int]): The partition range.
        measuring_range (tuple[int, int]): The measuring range.

    Returns:
        str: The ranging info string.
    """
    return f"partition range: {partition_range}, measuring range: {measuring_range}"


def v2_ranging_info(selected_classical_registers: list[int]) -> str:
    """Get the ranging info string for v2 functions.

    Args:
        selected_classical_registers (list[int]): The selected classical registers.

    Returns:
        str: The ranging info string.
    """
    return f"selected classical registers: {selected_classical_registers}"


def averaging_cells(cells: dict[int, float] | dict[int, np.float64]) -> np.float64:
    """Get the average value of the cells.

    Args:
        cells (dict[int, float] | dict[int, np.float64]): The cells dictionary.
    Returns:
        np.float64: The average value of the cells.
    """
    return np.average(np.array(list(cells.values())))


def test_availability():
    """Test the availability of the Rust backend for the entangled_entropy_core function."""

    assert_and_logging_rust_available(
        [
            randomized_availability,
            entangled_availability,
            entangled_v1_availability,
            overlap_availability,
            overlap_v1_availability,
        ],
        logger,
    )


@pytest.mark.parametrize(["target", "counts"], randomized_cases_entries)
def test_entangled_entropy_core(target: RandomizedMeasureTarget, counts: list[dict[str, int]]):
    """Test the entangled_entropy_core function."""

    selected_classical_registers, cycling_selected = selected_and_cycling_selected_making(
        target["absolute_range"], target["selected_range"]
    )

    comparison_target: list[tuple[str, np.float64, str]] = []

    py_1_tmp = entangled_entropy_core(
        target["shots"],
        counts,
        target["selected_range"],
        target["absolute_range"],
        backend="Python",
    )
    comparison_target.append(
        ("Python V1", averaging_cells(py_1_tmp[0]), v1_ranging_info(py_1_tmp[1], py_1_tmp[2]))
    )

    py_2_tmp = entangled_entropy_core_2(
        target["shots"], counts, selected_classical_registers, backend="Python"
    )
    comparison_target.append(("Python", averaging_cells(py_2_tmp[0]), v2_ranging_info(py_2_tmp[1])))

    rust_1_tmp = entangled_entropy_core(
        target["shots"],
        counts,
        target["selected_range"],
        target["absolute_range"],
        backend="Rust",
    )
    comparison_target.append(
        ("Rust V1", averaging_cells(rust_1_tmp[0]), v1_ranging_info(rust_1_tmp[1], rust_1_tmp[2]))
    )

    rust_2_tmp = entangled_entropy_core_2(
        target["shots"], counts, selected_classical_registers, backend="Rust"
    )
    comparison_target.append(
        ("Rust", averaging_cells(rust_2_tmp[0]), v2_ranging_info(rust_2_tmp[1]))
    )

    for (title_01, result_01, info_01), (title_02, result_02, info_02) in combinations(
        comparison_target, 2
    ):
        assert_numerical_tolerance_check(
            "entangled_entropy_core",
            result_01,
            title_01,
            result_02,
            title_02,
            logger,
        )

    if selected_classical_registers != cycling_selected:
        msg = (
            "FAIL - entangled_entropy_core - "
            + f"selected_classical_registers: {selected_classical_registers} != "
            + f"selected_classical_registers_by_cycling: {cycling_selected}"
        )
        logger.error(msg)
    else:
        msg = (
            "PASS - entangled_entropy_core - "
            + f"selected_classical_registers: {selected_classical_registers} == "
            + f"selected_classical_registers_by_cycling: {cycling_selected}"
        )
        logger.info(msg)
    assert selected_classical_registers == cycling_selected, msg


@pytest.mark.parametrize(["target", "counts"], randomized_cases_entries)
def test_overlap_echo_core(target: RandomizedMeasureTarget, counts: list[dict[str, int]]):
    """Test the overlap_echo_core function."""

    selected_classical_registers, cycling_selected = selected_and_cycling_selected_making(
        target["absolute_range"], target["selected_range"]
    )

    comparison_target: list[tuple[str, np.float64, str]] = []

    py_1_tmp = overlap_echo_core(
        target["shots"],
        counts,
        target["selected_range"],
        target["absolute_range"],
        backend="Python",
    )
    comparison_target.append(
        ("Python V1", averaging_cells(py_1_tmp[0]), v1_ranging_info(py_1_tmp[1], py_1_tmp[2]))
    )

    py_2_tmp = overlap_echo_core_2(
        target["shots"], counts, counts, selected_classical_registers, backend="Python"
    )
    comparison_target.append(("Python", averaging_cells(py_2_tmp[0]), v2_ranging_info(py_2_tmp[1])))

    rust_1_tmp = overlap_echo_core(
        target["shots"],
        counts,
        target["selected_range"],
        target["absolute_range"],
        backend="Rust",
    )
    comparison_target.append(
        ("Rust V1", averaging_cells(rust_1_tmp[0]), v1_ranging_info(rust_1_tmp[1], rust_1_tmp[2]))
    )

    rust_2_tmp = overlap_echo_core_2(
        target["shots"], counts, counts, selected_classical_registers, backend="Rust"
    )
    comparison_target.append(
        ("Rust", averaging_cells(rust_2_tmp[0]), v2_ranging_info(rust_2_tmp[1]))
    )

    for (title_01, result_01, info_01), (title_02, result_02, info_02) in combinations(
        comparison_target, 2
    ):
        assert_numerical_tolerance_check(
            "overlap_echo_core",
            result_01,
            title_01,
            result_02,
            title_02,
            logger,
        )

    if selected_classical_registers != cycling_selected:
        msg = (
            "FAIL - overlap_echo_core - "
            + f"selected_classical_registers: {selected_classical_registers} != "
            + f"selected_classical_registers_by_cycling: {cycling_selected}"
        )
        logger.error(msg)
    else:
        msg = (
            "PASS - overlap_echo_core - "
            + f"selected_classical_registers: {selected_classical_registers} == "
            + f"selected_classical_registers_by_cycling: {cycling_selected}"
        )
        logger.info(msg)
    assert selected_classical_registers == cycling_selected, msg
