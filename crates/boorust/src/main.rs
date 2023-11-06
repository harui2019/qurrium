mod randomized;

extern crate serde;
extern crate serde_json;
extern crate rayon;

use std::collections::HashMap;
use std::time::Instant;
use std::fs;
use rayon::prelude::*;

use randomized::randomized::{ ensemble_cell_rust, purity_cell_rust };
use randomized::construct::construct_test;

/// ensemble_cell x 10000000:  7.209437532 sec
/// purity_cell: 8.892290667s

fn ensemble_cell_test() {
    let s_i = "1010101010101010";
    let s_i_meas = 100;
    let s_j = "0101010101010101";
    let s_j_meas = 100;
    let a_num = 12;
    let shots = 1000;

    let ensemble_cell_result = ensemble_cell_rust(s_i, s_i_meas, s_j, s_j_meas, a_num, shots);
    println!("| ensemble_cell x 1: {}", ensemble_cell_result);
}

fn main() {
    let is_ensemble_cell_test = false;
    let is_all_data_hashmap_iter = false;
    let is_all_data_vector_iter = false;

    if is_ensemble_cell_test {
        ensemble_cell_test();
    }

    // Iterate through the JSON files in a directory
    let route_file_as_string = fs
        ::read_to_string("../largedummy-1.json")
        .expect("Failed to read directory");
    let all_data_hashmap: HashMap<String, HashMap<String, i32>> = serde_json
        ::from_str(&route_file_as_string)
        .unwrap();
    let all_data_vector: Vec<(&String, &HashMap<String, i32>)> = all_data_hashmap.iter().collect();

    if is_all_data_hashmap_iter {
        let start = Instant::now();
        let mut purity_loader_1: HashMap<i32, f64> = HashMap::new();
        for (identifier, data) in all_data_hashmap.iter() {
            let result = purity_cell_rust(identifier.parse::<i32>().unwrap(), data.clone(), (0, 8), 8);
            purity_loader_1.insert(result.0, result.1);
        }
        let duration = start.elapsed();
        println!("| all_data_hashmap is: {:?}", duration);

        let start = Instant::now();
        let mut purity_loader_1: HashMap<i32, f64> = HashMap::new();
        for (identifier, data) in all_data_vector.iter() {
            let result = purity_cell_rust(identifier.parse::<i32>().unwrap(), data.clone().clone(), (0, 8), 8);
            purity_loader_1.insert(result.0, result.1);
        }
        let duration = start.elapsed();
        println!("| all_data_vector is: {:?}", duration);
    }

    if is_all_data_vector_iter {
        let start_2 = Instant::now();
        let mut vec: Vec<f64> = vec![];

        for _ in 0..100 {
            let mut purity_loader_2: HashMap<i32, f64> = HashMap::new();
            let result_vec = all_data_vector.par_iter().map(|(identifier, data)| {
                let result = purity_cell_rust(identifier.parse::<i32>().unwrap(), data.clone().clone(), (0, 8), 8);
                return result;
            });
            result_vec
                .collect::<Vec<(i32, f64)>>()
                .iter()
                .for_each(|(idx, purity_cell)| {
                    purity_loader_2.insert(*idx, *purity_cell);
                });
            let purity = purity_loader_2.values().sum::<f64>() / (purity_loader_2.len() as f64);
            vec.push(purity);
        }

        let duration_2 = start_2.elapsed();
        println!("| vec of purity_loader_1: {:?}", vec);
        println!("| all_data_hashmap.par_iter is: {:?}", duration_2);
    }

    // let qubit_select_target: Vec<QubitDegree>> = vec![
    //     QubitDegree(0), None, (0, 3), 3, 4, 5, 6, 7, 8];

    // qubit_selector(9, qubit_select_target);
    construct_test();
}
