extern crate pyo3;
extern crate rayon;

use pyo3::prelude::*;
use rayon::iter::IntoParallelRefIterator;
use rayon::prelude::*;
use std::collections::HashMap;
use std::time::Instant;

use crate::randomized::construct::{degree_handler_rust, QubitDegree};
use crate::randomized::randomized::purity_cell_rust;

#[pyfunction]
#[pyo3(signature = (shots, counts, degree=None, measure=None))]
pub fn entangled_entropy_core_rust(
    shots: i32,
    counts: Vec<HashMap<String, i32>>,
    degree: Option<QubitDegree>,
    measure: Option<(i32, i32)>,
) -> (HashMap<i32, f64>, (i32, i32), (i32, i32), &'static str, f64) {
    // check if the sum of shots is equal to the sum of all counts
    let sample_shots: i32 = counts[0].values().sum();
    assert!(shots == sample_shots);

    // Determine the size of the allsystems
    let allsystems_size: i32 = counts[0].keys().next().unwrap().len() as i32;

    // Determine degree
    let (bitstring_range, actual_measure, subsystems_size) =
        degree_handler_rust(allsystems_size, degree, measure);

    let begin: Instant = Instant::now();

    let mut purity_loader_2: HashMap<i32, f64> = HashMap::new();
    let result_vec = counts.par_iter().enumerate().map(|(identifier, data)| {
        let result: (i32, f64) = purity_cell_rust(
            identifier as i32,
            data.clone(),
            bitstring_range,
            subsystems_size,
        );
        // println!("| purity_cell: {:?} {}", result, subsystems_size);
        result
    });
    result_vec
        .collect::<Vec<(i32, f64)>>()
        .iter()
        .for_each(|(idx, purity_cell)| {
            purity_loader_2.insert(*idx, *purity_cell);
        });

    let duration_2: f64 = begin.elapsed().as_secs_f64() as f64;

    (
        purity_loader_2,
        bitstring_range,
        actual_measure,
        "",
        duration_2,
    )
}
