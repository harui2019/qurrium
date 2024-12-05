extern crate pyo3;
extern crate rayon;

use pyo3::prelude::*;
use rayon::iter::IntoParallelRefIterator;
use rayon::prelude::*;
use std::collections::HashMap;
use std::time::Instant;

use crate::randomized::randomized::ensemble_cell_rust;

#[pyfunction]
#[pyo3(signature = (idx, single_counts, selected_classical_registers))]
pub fn purity_cell_2_rust(
    idx: i32,
    single_counts: HashMap<String, i32>,
    selected_classical_registers: Vec<i32>,
) -> (i32, f64, Vec<i32>) {
    let shots: i32 = single_counts.values().sum();
    let num_classical_registers: i32 = single_counts.keys().next().unwrap().len() as i32;

    let mut selected_classical_registers_sorted = selected_classical_registers.clone();
    selected_classical_registers_sorted.sort();
    let subsystem_size = selected_classical_registers_sorted.len() as i32;

    let mut single_counts_under_degree: HashMap<String, i32> = HashMap::new();
    for (bit_string_all, count) in &single_counts {
        let substring = selected_classical_registers
            .iter()
            .map(|&i| {
                bit_string_all
                    .chars()
                    .nth((num_classical_registers - i - 1) as usize)
                    .unwrap()
            })
            .collect::<String>();
        let entry = single_counts_under_degree
            .entry(substring.to_string())
            .or_insert(0);
        *entry += count;
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

    (idx, purity_cell, selected_classical_registers_sorted)
}

#[pyfunction]
#[pyo3(signature = (shots, counts, selected_classical_registers=None))]
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
        shots, sample_shots,
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
