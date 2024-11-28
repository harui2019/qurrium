extern crate pyo3;
extern crate rayon;

use pyo3::prelude::*;
use rayon::iter::IntoParallelRefIterator;
use rayon::prelude::*;
use std::collections::HashMap;
use std::time::Instant;

use crate::randomized::randomized::ensemble_cell_rust;

#[pyfunction]
#[pyo3(signature = (idx, first_counts, second_counts, selected_classical_registers))]
pub fn echo_cell_2_rust(
    idx: i32,
    first_counts: HashMap<String, i32>,
    second_counts: HashMap<String, i32>,
    selected_classical_registers: Vec<i32>,
) -> (i32, f64, Vec<i32>) {
    let sample_shots_01: i32 = first_counts.values().sum();
    let sample_shots_02: i32 = second_counts.values().sum();
    assert_eq!(
        sample_shots_01, sample_shots_02,
        "The number of shots must be equal, but the first count is {}, and the second count is {}, in the index {}",
        sample_shots_01, sample_shots_02, idx,
    );

    let num_classical_registers_01: i32 = first_counts.keys().next().unwrap().len() as i32;
    let num_classical_registers_02: i32 = second_counts.keys().next().unwrap().len() as i32;
    assert_eq!(
        num_classical_registers_01, num_classical_registers_02,
        "The number of classical registers must be equal, but the first count is {}, and the second count is {}, in the index {}",
        num_classical_registers_01, num_classical_registers_02, idx,
    );

    let shots: i32 = sample_shots_01.clone();
    let num_classical_registers: i32 = num_classical_registers_01.clone();

    let mut selected_classical_registers_sorted = selected_classical_registers.clone();
    selected_classical_registers_sorted.sort();
    let subsystem_size = selected_classical_registers_sorted.len() as i32;

    let mut first_counts_under_degree: HashMap<String, i32> = HashMap::new();
    for (bit_string_all, count) in &first_counts {
        let substring = selected_classical_registers
            .iter()
            .map(|&i| {
                bit_string_all
                    .chars()
                    .nth((num_classical_registers - i - 1) as usize)
                    .unwrap()
            })
            .collect::<String>();
        let entry = first_counts_under_degree
            .entry(substring.to_string())
            .or_insert(0);
        *entry += count;
    }

    let mut second_counts_under_degree: HashMap<String, i32> = HashMap::new();
    for (bit_string_all, count) in &second_counts {
        let substring = selected_classical_registers
            .iter()
            .map(|&i| {
                bit_string_all
                    .chars()
                    .nth((num_classical_registers - i - 1) as usize)
                    .unwrap()
            })
            .collect::<String>();
        let entry = second_counts_under_degree
            .entry(substring.to_string())
            .or_insert(0);
        *entry += count;
    }

    let echo_cell: f64 = first_counts_under_degree
        .par_iter()
        .flat_map(|(s_ai, s_ai_meas)| {
            second_counts_under_degree
                .par_iter()
                .map(move |(s_aj, s_aj_meas)| {
                    ensemble_cell_rust(s_ai, *s_ai_meas, s_aj, *s_aj_meas, subsystem_size, shots)
                })
        })
        .sum();

    (idx, echo_cell, selected_classical_registers_sorted)
}

#[pyfunction]
#[pyo3(signature = (shots, first_counts, second_counts, selected_classical_registers=None))]
pub fn overlap_echo_core_2_rust(
    shots: i32,
    first_counts: Vec<HashMap<String, i32>>,
    second_counts: Vec<HashMap<String, i32>>,
    selected_classical_registers: Option<Vec<i32>>,
) -> (HashMap<i32, f64>, Vec<i32>, &'static str, f64) {
    assert_eq!(
        first_counts.len(),
        second_counts.len(),
        "The number of counts must be equal, but the first count is {}, and the second count is {}",
        first_counts.len(),
        second_counts.len(),
    );

    let sample_shots_01: i32 = first_counts[0].values().sum();
    let sample_shots_02: i32 = second_counts[0].values().sum();
    for (tmp01, tmp02, tmp01_name, tmp02_name) in vec![
        (shots, sample_shots_01, "shots", "first counts"),
        (shots, sample_shots_02, "shots", "second counts"),
        (
            sample_shots_01,
            sample_shots_02,
            "first counts",
            "second counts",
        ),
    ] {
        assert_eq!(
            tmp01, tmp02,
            "The number of shots must be equal, but the {} is {}, and the {} is {}",
            tmp01_name, tmp01, tmp02_name, tmp02,
        );
    }

    let sample_bitstrings_num_01: i32 = first_counts[0].keys().next().unwrap().len() as i32;
    let sample_bitstrings_num_02: i32 = second_counts[0].keys().next().unwrap().len() as i32;
    assert_eq!(
        sample_bitstrings_num_01, sample_bitstrings_num_02,
        "The number of bitstrings must be equal, but the first counts is {}, and the second counts is {}",
        sample_bitstrings_num_01, sample_bitstrings_num_02,
    );
    let measured_system_size: i32 = first_counts[0].keys().next().unwrap().len() as i32;

    let selected_classical_registers_actual = match selected_classical_registers {
        Some(selected_classical_registers) => selected_classical_registers,
        None => (0..measured_system_size).collect(),
    };

    let begin: Instant = Instant::now();

    let counts_pair: Vec<(HashMap<String, i32>, HashMap<String, i32>)> = (0..first_counts.len())
        .map(|i| (first_counts[i].clone(), second_counts[i].clone()))
        .collect();

    let result_vec = counts_pair
        .par_iter()
        .enumerate()
        .map(|(identifier, (data, data2))| {
            let result: (i32, f64, Vec<i32>) = echo_cell_2_rust(
                identifier as i32,
                data.clone(),
                data2.clone(),
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
    let mut echo_loader_2: HashMap<i32, f64> = HashMap::new();
    let mut selected_classical_registers_checked: HashMap<i32, Vec<i32>> = HashMap::new();
    result_vec
        .collect::<Vec<(i32, f64, Vec<i32>)>>()
        .iter()
        .for_each(
            |(idx, purity_cell, selected_classical_registers_sorted_result)| {
                echo_loader_2.insert(*idx, *purity_cell);

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
        echo_loader_2,
        selected_classical_registers_actual_sorted,
        "",
        duration_2,
    )
}
