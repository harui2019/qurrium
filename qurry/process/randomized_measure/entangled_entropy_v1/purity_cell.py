"""Post Processing - Randomized Measure - Entangled Entropy V1 - Purity Cell
(:mod:`qurry.process.randomized_measure.entangled_entropy_v1.purity_cell`)

"""

import numpy as np

from ...utils import ensemble_cell as ensemble_cell_py, cycling_slice as cycling_slice_py


def purity_cell_py(
    idx: int,
    single_counts: dict[str, int],
    bitstring_range: tuple[int, int],
    subsystem_size: int,
) -> tuple[int, np.float64]:
    """Calculate the purity cell, one of overlap, of a subsystem by Python.

    Args:
        idx (int): Index of the cell (counts).
        single_counts (dict[str, int]): Counts measured by the single quantum circuit.
        bitstring_range (tuple[int, int]): The range of the subsystem.
        subsystem_size (int): Subsystem size included.

    Returns:
        tuple[int, float]: Index, one of overlap purity.
    """

    shots = sum(single_counts.values())

    _dummy_string = list(range(len(list(single_counts.keys())[0])))

    if _dummy_string[bitstring_range[0] : bitstring_range[1]] == cycling_slice_py(
        _dummy_string, bitstring_range[0], bitstring_range[1], 1
    ):
        single_counts_under_degree = dict.fromkeys(
            [k[bitstring_range[0] : bitstring_range[1]] for k in single_counts], 0
        )
        for bitstring in list(single_counts):
            single_counts_under_degree[bitstring[bitstring_range[0] : bitstring_range[1]]] += (
                single_counts[bitstring]
            )

    else:
        single_counts_under_degree = dict.fromkeys(
            [cycling_slice_py(k, bitstring_range[0], bitstring_range[1], 1) for k in single_counts],
            0,
        )
        for bitstring in list(single_counts):
            single_counts_under_degree[
                cycling_slice_py(bitstring, bitstring_range[0], bitstring_range[1], 1)
            ] += single_counts[bitstring]

    _purity_cell = np.float64(0)
    for s_ai, s_ai_meas in single_counts_under_degree.items():
        for s_aj, s_aj_meas in single_counts_under_degree.items():
            _purity_cell += ensemble_cell_py(
                s_ai, s_ai_meas, s_aj, s_aj_meas, subsystem_size, shots
            )

    return idx, _purity_cell
