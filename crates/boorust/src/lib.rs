mod bit_slice;
mod counts_process;
mod hadamard;
mod magnet_square;
mod randomized;
mod shadow;
mod string_operator;
mod tool;

use pyo3::prelude::*;

use crate::bit_slice::{cycling_slice_rust, degree_handler_rust, qubit_selector_rust};
use crate::counts_process::{
    counts_list_recount_rust, counts_list_vectorize_rust, rho_m_flatten_counts_list_vectorize_rust,
    shot_counts_selected_clreg_checker, single_counts_recount_rust,
};
use crate::hadamard::purity_echo_core_rust;
use crate::magnet_square::{magnet_square_core_rust, z_dir_magnet_square_core_rust};
use crate::randomized::echo::v1::overlap_echo_core_rust;
use crate::randomized::echo::v2::overlap_echo_core_2_rust;
use crate::randomized::entropy::v1::entangled_entropy_core_rust;
use crate::randomized::entropy::v2::entangled_entropy_core_2_rust;
use crate::randomized::randomized::{ensemble_cell_rust, hamming_distance_rust};
use crate::shadow::nomatmul_trace::nomatmul_trace_sum_rust;
use crate::string_operator::string_operator_core_rust;
use crate::tool::{make_dummy_case_32, make_two_bit_str_32, make_two_bit_str_unlimit};

#[pymodule]
mod boorust {
    #[pymodule_export]
    use super::bit_slice_py;
    #[pymodule_export]
    use super::counts_process_py;
    #[pymodule_export]
    use super::hadamard_py;
    #[pymodule_export]
    use super::magnet_square_py;
    #[pymodule_export]
    use super::randomized_py;
    #[pymodule_export]
    use super::shadow_py;
    #[pymodule_export]
    use super::string_operator_py;
    #[pymodule_export]
    use super::dummy_py;
}

#[pymodule(name = "bit_slice")]
mod bit_slice_py {
    #[pymodule_export]
    use super::cycling_slice_rust;
    #[pymodule_export]
    use super::degree_handler_rust;
    #[pymodule_export]
    use super::qubit_selector_rust;
}

#[pymodule(name = "randomized")]
mod randomized_py {
    #[pymodule_export]
    use super::ensemble_cell_rust;
    #[pymodule_export]
    use super::entangled_entropy_core_2_rust;
    #[pymodule_export]
    use super::entangled_entropy_core_rust;
    #[pymodule_export]
    use super::hamming_distance_rust;
    #[pymodule_export]
    use super::overlap_echo_core_2_rust;
    #[pymodule_export]
    use super::overlap_echo_core_rust;
}

#[pymodule(name = "counts_process")]
mod counts_process_py {
    #[pymodule_export]
    use super::counts_list_recount_rust;
    #[pymodule_export]
    use super::counts_list_vectorize_rust;
    #[pymodule_export]
    use super::rho_m_flatten_counts_list_vectorize_rust;
    #[pymodule_export]
    use super::shot_counts_selected_clreg_checker;
    #[pymodule_export]
    use super::single_counts_recount_rust;
}

#[pymodule(name = "hadamard")]
mod hadamard_py {
    #[pymodule_export]
    use super::purity_echo_core_rust;
}

#[pymodule(name = "magnet_square")]
mod magnet_square_py {
    #[pymodule_export]
    use super::magnet_square_core_rust;
    #[pymodule_export]
    use super::z_dir_magnet_square_core_rust;
}

#[pymodule(name = "string_operator")]
mod string_operator_py {
    #[pymodule_export]
    use super::string_operator_core_rust;
}

#[pymodule(name = "shadow")]
mod shadow_py {
    #[pymodule_export]
    use super::nomatmul_trace_sum_rust;
}

#[pymodule(name = "dummy")]
mod dummy_py {
    #[pymodule_export]
    use super::make_dummy_case_32;
    #[pymodule_export]
    use super::make_two_bit_str_32;
    #[pymodule_export]
    use super::make_two_bit_str_unlimit;
}
