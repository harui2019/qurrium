extern crate pyo3;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use std::collections::HashMap;

#[allow(dead_code)]
#[pyfunction]
pub fn purity_echo_core_rust(
    shots: i32,
    counts: Vec<HashMap<String, i32>>,
) -> PyResult<f64> {
    let only_counts = &counts[0];
    let sample_shots: i32 = only_counts.values().sum();

    if sample_shots != shots {
        return Err(PyValueError::new_err(format!(
            "shots {} does not match sample_shots {}",
            shots, sample_shots
        )));
    }

    let is_zero_include = only_counts.contains_key("0");
    let is_one_include = only_counts.contains_key("1");

    if is_zero_include && is_one_include {
        Ok((only_counts["0"] - only_counts["1"]) as f64 / shots as f64)
    } else if is_zero_include {
        Ok(only_counts["0"] as f64 / shots as f64)
    } else if is_one_include {
        Ok(only_counts["1"] as f64 / shots as f64)
    } else {
        Err(PyValueError::new_err(
            "Expected '0' and '1', but there is no such keys",
        ))
    }
}
