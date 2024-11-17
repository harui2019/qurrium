extern crate pyo3;
extern crate rayon;

use pyo3::prelude::*;
use rayon::iter::IntoParallelRefIterator;
use rayon::prelude::*;
use std::collections::HashMap;
use std::time::Instant;

use crate::randomized::construct::{degree_handler_rust, QubitDegree};
use crate::randomized::randomized::echo_cell_rust;

#[pyfunction]
#[pyo3(signature = (shots, counts, degree=None, measure=None))]
pub fn overlap_echo_core_rust(
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

    assert!(
        counts.len() % 2 == 0,
        "The counts should be even: {}.",
        counts.len()
    );
    let times = counts.len() / 2;

    let counts_pair: Vec<(HashMap<String, i32>, HashMap<String, i32>)> = (0..times)
        .map(|i| {
            let first_counts = counts[i].clone();
            let second_counts = counts[i + times].clone();
            (first_counts, second_counts)
        })
        .collect();

    let begin: Instant = Instant::now();

    let mut echo_loader_2: HashMap<i32, f64> = HashMap::new();
    let result_vec = counts_pair
        .par_iter()
        .enumerate()
        .map(|(identifier, (data, data2))| {
            let result: (i32, f64) = echo_cell_rust(
                identifier as i32,
                data.clone(),
                data2.clone(),
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
            echo_loader_2.insert(*idx, *purity_cell);
        });

    let duration_2: f64 = begin.elapsed().as_secs_f64() as f64;

    (
        echo_loader_2,
        bitstring_range,
        actual_measure,
        "",
        duration_2,
    )
}
