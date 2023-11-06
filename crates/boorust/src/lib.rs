mod randomized;

extern crate pyo3;

use pyo3::prelude::*;

use crate::randomized::randomized::{
    entangled_entropy_core_rust,
    ensemble_cell_rust,
    hamming_distance_rust,
    purity_cell_rust,
};
use crate::randomized::construct::{ cycling_slice_rust, qubit_selector_rust };

// #[pymodule]
// fn boorust(py: Python<'_>, m: &PyModule) -> PyResult<()> {
//     register_child_module(py, m)?;
//     Ok(())
// }

// fn register_child_module(py: Python<'_>, parent_module: &PyModule) -> PyResult<()> {
//     let randomized = PyModule::new(py, "randomized")?;
//     randomized.add_function(wrap_pyfunction!(entangled_entropy_core_rust, randomized)?)?;
//     randomized.add_function(wrap_pyfunction!(ensemble_cell_rust, randomized)?)?;
//     randomized.add_function(wrap_pyfunction!(hamming_distance_rust, randomized)?)?;
//     randomized.add_function(wrap_pyfunction!(purity_cell_rust, randomized)?)?;

//     let construct = PyModule::new(py, "construct")?;
//     construct.add_function(wrap_pyfunction!(qubit_selector_rust, construct)?)?;
//     construct.add_function(wrap_pyfunction!(cycling_slice_rust, construct)?)?;

//     parent_module.add_submodule(randomized)?;
//     parent_module.add_submodule(construct)?;
//     Ok(())
// }

// '''
// Note that this does not define a package,
// so this won’t allow Python code to directly import submodules
// by using from parent_module import child_module.
// For more information, see #759 and #1517.
// '''
// WTF?

#[pymodule]
fn boorust(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(entangled_entropy_core_rust, m)?)?;
    m.add_function(wrap_pyfunction!(ensemble_cell_rust, m)?)?;
    m.add_function(wrap_pyfunction!(cycling_slice_rust, m)?)?;
    m.add_function(wrap_pyfunction!(hamming_distance_rust, m)?)?;
    m.add_function(wrap_pyfunction!(purity_cell_rust, m)?)?;
    m.add_function(wrap_pyfunction!(qubit_selector_rust, m)?)?;
    Ok(())
}
