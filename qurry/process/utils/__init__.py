"""Utility functions for qurry.process (:mod:`qurry.process.utils`)"""

from .counts_process import (
    single_counts_recount_proto,
    single_counts_recount_pyrust,
    counts_list_recount_pyrust,
    BACKEND_AVAILABLE as counts_process_availability,
    selected_clregs_to_optlist,
    shot_counts_selected_clreg_checker,
    shot_counts_selected_clreg_checker_pyrust,
    counts_list_vectorize_pyrust,
    rho_m_flatten_counts_list_vectorize_pyrust,
    check_invalid_counts,
)
from .other import NUMERICAL_ERROR_TOLERANCE, FloatType
from .bit_slice import (
    qubit_selector,
    cycling_slice,
    degree_handler,
    qubit_mapper,
    QubitSelectionType,
    is_cycling_slice_active,
    BACKEND_AVAILABLE as bit_slice_availability,
)
from .randomized import (
    hamming_distance,
    ensemble_cell,
    hamming_distance_rust,
    ensemble_cell_rust,
    BACKEND_AVAILABLE as randomized_availability,
)
from .dummy import BACKEND_AVAILABLE as dummy_availability
from .purity import clamp_purity, depolarizing_error_mitgation, MitigatedResult
from .method_enum import BaseMethodEnum
from .bloch_vector import density_matrix_to_bloch_vector
