"""
============================================================================
Test the qurry.boorust module.
============================================================================

"""

from typing import Union
import pytest

from qurry.process.utils import (
    construct_availability,
    dummy_availability,
    test_availability,
)
from qurry.process.utils.construct import (
    qubit_selector as qubit_selector_py,
    qubit_selector_rust,
    cycling_slice as cycling_slice_py,
    cycling_slice_rust,
)
from qurry.process.utils.test import test_construct


def test_test_construct():
    """Test the test_construct function."""

    assert test_availability[1]["Rust"], (
        "Rust is not available." + f" Check the error: {test_availability[2]}"
    )
    test_construct()


def test_dummy_availability():

    assert dummy_availability[1]["Rust"], (
        "Rust is not available." + f" Check the error: {dummy_availability[2]}"
    )


test_setup_selector: list[tuple[int, Union[int, tuple[int, int]], str]] = [
    (8, 6, "Case: int"),
    (8, (2, 8), "Case: tuple[int, int]"),
    (8, 7, "Case: int"),
    (8, (0, 7), "Case: tuple[int, int]"),
    (8, (-2, 5), "Case: tuple[-int, int]"),
    (8, (-5, -1), "Case: tuple[-int, -int]"),
    (8, (3, -2), "Case: tuple[int, -int]"),
]
test_setup_cycling: list[tuple[Union[int, tuple[int, int]], str]] = []


@pytest.mark.parametrize("test_items", test_setup_selector)
def test_qubit_selector(test_items: tuple[int, Union[int, tuple[int, int]], str]):
    """Test the qubit_selector function."""

    assert construct_availability[1]["Rust"], (
        "Rust is not available." + f" Check the error: {construct_availability[2]}"
    )
    qubit_selector_py_result = qubit_selector_py(*test_items[:1])
    qubit_selector_rust_result = qubit_selector_rust(*test_items[:1])

    assert qubit_selector_rust_result == qubit_selector_py_result, (
        "Rust and Python results are not equal in"
        + f"qubit_selector at {test_items[2]}: {test_items[0]} qubits {test_items[1]}."
    )

    selected = qubit_selector_py_result

    cycling_slice_py_result = cycling_slice_py("01234567", *selected, 1)
    cycling_slice_rust_result = cycling_slice_rust("01234567", *selected, 1)

    assert cycling_slice_rust_result == cycling_slice_py_result, (
        "Rust and Python results are not equal in"
        + f"cycling_slice at {test_items[2]}: {test_items[0]} qubits {test_items[1]}."
    )
