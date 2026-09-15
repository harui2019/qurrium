use pyo3::prelude::*;
use rayon::iter::IntoParallelRefIterator;
use rayon::prelude::*;
use std::collections::HashMap;
use std::time::Instant;

use crate::counts_process::{check_invalid_counts, single_counts_recount_prototype};

pub fn check_invalid_counts_magsq(counts: &Vec<HashMap<String, i32>>) {
    let invalid_counts = counts
        .iter()
        .enumerate()
        .filter(|(_i, single_counts)| single_counts.keys().all(|bits| bits.len() != 2))
        .map(|(i, _)| i)
        .collect::<Vec<_>>();
    if !invalid_counts.is_empty() {
        panic!(
            "The counts must be equal to the number of shots, but following counts are invalid, index: {:?}",
            invalid_counts
        );
    }
}

pub fn magsq_cell_rust(idx: i32, single_counts: &HashMap<String, i32>, shots: i32) -> (i32, f64) {
    let mut magnetsq_cell: f64 = 0.0;

    for (bits, &count) in single_counts.iter() {
        let weight = if bits.chars().nth(0) == bits.chars().nth(1) {
            1.0
        } else {
            -1.0
        };
        magnetsq_cell += (count as f64) * weight / (shots as f64);
    }

    (idx, magnetsq_cell)
}

#[pyfunction]
#[pyo3(signature = (shots, counts, num_qubits))]
pub fn magnet_square_core_rust(
    shots: i32,
    counts: Vec<HashMap<String, i32>>,
    num_qubits: i32,
) -> (f64, HashMap<i32, f64>, f64) {
    check_invalid_counts(shots, &counts);
    check_invalid_counts_magsq(&counts);

    let begin = Instant::now();

    let magnetsq_cell_vec = counts
        .par_iter()
        .enumerate()
        .map(|(idx, count)| magsq_cell_rust(idx as i32, count, shots))
        .collect::<Vec<(i32, f64)>>();

    let magnetsq_cell_dict: HashMap<i32, f64> = magnetsq_cell_vec.into_iter().collect();

    let magnetsq =
        (magnetsq_cell_dict.values().sum::<f64>() + num_qubits as f64) / (num_qubits.pow(2) as f64);

    let taken = begin.elapsed().as_secs_f64();

    (magnetsq, magnetsq_cell_dict, taken)
}

#[pyfunction]
#[pyo3(signature = (shots, single_counts, num_qubits))]
pub fn z_dir_magnet_square_core_rust(
    shots: i32,
    single_counts: HashMap<String, i32>,
    num_qubits: i32,
) -> (f64, HashMap<i32, f64>, f64) {
    let sample_shots: i32 = single_counts.values().sum();
    assert_eq!(
        shots, sample_shots,
        "shots {} does not match sample_shots {}",
        shots, sample_shots
    );

    let begin = Instant::now();

    let permutations = (0..num_qubits)
        .flat_map(|i| {
            (0..num_qubits)
                .filter(move |&j| j != i)
                .map(move |j| (i, j))
        })
        .collect::<Vec<(i32, i32)>>();

    let magnetsq_cell_vec = permutations
        .par_iter()
        .enumerate()
        .map(|(idx, &pair)| {
            let recounted = single_counts_recount_prototype(
                &single_counts,
                num_qubits,
                &vec![pair.0 as i32, pair.1 as i32],
            );
            magsq_cell_rust(idx as i32, &recounted, shots)
        })
        .collect::<Vec<(i32, f64)>>();

    let magnetsq_cell_dict = magnetsq_cell_vec.into_iter().collect::<HashMap<i32, f64>>();

    let magnetsq =
        (magnetsq_cell_dict.values().sum::<f64>() + num_qubits as f64) / (num_qubits.pow(2) as f64);

    let taken = begin.elapsed().as_secs_f64();

    (magnetsq, magnetsq_cell_dict, taken)
}
