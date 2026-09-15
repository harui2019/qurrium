"""Test the qurry.boorust module."""

import logging
import pytest

from qurry.process.utils import (
    counts_process_availability,
    bit_slice_availability,
    dummy_availability,
)
from qurry.process.utils.bit_slice import (
    qubit_selector as qubit_selector_py,
    qubit_selector_rust,
    cycling_slice as cycling_slice_py,
    cycling_slice_rust,
)

from .utilities import assert_and_logging_rust_available

logger = logging.getLogger(__name__)


def test_availability():
    """Test the availability of the Rust backend for the entangled_entropy_core function."""

    assert_and_logging_rust_available(
        [
            counts_process_availability,
            bit_slice_availability,
            dummy_availability,
        ],
        logger,
    )


cases_entries: list[tuple[str, int | tuple[int, int] | None]] = [
    ("01234567", 6),
    ("01234567", (2, 8)),
    ("01234567", 7),
    ("01234567", (0, 7)),
    ("01234567", (-2, 5)),
    ("01234567", (-5, -1)),
    ("01234567", (3, -2)),
    ("01234567", None),
]


@pytest.mark.parametrize(["dummy_string", "degree"], cases_entries)
def test_qubit_selector(dummy_string: str, degree: int | tuple[int, int] | None):
    """Test the qubit_selector function."""

    if isinstance(degree, tuple):
        if len(degree) != 2:
            raise ValueError("Degree tuple must have exactly two elements.")
        case_desc = (
            "tuple["
            + ("-" if degree[0] < 0 else "")
            + "int, "
            + ("-" if degree[1] < 0 else "")
            + "int]"
        )
    elif isinstance(degree, int):
        case_desc = "int"
    elif degree is None:
        case_desc = "None"
    else:
        raise ValueError("Degree must be an int, tuple of two ints, or None.")

    selected_by_py = qubit_selector_py(len(dummy_string), degree)
    selected_by_rust = qubit_selector_rust(len(dummy_string), degree)

    if selected_by_rust == selected_by_py:
        msg_1 = (
            "PASS - qubit_selector - Rust and Python results are equal "
            + f"with string '{dummy_string}' and degree {degree} "
            + f"by selection input of {case_desc}."
        )
        logger.info(msg_1)
    else:
        msg_1 = (
            "FAIL - qubit_selector - Rust and Python results are not equal "
            + f"with string '{dummy_string}' and degree {degree} "
            + f"by selection input of {case_desc}."
        )
        logger.error(msg_1)
    assert selected_by_rust == selected_by_py, msg_1

    cycling_slice_py_result = cycling_slice_py(dummy_string, *selected_by_py, 1)
    cycling_slice_rust_result = cycling_slice_rust(dummy_string, *selected_by_rust, 1)

    if cycling_slice_rust_result == cycling_slice_py_result:
        msg_2 = (
            "PASS - cycling_slice - Rust and Python results are equal in "
            + f"with string '{dummy_string}' and degree {degree} "
            + f"by selection input of {case_desc}."
        )
        logger.info(msg_2)
    else:
        msg_2 = (
            "FAIL - cycling_slice - Rust and Python results are not equal in "
            + f"with string '{dummy_string}' and degree {degree} "
            + f"by selection input of {case_desc}."
        )
        logger.error(msg_2)

    assert cycling_slice_rust_result == cycling_slice_py_result, msg_2
