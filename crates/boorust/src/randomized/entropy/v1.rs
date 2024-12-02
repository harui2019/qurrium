extern crate pyo3;
extern crate rayon;

use pyo3::prelude::*;
use rayon::iter::IntoParallelRefIterator;
use rayon::prelude::*;
use std::collections::HashMap;
use std::time::Instant;

use crate::construct::{cycling_slice_rust, degree_handler_rust, QubitDegree};
use crate::randomized::randomized::ensemble_cell_rust;

#[pyfunction]
#[pyo3(signature = (idx, single_counts, bit_string_range, subsystem_size))]
pub fn purity_cell_rust(
    idx: i32,
    single_counts: HashMap<String, i32>,
    bit_string_range: (i32, i32),
    subsystem_size: i32,
) -> (i32, f64) {
    let shots: i32 = single_counts.values().sum();
    let _dummy_string: String = (0..subsystem_size).map(|ds| ds.to_string()).collect();
    let mut single_counts_under_degree: HashMap<String, i32> = HashMap::new();

    if 0 <= bit_string_range.0 && bit_string_range.1 <= subsystem_size {
        // serial
        for (bit_string, count) in &single_counts {
            let substring = &bit_string[bit_string_range.0 as usize..bit_string_range.1 as usize];
            let entry = single_counts_under_degree
                .entry(substring.to_string())
                .or_insert(0);
            *entry += count;
        }
    } else {
        // cycling
        for (bit_string, count) in &single_counts {
            let key = cycling_slice_rust(&bit_string, bit_string_range.0, bit_string_range.1, 1);
            let substring = match key {
                Ok(string) => string.to_string(),
                Err(err) => {
                    panic!("Error: {}", err)
                }
            };
            let entry = single_counts_under_degree
                .entry(substring.to_string())
                .or_insert(0);
            *entry += count;
        }
    }

    let purity_cell: f64 = single_counts_under_degree
        .par_iter()
        .flat_map(|(s_ai, s_ai_meas)| {
            single_counts_under_degree
                .par_iter()
                .map(move |(s_aj, s_aj_meas)| {
                    ensemble_cell_rust(s_ai, *s_ai_meas, s_aj, *s_aj_meas, subsystem_size, shots)
                })
        })
        .sum();

    (idx, purity_cell)
}

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
