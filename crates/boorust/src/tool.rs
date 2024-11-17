extern crate pyo3;

use dashmap::DashMap;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use rand::seq::SliceRandom;
use rand::thread_rng;
use rand::Rng;
use rayon::prelude::*;
use std::collections::HashMap;
use std::sync::Arc;

fn generate_bits(num: usize, bits: Option<Arc<Vec<String>>>) -> Arc<Vec<String>> {
    let bits = bits.unwrap_or_else(|| Arc::new(vec![String::new()]));

    if num == 0 {
        return bits;
    }

    let new_bits: Vec<String> = bits
        .iter()
        .flat_map(|bit| vec![format!("0{}", bit), format!("1{}", bit)])
        .collect();

    generate_bits(num - 1, Some(Arc::new(new_bits)))
}

#[pyfunction]
#[pyo3(signature = (bitlen, num=None))]
pub fn make_two_bit_str_32(bitlen: usize, num: Option<usize>) -> PyResult<Vec<String>> {
    const ULTMAX: usize = 31;
    let mut is_less_than_16 = false;
    let mut less_slice = 0;

    let (logged_num, real_num) = match num {
        None => (ULTMAX as f64, 2_usize.pow(ULTMAX as u32)),
        Some(n) => {
            if n < 16 {
                is_less_than_16 = true;
                less_slice = n;
                (4 as f64, 16)
            } else {
                let logged = (n as f64).log2();
                (logged, n)
            }
        }
    };

    if logged_num > ULTMAX as f64 {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
            "num should be less than {} for safety reasons.",
            2_usize.pow(ULTMAX as u32)
        )));
    }

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

    let generate_bits =
        |num| Arc::try_unwrap(generate_bits(num, None)).unwrap_or_else(|arc| (*arc).clone());

    if bitlen <= logged_num as usize {
        let mut result = generate_bits(bitlen);
        if is_less_than_16 {
            result.shuffle(&mut thread_rng());
            return Ok(result[..less_slice].to_vec());
        }
        return Ok(result);
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

    fn filler_h_or_e(ff: &str, item: &str) -> String {
        if rand::thread_rng().gen::<bool>() {
            format!("{}{}", ff, item)
        } else {
            format!("{}{}", item, ff)
        }
    }

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
                let mut rng = rand::thread_rng();
                let rand_item = &raw_content[rng.gen_range(0..len_raw_content)];
                filler_h_or_e(rand_item, item)
            })
            .collect();
        less_bitlen -= logged_num as usize;
    }

    if less_bitlen == 0 {
        if is_less_than_16 {
            return Ok(num_fulfill_content[..less_slice].to_vec());
        }
        return Ok(num_fulfill_content);
    }

    let remain_fillers = generate_bits(less_bitlen);
    let len_remain_fillers = remain_fillers.len();

    let mut result: Vec<String> = num_fulfill_content
        .par_iter()
        .map(|item| {
            let mut rng = rand::thread_rng();
            let filler = &remain_fillers[rng.gen_range(0..len_remain_fillers)];
            filler_h_or_e(filler, item)
        })
        .collect();

    if is_less_than_16 {
        result.shuffle(&mut thread_rng());
        return Ok(result[..less_slice].to_vec());
    }
    Ok(result)
}

#[pyfunction]
#[pyo3(signature = (num))]
pub fn make_two_bit_str_unlimit(num: usize) -> Vec<String> {
    Arc::try_unwrap(generate_bits(num, None)).unwrap_or_else(|arc| (*arc).clone())
}

#[pyfunction]
#[pyo3(signature = (n_a, shot_per_case, bitstring_num=None))]
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

    bitstring_cases.iter().for_each(|case| {
        result.insert(case.clone(), shot_per_case);
    });

    // Convert DashMap to HashMap for return
    Ok(result.into_iter().collect())
}
