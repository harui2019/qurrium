extern crate pyo3;

use pyo3::prelude::*;

#[pyfunction]
#[pyo3(signature = (s_i, s_j))]
pub fn hamming_distance_rust(s_i: &str, s_j: &str) -> i32 {
    // Proved to be correct
    s_i.chars()
        .zip(s_j.chars())
        .filter(|(c1, c2)| c1 != c2)
        .count() as i32
}

#[pyfunction]
#[pyo3(signature = (s_i, s_i_meas, s_j, s_j_meas, a_num, shots))]
pub fn ensemble_cell_rust(
    s_i: &str,
    s_i_meas: i32,
    s_j: &str,
    s_j_meas: i32,
    a_num: i32,
    shots: i32,
) -> f64 {
    // Must to be f64 for all the values
    // Otherwise, float will lose precision
    // Proved to be correct
    let diff: i32 = hamming_distance_rust(s_i, s_j);
    let tmp: f64 = f64::powi(2.0, a_num)
        * f64::powi(-2.0, -diff)
        * (((s_i_meas as f64) / (shots as f64)) as f64)
        * (((s_j_meas as f64) / (shots as f64)) as f64);
    tmp
}
