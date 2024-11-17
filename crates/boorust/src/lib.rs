mod hadamard;
mod randomized;
mod tool;
extern crate pyo3;

use pyo3::prelude::*;

use crate::hadamard::purity_echo_core_rust;
use crate::randomized::construct::{
    cycling_slice_rust, degree_handler_rust, qubit_selector_rust, test_construct,
};
use crate::randomized::echo::overlap_echo_core_rust;
use crate::randomized::entropy::entangled_entropy_core_rust;
use crate::randomized::entropy_2::entangled_entropy_core_2_rust;
use crate::randomized::randomized::{
    echo_cell_rust, ensemble_cell_rust, hamming_distance_rust, purity_cell_2_rust, purity_cell_rust,
};
use crate::tool::{make_dummy_case_32, make_two_bit_str_32, make_two_bit_str_unlimit};

#[pymodule]
fn boorust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    register_child_module(m)?;
    Ok(())
}

fn register_child_module(parent_module: &Bound<'_, PyModule>) -> PyResult<()> {
    let randomized = PyModule::new(parent_module.py(), "randomized")?;
    // construct
    randomized.add_function(wrap_pyfunction!(ensemble_cell_rust, &randomized)?)?;
    randomized.add_function(wrap_pyfunction!(hamming_distance_rust, &randomized)?)?;
    // core
    randomized.add_function(wrap_pyfunction!(purity_cell_rust, &randomized)?)?;
    randomized.add_function(wrap_pyfunction!(echo_cell_rust, &randomized)?)?;
    randomized.add_function(wrap_pyfunction!(purity_cell_2_rust, &randomized)?)?;
    // main
    randomized.add_function(wrap_pyfunction!(entangled_entropy_core_rust, &randomized)?)?;
    randomized.add_function(wrap_pyfunction!(
        entangled_entropy_core_2_rust,
        &randomized
    )?)?;
    randomized.add_function(wrap_pyfunction!(overlap_echo_core_rust, &randomized)?)?;

    let construct = PyModule::new(parent_module.py(), "construct")?;
    construct.add_function(wrap_pyfunction!(qubit_selector_rust, &construct)?)?;
    construct.add_function(wrap_pyfunction!(cycling_slice_rust, &construct)?)?;
    construct.add_function(wrap_pyfunction!(degree_handler_rust, &construct)?)?;

    let hadamard = PyModule::new(parent_module.py(), "hadamard")?;
    hadamard.add_function(wrap_pyfunction!(purity_echo_core_rust, &hadamard)?)?;

    let dummy = PyModule::new(parent_module.py(), "dummy")?;
    dummy.add_function(wrap_pyfunction!(make_two_bit_str_32, &dummy)?)?;
    dummy.add_function(wrap_pyfunction!(make_dummy_case_32, &dummy)?)?;
    dummy.add_function(wrap_pyfunction!(make_two_bit_str_unlimit, &dummy)?)?;

    let test = PyModule::new(parent_module.py(), "test")?;
    test.add_function(wrap_pyfunction!(test_construct, &test)?)?;

    parent_module.add_submodule(&randomized)?;
    parent_module.add_submodule(&construct)?;
    parent_module.add_submodule(&hadamard)?;
    parent_module.add_submodule(&dummy)?;
    parent_module.add_submodule(&test)?;
    Ok(())
}

// """
// Note that this does not define a package,
// so this won’t allow Python code to directly import submodules
// by using from parent_module import child_module.
// For more information,
// see [#759](https://github.com/PyO3/pyo3/issues/759)
// and [#1517](https://github.com/PyO3/pyo3/issues/1517).
// from https://pyo3.rs/v0.23.0/module.html#python-submodules
// (Since PyO3 0.20.0, until PyO3 0.23.0)
// :smile:
// """
