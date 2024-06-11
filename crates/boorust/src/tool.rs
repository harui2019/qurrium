extern crate pyo3;

use dashmap::DashMap;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use rand::rngs::StdRng;
use rand::{Rng, SeedableRng};
use rayon::prelude::*;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};

fn generate_bits(num: usize, bits: Option<Arc<Vec<String>>>) -> Arc<Vec<String>> {
    let bits = bits.unwrap_or_else(|| Arc::new(vec![String::new()]));

    if num == 0 {
        return bits;
    }

    let new_bits: Vec<String> = bits
        .par_iter()
        .flat_map(|bit| vec![format!("0{}", bit), format!("1{}", bit)])
        .collect();

    generate_bits(num - 1, Some(Arc::new(new_bits)))
}

#[pyfunction]
pub fn make_two_bit_str_32(bitlen: usize, num: Option<usize>) -> PyResult<Vec<String>> {
    const ULTMX: usize = 31;

    let (logged_num, real_num) = match num {
        None => (ULTMX as f64, 2_usize.pow(ULTMX as u32)),
        Some(n) => {
            let logged = (n as f64).log2();
            (logged, n)
        }
    };

    if logged_num > ULTMX as f64 {
        return Err(PyErr::new::<PyValueError, _>(format!(
            "num should be less than {} for safety reasons.",
            2_usize.pow(ULTMX as u32)
        )));
    }

    let generate_bits =
        |num| Arc::try_unwrap(generate_bits(num, None)).unwrap_or_else(|arc| (*arc).clone());

    if bitlen <= logged_num as usize {
        return Ok(generate_bits(bitlen));
    }

    let less_bitlen = bitlen - logged_num as usize - 1;
    let raw_content = generate_bits(logged_num as usize);
    let len_raw_content = raw_content.len();

    assert_eq!(2_usize.pow(logged_num as u32), len_raw_content);
    assert!(2 * len_raw_content >= real_num && real_num >= len_raw_content);

    let mut rng = rand::thread_rng();
    let first_filler = if rng.gen::<bool>() {
        vec!["0", "1"]
    } else {
        vec!["1", "0"]
    };

    let rng = Arc::new(Mutex::new(StdRng::from_entropy()));

    let filler_h_or_e = |ff: &str, item: &str| -> String {
        let rng = Arc::clone(&rng);
        let mut rng = rng.lock().unwrap();
        if rng.gen::<bool>() {
            format!("{}{}", ff, item)
        } else {
            format!("{}{}", item, ff)
        }
    };

    let mut num_fulfill_content: Vec<String> = raw_content
        .par_iter()
        .map(|item| filler_h_or_e(first_filler[0], item))
        .collect();

    let remaining_items: Vec<String> = raw_content[..(real_num - len_raw_content)]
        .par_iter()
        .map(|item| filler_h_or_e(first_filler[1], item))
        .collect();

    num_fulfill_content.extend(remaining_items);

    let mut less_bitlen = less_bitlen;
    while less_bitlen >= logged_num as usize {
        num_fulfill_content = num_fulfill_content
            .par_iter()
            .map(|item| {
                let rng = Arc::clone(&rng);
                let mut rng2 = rng.lock().unwrap();
                let rand_item = &raw_content[rng2.gen_range(0..len_raw_content)];
                filler_h_or_e(rand_item, item)
            })
            .collect();
        less_bitlen -= logged_num as usize;
    }

    if less_bitlen == 0 {
        return Ok(num_fulfill_content);
    }

    let remain_fillers = generate_bits(less_bitlen);
    let len_remain_fillers = remain_fillers.len();

    let result: Vec<String> = num_fulfill_content
        .par_iter()
        .map(|item| {
            let rng = Arc::clone(&rng);
            let mut rng2 = rng.lock().unwrap();
            let filler = &remain_fillers[rng2.gen_range(0..len_remain_fillers)];
            filler_h_or_e(filler, item)
        })
        .collect();

    Ok(result)
}

#[pyfunction]
pub fn make_two_bit_str_unlimit(num: usize) -> Vec<String> {
    Arc::try_unwrap(generate_bits(num, None)).unwrap_or_else(|arc| (*arc).clone())
}

#[pyfunction]
pub fn make_dummy_case_32(
    n_a: usize,
    shot_per_case: usize,
    bitstring_num: Option<usize>,
) -> PyResult<HashMap<String, usize>> {
    let raw_bitstring_cases = make_two_bit_str_32(n_a, bitstring_num);
    let bitstring_cases = match raw_bitstring_cases {
        Ok(cases) => cases,
        Err(_) => {
            return Err(PyErr::new::<PyValueError, _>(
                "Failed to generate bitstring cases",
            ))
        }
    };
    let result = DashMap::new();

    bitstring_cases.par_iter().for_each(|case| {
        result.insert(case.clone(), shot_per_case);
    });

    // Convert DashMap to HashMap for return
    Ok(result.into_iter().collect())
}
