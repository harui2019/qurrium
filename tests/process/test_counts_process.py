"""Tests qurry.process.utils.construct module."""

import logging
import pytest

from qurry.process.utils import counts_process_availability
from qurry.process.utils.counts_process import (
    single_counts_recount_pyrust,
    counts_list_recount_pyrust,
    counts_list_vectorize_pyrust,
    counts_list_vectorize_rust,
    rho_m_flatten_counts_list_vectorize_pyrust,
    rho_m_flatten_counts_list_vectorize_rust,
)

from .utilities import quick_json_read, get_dummy_file_path, assert_and_logging_rust_available

logger = logging.getLogger(__name__)

EASY_DUMMY_PATH = get_dummy_file_path("easy_dummy.json")
easy_dummy_raw: dict[str, dict[str, int]] = quick_json_read(EASY_DUMMY_PATH)
easy_dummy: dict[int, dict[str, int]] = {int(k): v for k, v in easy_dummy_raw.items()}


case_entries: list[list[int]] = (
    [[i] for i in range(8)]
    + [[i, i + 1] for i in range(7)]
    + [[1, 2, 3, 4], [2, 3, 4, 5], [3, 4, 5, 6], [4, 5, 6, 7]]
)


def test_availability():
    """Test the availability of the Rust backend for the counts_recount function."""

    assert_and_logging_rust_available([counts_process_availability], logger)


@pytest.mark.parametrize("test_items", case_entries)
def test_counts_substring(test_items: list[int]):
    """Test the ensemble_cell_rust function."""

    counts_recounted_py_result = single_counts_recount_pyrust(
        easy_dummy[0], 8, test_items, backend="Python"
    )
    counts_recounted_rust_result = single_counts_recount_pyrust(
        easy_dummy[0], 8, test_items, backend="Rust"
    )

    is_count_recount_equal = all(
        counts_recounted_rust_result[s] == v for s, v in counts_recounted_py_result.items()
    )
    if is_count_recount_equal:
        msg_1 = (
            "PASS - counts_recount - Rust and Python results are equal in "
            + f"counts_recount with test_items: {test_items}."
        )
        logger.info(msg_1)
    else:
        msg_1 = (
            "FAIL - counts_recount - Rust and Python results are not equal in "
            + f"counts_recount with test_items: {test_items}, "
            + f"counts_recount_rust_result: {counts_recounted_rust_result}, "
            + f"counts_recount_py_result: {counts_recounted_py_result}."
        )
        logger.error(msg_1)
    assert is_count_recount_equal, msg_1

    counts_list_recounted_py_result = counts_list_recount_pyrust(
        [easy_dummy[0]], 8, test_items, backend="Python"
    )
    counts_list_recounted_rust_result = counts_list_recount_pyrust(
        [easy_dummy[0]], 8, test_items, backend="Rust"
    )

    is_count_list_recount_equal = all(
        counts_list_recounted_rust_result[0][s] == v
        for s, v in counts_list_recounted_py_result[0].items()
    )
    if is_count_list_recount_equal:
        msg_2 = (
            "PASS - counts_list_recount - Rust and Python results are equal in "
            + f"counts_list_recount with test_items: {test_items}."
        )
        logger.info(msg_2)
    else:
        msg_2 = (
            "FAIL - counts_list_recount - Rust and Python results are not equal in "
            + f"counts_list_recount with test_items: {test_items}, "
            + f"counts_list_recount_rust_result: {counts_list_recounted_rust_result}, "
            + f"counts_list_recount_py_result: {counts_list_recounted_py_result}."
        )
        logger.error(msg_2)
    assert is_count_list_recount_equal, msg_2


def test_counts_list_vectorize():
    """Test the counts_list_vectorize function."""

    origin_counts_list = [easy_dummy[0]]
    counts_list_vectorize_py_result = counts_list_vectorize_pyrust(
        origin_counts_list, backend="Python"
    )
    counts_list_vectorize_rust_result = counts_list_vectorize_rust(origin_counts_list)

    for idx, ((bit_array, value_array), single_counts) in enumerate(
        zip(counts_list_vectorize_py_result, origin_counts_list)
    ):
        tmp = []
        for bit, v in zip(bit_array, value_array):
            bitstring_recover = "".join([str(b) for b in bit])
            if v != single_counts[bitstring_recover]:
                tmp.append((bitstring_recover, v, single_counts[bitstring_recover]))

        if tmp:
            msg = f"FAIL - counts_list_vectorize - Python is not equal at index {idx}: {tmp}"
            logger.error(msg)
        else:
            msg = f"PASS - counts_list_vectorize - Python results are equal at index {idx}."
            logger.info(msg)
        assert not tmp, msg

    for idx, ((bit_array, value_array), single_counts) in enumerate(
        zip(counts_list_vectorize_rust_result, origin_counts_list)
    ):
        tmp = []
        for bit, v in zip(bit_array, value_array):
            bitstring_recover = "".join([str(b) for b in bit])
            if v != single_counts[bitstring_recover]:
                tmp.append((bitstring_recover, v, single_counts[bitstring_recover]))

        if tmp:
            msg = f"FAIL - counts_list_vectorize - Rust is not equal at index {idx}: {tmp}"
            logger.error(msg)
        else:
            msg = f"PASS - counts_list_vectorize - Rust results are equal at index {idx}."
            logger.info(msg)
        assert not tmp, msg


def test_rho_m_flatten_counts_list_vectorize():
    """Test the rho_m_flatten_counts_list_vectorize function."""

    origin_counts_list = [easy_dummy[0]]
    rho_m_flatten_counts_list_vectorize_py_result = rho_m_flatten_counts_list_vectorize_pyrust(
        origin_counts_list, [[0] * 8], list(range(8)), backend="Python"
    )
    rho_m_flatten_counts_list_vectorize_rust_result = rho_m_flatten_counts_list_vectorize_rust(
        origin_counts_list, [[0] * 8], list(range(8))
    )

    for idx, ((bit_array, value_array), single_counts) in enumerate(
        zip(rho_m_flatten_counts_list_vectorize_py_result, origin_counts_list)
    ):
        tmp = []
        for bit, v in zip(bit_array, value_array):
            bitstring_recover = "".join([str(b) for b in bit])
            if v != single_counts[bitstring_recover]:
                tmp.append((bitstring_recover, v, single_counts[bitstring_recover]))

        if tmp:
            msg = (
                "FAIL - rho_m_flatten_counts_list_vectorize "
                + f"- Python is not equal at index {idx}: {tmp}"
            )
            logger.error(msg)
        else:
            msg = (
                "PASS - rho_m_flatten_counts_list_vectorize "
                + f"- Python results are equal at index {idx}."
            )
            logger.info(msg)
        assert not tmp, msg

    for idx, ((bit_array, value_array), single_counts) in enumerate(
        zip(rho_m_flatten_counts_list_vectorize_rust_result, origin_counts_list)
    ):
        tmp = []
        for bit, v in zip(bit_array, value_array):
            bitstring_recover = "".join([str(b) for b in bit])
            if v != single_counts[bitstring_recover]:
                tmp.append((bitstring_recover, v, single_counts[bitstring_recover]))

        if tmp:
            msg = (
                "FAIL - rho_m_flatten_counts_list_vectorize "
                + f"- Rust is not equal at index {idx}: {tmp}"
            )
            logger.error(msg)
        else:
            msg = (
                "PASS - rho_m_flatten_counts_list_vectorize "
                + f"- Rust results are equal at index {idx}."
            )
            logger.info(msg)
        assert not tmp, msg
