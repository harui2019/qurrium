extern crate pyo3;
extern crate rayon;

use pyo3::prelude::*;
use rayon::iter::IntoParallelRefIterator;
use rayon::{prelude::*, result};
use std::collections::HashMap;
use std::time::Instant;

use crate::randomized::construct::{degree_handler_rust, QubitDegree};
use crate::randomized::randomized::purity_cell_2_rust;

#[pyfunction]
pub fn entangled_entropy_core_2_rust(
    shots: i32,
    counts: Vec<HashMap<String, i32>>,
    selected_classical_registers: Option<Vec<i32>>,
) -> (HashMap<i32, f64>, Vec<i32>, &'static str, f64) {
    // check if the sum of shots is equal to the sum of all counts
    let sample_shots: i32 = counts[0].values().sum();
    assert_eq!(
        shots, sample_shots,
        "shots {} does not match sample_shots {}",
        a, b
    );

    // Determine the size of the allsystems
    let measured_system_size: i32 = counts[0].keys().next().unwrap().len() as i32;

    let selected_classical_registers_actual = match selected_classical_registers {
        Some(selected_classical_registers) => selected_classical_registers,
        None => (0..measured_system_size).collect(),
    };

    let begin: Instant = Instant::now();

    let result_vec = counts.par_iter().enumerate().map(|(identifier, data)| {
        let result: (i32, f64, Vec<i32>) = purity_cell_2_rust(
            identifier as i32,
            data.clone(),
            selected_classical_registers_actual.clone(),
        );
        // println!("| purity_cell: {:?} {}", result, subsystems_size);
        result
    });

    let selected_classical_registers_actual_sorted = {
        let mut selected_sorted_inner = selected_classical_registers_actual.clone();
        selected_sorted_inner.sort();
        selected_sorted_inner
    };
    let mut purity_loader_2: HashMap<i32, f64> = HashMap::new();
    let mut selected_classical_registers_checked: HashMap<i32, Vec<i32>> = HashMap::new();
    result_vec
        .collect::<Vec<(i32, f64, Vec<i32>)>>()
        .iter()
        .for_each(
            |(idx, purity_cell, selected_classical_registers_sorted_result)| {
                purity_loader_2.insert(*idx, *purity_cell);

                let compare = selected_classical_registers_actual_sorted
                    .iter()
                    .zip(selected_classical_registers_sorted_result.iter())
                    .all(|(a, b)| a == b);
                if !compare {
                    selected_classical_registers_checked
                        .insert(*idx, selected_classical_registers_sorted_result.clone());
                }
            },
        );
    if selected_classical_registers_checked.len() > 0 {
        println!(
            "Selected classical registers are not the same: {:?}",
            selected_classical_registers_checked
        );
    }

    let duration_2: f64 = begin.elapsed().as_secs_f64() as f64;

    (
        purity_loader_2,
        selected_classical_registers_actual_sorted,
        "",
        duration_2,
    )
}
