extern crate pyo3;

use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;

#[derive(Clone)]
#[derive(FromPyObject)]
pub enum QubitDegree {
    Pair(i32, i32),
    Single(i32),
}

#[pyfunction]
pub fn cycling_slice_rust(target: &str, start: i32, end: i32, step: i32) -> PyResult<String> {
    let length = target.len() as i32;
    let slice_check = vec![
        ("start <= -length", start <= -length),
        ("end >= length", end >= length)
    ];

    if slice_check.iter().all(|&(_, v)| v) {
        let invalid_ranges: Vec<String> = slice_check
            .iter()
            .filter(|&&(_, v)| !v)
            .map(|&(k, _)| format!(" {}", k))
            .collect();
        return Err(
            PyValueError::new_err(format!("Slice out of range: {}", invalid_ranges.join(";")))
        );
    }

    if length <= 0 {
        return Ok(target.to_string());
    }

    let mut new_string = String::new();
    if start >= 0 && end >= 0 {
        new_string.push_str(&target[start as usize..end as usize]);
    } else if start < 0 && end >= 0 {
        new_string.push_str(&target[(start + length) as usize..]);
        new_string.push_str(&target[..end as usize]);
    } else if start >= 0 && end < 0 {
        new_string.push_str(&target[start as usize..(end + length) as usize]);
    } else {
        new_string.push_str(&target[(start + length) as usize..(end + length) as usize]);
    }

    // Ok(new_string.to_string())

    let mut result = String::new();
    for (i, c) in new_string.chars().enumerate() {
        if i % (step as usize) == 0 {
            result.push(c);
        }
    }

    Ok(result)
}

#[pyfunction]
pub fn qubit_selector_rust(num_qubits: i32, degree: Option<QubitDegree>) -> PyResult<(i32, i32)> {
    let full_subsystem: Vec<i32> = (0..num_qubits).collect();

    let item_range: (i32, i32) = match degree {
        Some(QubitDegree::Single(d)) => {
            if d > num_qubits {
                return Err(
                    PyValueError::new_err(
                        format!(
                            "The subsystem A includes {} qubits beyond {} which the wave function has.",
                            d,
                            num_qubits
                        )
                    )
                );
            } else if d < 0 {
                return Err(
                    PyValueError::new_err(
                        "The number of qubits of subsystem A has to be a natural number."
                    )
                );
            }

            let _subsystem: Vec<i32> = full_subsystem
                .iter()
                .skip((num_qubits - d) as usize)
                .copied()
                .collect::<Vec<i32>>();
            (num_qubits - d, num_qubits)
        }
        Some(QubitDegree::Pair(start, end)) => {
            let mut raw_values: Vec<i32> = Vec::new();
            raw_values.push(start);
            raw_values.push(end);
            let mapped_values = raw_values.iter().map(|d: &i32| {
                if d != &num_qubits { (d+num_qubits) % num_qubits } else { num_qubits }
            });

            let vec_parsed: Vec<i32> = mapped_values.collect::<Vec<i32>>();
            let tmp: (i32, i32) = (
                *vec_parsed.iter().min().unwrap(),
                *vec_parsed.iter().max().unwrap(),
            );
            let _subsystem: Vec<i32> = full_subsystem
                .iter()
                .skip(tmp.0 as usize)
                .take((tmp.1 - tmp.0) as usize)
                .copied()
                .collect::<Vec<i32>>();
            tmp
        }
        None => { (0, num_qubits) }
    };

    assert!(item_range.1 >= item_range.0);
    Ok(item_range)
}

#[allow(dead_code)]
pub fn construct_test() {
    // Example usage
    let qubit_select_target: Vec<Option<QubitDegree>> = vec![
        Some(QubitDegree::Single(0)),
        None,
        Some(QubitDegree::Pair(0, 3)),
        Some(QubitDegree::Single(3)),
        Some(QubitDegree::Single(4)),
        Some(QubitDegree::Pair(4, 6)),
        Some(QubitDegree::Single(6)),
        Some(QubitDegree::Pair(7, 3)),
        Some(QubitDegree::Single(8))
    ];
    let num_qubits = 8;

    for degree in qubit_select_target.iter() {
        match degree {
            None => {
                println!("| Input qubits range: None");
            }
            Some(QubitDegree::Single(d)) => {
                println!("| Input qubits range: {}", d);
            }
            Some(QubitDegree::Pair(start, end)) => {
                println!("| Inputqubits range: {} to {}", start, end);
            }
        }
        match qubit_selector_rust(num_qubits, degree.clone()) {
            Ok(item_range) => {
                let (start, end) = item_range;
                println!("| Selected qubits range: {} to {}", start, end);
            }
            Err(err) => {
                eprintln!("Error: {}", err);
            }
        };
    }
}
