"""
============================================================================
Test the qurry.boorust module.
============================================================================

"""
from typing import Union
import pytest

# pylint: disable=import-error, no-name-in-module
from qurry.boorust.construct import (  # type: ignore
    cycling_slice_rust, qubit_selector_rust)
from qurry.boost.randomized import cycling_slice as cycling_slice_cy
from qurry.qurrent.RandomizedMeasure import (
    cycling_slice as cycling_slice_py)
from qurry.qurrium.utils.construct import (
    qubit_selector as qubit_selector_py)
# pylint: enable=import-error, no-name-in-module


test_setup_selector: tuple[
    int,
    Union[int, tuple[int, int]],
    str
] = [
    (8, 6, "Case: int"),
    (8, (2, 8), "Case: tuple[int, int]"),
    (8, 7, "Case: int"),
    (8, (0, 7), "Case: tuple[int, int]"),
    (8, (-2, 5), "Case: tuple[-int, int]"),
    (8, (-5, -1), "Case: tuple[-int, -int]"),
    (8, (3, -2), "Case: tuple[int, -int]"),
]
test_setup_cycling: tuple[
    Union[int, tuple[int, int]],
    str
] = []


@pytest.mark.parametrize("test_items", test_setup_selector)
def test_qubit_selector(test_items: tuple[int, Union[int, tuple[int, int]], str]):
    """Test the qubit_selector function.
    """

    qubit_selector_rust_result = qubit_selector_rust(*test_items[:1])
    qubit_selector_py_result = qubit_selector_py(*test_items[:1])

    assert (
        qubit_selector_rust_result == qubit_selector_py_result
    ), (
        "Rust and Python results are not equal in" +
        f"qubit_selector at case: {test_items[2]}."
    )

    selected = qubit_selector_rust_result

    cycling_slice_cy_result = cycling_slice_cy(
        '01234567', *selected, 1)
    cycling_slice_py_result = cycling_slice_py(
        '01234567', *selected, 1)
    cycling_slice_rust_result = cycling_slice_rust(
        '01234567', *selected, 1)

    assert (
        cycling_slice_cy_result == cycling_slice_py_result
    ), (
        "Cython and Python results are not equal in" +
        f"cycling_slice at case: {test_items[1]}."
    )
    assert (
        cycling_slice_rust_result == cycling_slice_py_result
    ), (
        "Rust and Python results are not equal in" +
        f"cycling_slice at case: {test_items[1]}."
    )
    assert (
        cycling_slice_rust_result == cycling_slice_cy_result
    ), (
        "Rust and Cython results are not equal in" +
        f"cycling_slice at case: {test_items[1]}."
    )
