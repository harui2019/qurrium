"""
================================================================
Test the qurry.boorust module.
================================================================

"""
from typing import Union
import os
import warnings
import pytest
import numpy as np

from qurry.capsule import quickRead
from qurry.exceptions import QurryRustUnavailableWarning

# pylint: disable=import-error, no-name-in-module
# from qurry.boorust.randomized import (  # type: ignore
#     ensemble_cell_rust,
#     entangled_entropy_core_rust,
# )

# from qurry.boost.randomized import ensembleCell as ensemble_cell_cy
# from qurry.qurrent.RandomizedMeasure import (
#     _entangled_entropy_core as entangled_entropy_core,
# )
# from qurry.qurrium.utils.randomized import ensemble_cell as ensemble_cell_py

# pylint: enable=import-error, no-name-in-module

from qurry.qurrium.utils.randomized import (
    RUST_AVAILABLE as rust_available_randomized,
    ensemble_cell as ensemble_cell_py,
    ensemble_cell_cy,
)

if rust_available_randomized:
    from qurry.qurrium.utils.randomized import ensemble_cell_rust
else:

    def ensemble_cell_rust(*args, **kwargs):
        """Dummy function."""
        warnings.warn(
            "Rust is not available, ensemble_cell_rust is a dummy function.",
            category=QurryRustUnavailableWarning,
        )
        return ensemble_cell_py(*args, **kwargs)


from qurry.qurrent.postprocess import entangled_entropy_core

test_setup_ensemble = [
    ("1010101010101010", 100, "0101010101010101", 100, 12, 100),
    ("1010101010101010", 100, "1010101010101010", 100, 12, 100),
]


@pytest.mark.parametrize("test_items", test_setup_ensemble)
def test_ensemble_cell_rust(test_items):
    """Test the ensemble_cell_rust function."""

    ensemble_cell_rust_result = ensemble_cell_rust(*test_items)
    ensemble_cell_cy_result = ensemble_cell_cy(*test_items)
    ensemble_cell_py_result = ensemble_cell_py(*test_items)

    if rust_available_randomized:
        assert (
            np.abs(ensemble_cell_rust_result - ensemble_cell_cy_result) < 1e-10
        ), "Rust and Cython results are not equal in ensemble_cell."
        assert (
            np.abs(ensemble_cell_rust_result - ensemble_cell_py_result) < 1e-10
        ), "Rust and Python results are not equal in ensemble_cell."
    assert (
        np.abs(ensemble_cell_cy_result - ensemble_cell_py_result) < 1e-10
    ), "Cython and Python results are not equal in ensemble_cell."


FILE_LOCATION = os.path.join(os.path.dirname(__file__), "easy-dummy.json")


easy_dummy: dict[str, dict[str, int]] = quickRead(FILE_LOCATION)
large_dummy_list = [easy_dummy["0"] for i in range(100)]
test_setup_core: tuple[
    int, list[dict[str, int]], Union[int, tuple[int, int]], tuple[int, int]
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
    test_items: tuple[
        int, list[dict[str, int]], Union[int, tuple[int, int]], tuple[int, int]
    ]
):
    """Test the entangled_entropy_core function."""

    # rust = entangled_entropy_core_rust(*test_items)
    # cy = entangled_entropy_core(*test_items)
    # py = entangled_entropy_core(*test_items, use_cython=False)
    rust = entangled_entropy_core(*test_items, backend="Rust")
    cy = entangled_entropy_core(*test_items, backend="Cython")
    py = entangled_entropy_core(*test_items, backend="Python")

    if rust_available_randomized:
        assert (
            np.abs(
                np.average(list(rust[0].values())) - np.average(list(cy[0].values()))
            )
            < 1e-10
        ), "Rust and Cython results are not equal in entangled_entropy_core."

        assert (
            np.abs(
                np.average(list(rust[0].values())) - np.average(list(py[0].values()))
            )
            < 1e-10
        ), "Rust and Python results are not equal in entangled_entropy_core."

    assert (
        np.abs(np.average(list(cy[0].values())) - np.average(list(py[0].values())))
        < 1e-10
    ), "Cython and Python results are not equal in entangled_entropy_core."
