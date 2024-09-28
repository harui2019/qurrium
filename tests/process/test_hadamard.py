"""
================================================================
Test - qurry.process.hadamard_test
================================================================

"""

from typing import TypedDict, Union
import pytest
import numpy as np

from qurry.process.hadamard_test.purity_echo_core import purity_echo_core


class HadamardTest(TypedDict):
    """Input type for the purity_echo_core function."""

    shots: int
    counts: list[dict[str, int]]


class TestItemHadamardTest(TypedDict):
    """Test item for the purity_echo_core function."""

    target: HadamardTest
    answer: Union[float, int]


test_setup_hadamard: list[TestItemHadamardTest] = [
    {"target": {"shots": 100, "counts": [{"0": 50, "1": 50}]}, "answer": 0},
    {"target": {"shots": 100, "counts": [{"0": 100}]}, "answer": 1},
    {"target": {"shots": 100, "counts": [{"1": 100}]}, "answer": 1},
]


@pytest.mark.parametrize("test_input", test_setup_hadamard)
def test_hadamard(test_input: TestItemHadamardTest):
    """Test the purity_echo_core function."""

    purity_echo_rust_result = purity_echo_core(**test_input["target"], backend="Rust")
    purity_echo_py_result = purity_echo_core(**test_input["target"], backend="Python")

    assert (
        np.abs(purity_echo_rust_result - purity_echo_py_result) < 1e-10
    ), "Rust and Python results are not equal in purity_echo_core."
    assert np.abs(purity_echo_rust_result - test_input["answer"]) < 1e-10, (
        "The result of purity_echo_core is not correct,"
        + f"purity_echo_rust_result: {purity_echo_rust_result} "
        + f"!= test_input['answer']: {test_input['answer']}"
    )
