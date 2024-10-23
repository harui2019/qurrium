extern crate pyo3;
extern crate rayon;

use pyo3::prelude::*;
use rayon::prelude::*;
use std::collections::HashMap;
use std::panic;

use crate::randomized::construct::cycling_slice_rust;

#[pyfunction]
pub fn hamming_distance_rust(s_i: &str, s_j: &str) -> i32 {
    // Proved to be correct
    s_i.chars()
        .zip(s_j.chars())
        .filter(|(c1, c2)| c1 != c2)
        .count() as i32
}

#[pyfunction]
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

#[pyfunction]
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
pub fn echo_cell_rust(
    idx: i32,
    single_counts: HashMap<String, i32>,
    second_counts: HashMap<String, i32>,
    bit_string_range: (i32, i32),
    subsystem_size: i32,
) -> (i32, f64) {
    let shots: i32 = single_counts.values().sum();
    let shots2: i32 = second_counts.values().sum();
    assert_eq!(
        shots, shots2,
        "The number of shots must be equal, count1: {}, count2: {}",
        shots, shots2
    );

    let _dummy_string: String = (0..subsystem_size).map(|ds| ds.to_string()).collect();
    let mut single_counts_under_degree: HashMap<String, i32> = HashMap::new();
    let mut second_counts_under_degree: HashMap<String, i32> = HashMap::new();

    if 0 <= bit_string_range.0 && bit_string_range.1 <= subsystem_size {
        // serial
        for (bit_string, count) in &single_counts {
            let substring = &bit_string[bit_string_range.0 as usize..bit_string_range.1 as usize];
            let entry = single_counts_under_degree
                .entry(substring.to_string())
                .or_insert(0);
            *entry += count;
        }
        for (bit_string, count) in &second_counts {
            let substring = &bit_string[bit_string_range.0 as usize..bit_string_range.1 as usize];
            let entry = second_counts_under_degree
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
        for (bit_string, count) in &second_counts {
            let key = cycling_slice_rust(&bit_string, bit_string_range.0, bit_string_range.1, 1);
            let substring = match key {
                Ok(string) => string.to_string(),
                Err(err) => {
                    panic!("Error: {}", err)
                }
            };
            let entry = second_counts_under_degree
                .entry(substring.to_string())
                .or_insert(0);
            *entry += count;
        }
    }

    let echo_cell: f64 = single_counts_under_degree
        .par_iter()
        .flat_map(|(s_ai, s_ai_meas)| {
            second_counts_under_degree
                .par_iter()
                .map(move |(s_aj, s_aj_meas)| {
                    ensemble_cell_rust(s_ai, *s_ai_meas, s_aj, *s_aj_meas, subsystem_size, shots)
                })
        })
        .sum();

    (idx, echo_cell)
}
