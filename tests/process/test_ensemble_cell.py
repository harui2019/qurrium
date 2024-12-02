"""
================================================================
Tests - qurry.process.utils.randomized
================================================================

"""

from typing import TypedDict, Union
import warnings
import pytest
import numpy as np

from qurry.process.exceptions import PostProcessingRustUnavailableWarning
from qurry.process.utils.randomized import (
    RUST_AVAILABLE as rust_available_randomized,
    ensemble_cell as ensemble_cell_py,
)

if rust_available_randomized:
    from qurry.process.utils.randomized import ensemble_cell_rust
else:

    def ensemble_cell_rust(
        s_i: str, s_i_meas: int, s_j: str, s_j_meas: int, a_num: int, shots: int
    ) -> Union[float, np.float64]:
        """Dummy function."""
        warnings.warn(
            "Rust is not available, ensemble_cell_rust is a dummy function.",
            category=PostProcessingRustUnavailableWarning,
        )
        return ensemble_cell_py(s_i, s_i_meas, s_j, s_j_meas, a_num, shots)


class TargetItemEnsembleCell(TypedDict):
    """Test item for the purity_echo_core function."""

    target: tuple[str, int, str, int, int, int]
    answer: Union[float, int]


test_setup_ensemble: list[TargetItemEnsembleCell] = [
    {
        "target": ("10010101", 421, "10010101", 421, 8, 4096),
        "answer": (np.float64(421) ** 2) / np.float_power(2, 16, dtype=np.float64),
    },
    # (2**8)((-2)**(-0))(421/(2**12))(421/(2**12))
    {
        "target": ("10010101", 421, "00000000", 11, 8, 4096),
        "answer": (np.float64(421) * np.float64(11)) / np.float_power(2, 20, dtype=np.float64),
    },
    # (2**8)((-2)**(-4))(421/(2**12))(11/(2**12))
]


@pytest.mark.parametrize("test_items", test_setup_ensemble)
def test_ensemble_cell_rust(test_items: TargetItemEnsembleCell):
    """Test the ensemble_cell_rust function."""

    assert rust_available_randomized, "Rust is not available."
    ensemble_cell_py_result = ensemble_cell_py(*test_items["target"])
    ensemble_cell_rust_result = ensemble_cell_rust(*test_items["target"])

    assert (
        np.abs(ensemble_cell_rust_result - ensemble_cell_py_result) < 1e-10
    ), "Rust and Python results are not equal in ensemble_cell."
    assert np.abs(ensemble_cell_rust_result - test_items["answer"]) < 1e-10, (
        "The result of ensemble_cell is not correct,"
        + f"ensemble_cell_rust_result: {ensemble_cell_rust_result} "
        + f"!= test_items['answer']: {test_items['answer']}"
    )
