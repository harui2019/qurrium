"""
================================================================
Test the qurry.boorust module.
================================================================

"""

import pytest
import numpy as np

from qurry.process.hadamard_test.purity_echo_core import purity_echo_core


test_setup_hadamard = [
    {"shots": 100, "counts": [{"0": 50, "1": 50}]},
    {"shots": 100, "counts": [{"0": 100}]},
    {"shots": 100, "counts": [{"1": 100}]},
]


@pytest.mark.parametrize("test_items", test_setup_hadamard)
def test_hadamard(test_items):
    """Test the purity_echo_core function."""

    purity_echo_rust_result = purity_echo_core(**test_items, backend="Rust")
    purity_echo_py_result = purity_echo_core(**test_items, backend="Python")

    assert (
        np.abs(purity_echo_rust_result - purity_echo_py_result) < 1e-10
    ), "Rust and Python results are not equal in purity_echo_core."
