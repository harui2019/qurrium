extern crate pyo3;
extern crate rayon;

use pyo3::prelude::*;
use rayon::iter::IntoParallelRefIterator;
use rayon::prelude::*;
use std::collections::HashMap;
use std::panic;
use std::time::Instant;

use crate::randomized::construct::{qubit_selector_rust, QubitDegree};
use crate::randomized::randomized::purity_cell_rust;

#[pyfunction]
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
    let actual_deg: (i32, i32) = qubit_selector_rust(allsystems_size, degree).unwrap();
    let subsystems_size: i32 = actual_deg.1 - actual_deg.0;

    let bitstring_range: (i32, i32) = actual_deg.clone();

    // Check if the bitstring_range is valid and panic if not
    let mut bitstring_check: HashMap<&str, bool> = HashMap::new();
    bitstring_check.insert("b > a", bitstring_range.1 > bitstring_range.0);
    bitstring_check.insert("a >= -allsystemSize", bitstring_range.0 >= -allsystems_size);
    bitstring_check.insert("b <= allsystemSize", bitstring_range.1 <= allsystems_size);
    bitstring_check.insert(
        "b-a <= allsystemSize",
        bitstring_range.1 - bitstring_range.0 <= allsystems_size,
    );

    let mut error_message: String = format!(
        "Invalid 'bitStringRange = {:?} for allsystemSize = {}. Available range 'bitStringRange = [a, b)' should be",
        bitstring_range,
        allsystems_size
    );
    let invalid_ranges: Vec<String> = bitstring_check
        .iter()
        .filter(|(_, &v)| !v)
        .map(|(k, _): (&&str, _)| format!(" {}", k))
        .collect();
    error_message.push_str(&invalid_ranges.join(";"));
    if !bitstring_check.values().all(|&value: &bool| value) {
        panic!("{}", error_message);
    }

    let actual_measure: (i32, i32) = match measure {
        Some(m) => {
            let tmp: (i32, i32) = m.clone();
            tmp
        }
        None => {
            let tmp: PyResult<(i32, i32)> = qubit_selector_rust(
                allsystems_size,
                Some(QubitDegree::Pair(actual_deg.0, actual_deg.1)),
            );
            match tmp {
                Ok(val) => val,
                Err(e) => panic!("Error: {}", e),
            }
        }
    };

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
