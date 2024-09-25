"""
================================================================
Test the qurry.boorust module.
================================================================

"""

from typing import Union
import os
import pytest
import numpy as np

from qurry.capsule import quickRead
from qurry.process.randomized_measure.entangled_entropy import entangled_entropy_core
from qurry.process.randomized_measure.wavefunction_overlap import overlap_echo_core
from qurry.process.utils.randomized import (
    RUST_AVAILABLE as rust_available_randomized,
    CYTHON_AVAILABLE as cython_available_randomized,
)


FILE_LOCATION = os.path.join(os.path.dirname(__file__), "easy-dummy.json")


easy_dummy: dict[str, dict[str, int]] = quickRead(FILE_LOCATION)
large_dummy_list = [easy_dummy["0"] for i in range(100)]
test_setup_core: list[
    tuple[int, list[dict[str, int]], Union[int, tuple[int, int]], tuple[int, int]]
] = [
    (4096, large_dummy_list, 6, (0, 8)),
    (4096, large_dummy_list, (2, 8), (0, 8)),
    (4096, large_dummy_list, 7, (0, 8)),
    (4096, large_dummy_list, (0, 7), (0, 8)),
    (4096, large_dummy_list, (-2, 5), (0, 8)),
    (4096, large_dummy_list, (-5, -1), (0, 8)),
    (4096, large_dummy_list, (3, -2), (0, 8)),
]


@pytest.mark.parametrize("test_items", test_setup_core)
def test_entangled_entropy_core(
    test_items: tuple[int, list[dict[str, int]], Union[int, tuple[int, int]], tuple[int, int]]
):
    """Test the entangled_entropy_core function."""

    assert cython_available_randomized, "Cython is not available."
    assert rust_available_randomized, "Rust is not available."
    cy = entangled_entropy_core(*test_items, backend="Cython")
    py = entangled_entropy_core(*test_items, backend="Python")
    rust = entangled_entropy_core(*test_items, backend="Rust")

    assert (
        np.abs(
            np.average(np.array(list(rust[0].values())))
            - np.average(np.array(list(cy[0].values())))
        )
        < 1e-10
    ), "Rust and Cython results are not equal in entangled_entropy_core."

    assert (
        np.abs(
            np.average(np.array(list(rust[0].values())))
            - np.average(np.array(list(py[0].values())))
        )
        < 1e-10
    ), "Rust and Python results are not equal in entangled_entropy_core."

    assert (
        np.abs(
            np.average(np.array(list(cy[0].values()))) - np.average(np.array(list(py[0].values())))
        )
        < 1e-10
    ), "Cython and Python results are not equal in entangled_entropy_core."


@pytest.mark.parametrize("test_items", test_setup_core)
def test_overlap_echo_core(
    test_items: tuple[int, list[dict[str, int]], Union[int, tuple[int, int]], tuple[int, int]]
):
    """Test the overlap_echo_core function."""

    assert cython_available_randomized, "Cython is not available."
    assert rust_available_randomized, "Rust is not available."
    cy = overlap_echo_core(*test_items, backend="Cython")
    py = overlap_echo_core(*test_items, backend="Python")
    rust = overlap_echo_core(*test_items, backend="Rust")

    assert (
        np.abs(
            np.average(np.array(list(rust[0].values())))
            - np.average(np.array(list(cy[0].values())))
        )
        < 1e-10
    ), "Rust and Cython results are not equal in overlap_echo_core."

    assert (
        np.abs(
            np.average(np.array(list(rust[0].values())))
            - np.average(np.array(list(py[0].values())))
        )
        < 1e-10
    ), "Rust and Python results are not equal in overlap_echo_core."

    assert (
        np.abs(
            np.average(np.array(list(cy[0].values()))) - np.average(np.array(list(py[0].values())))
        )
        < 1e-10
    ), "Cython and Python results are not equal in overlap_echo_core."
