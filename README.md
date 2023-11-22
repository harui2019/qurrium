# Qurry 🍛 - The Quantum Experiment Manager for Qiskit and The Measuring Tool for Renyi Entropy, Wave Function Overlap, and More

This is a tool to measure the Renyi entropy, Loschmidt Echo, and Magnetization Squared of given wave function. Running on **IBM Qiskit** with the function from constructing experiment object to pending the jobs to IBMQ automatically.

---

## Acknowledgments

_It's a great thanks for
[National Chengchi University](https://www.nccu.edu.tw/), [NSTC-Quantum Virtual Machine project](https://www.nstc.gov.tw/),
and [National Center for Theoretical Sciences, Physics Division](https://phys.ncts.ntu.edu.tw/) located [National Taiwan University](https://www.ntu.edu.tw/)
, which funded the development of this tool during the author [@harui2019](https://github.com/harui2019/) worked at this institution as Research Assistiant, and i also a great thanks for [IBM Quantum Hub at National Taiwan University](https://quantum.ntu.edu.tw/) providing the access right of [IBM Quantum](https://quantum-computing.ibm.com/), let us can fully test this tool and execute our experiments._

<p><img src="./docs/image/logo/NCCU_Physics_Logo.png" alt="National Chengchi University" width="500" ></p>

<p><img src="./docs/image/logo/NSTC_Logo.png" alt="NSTC" width="500" ></p>

<p><img src="./docs/image/logo/NCTS_Phys_Logo.png" alt="National Center for Theoretical Sciences, Physics Division" width="500" ></p>

<p><img src="./docs/image/logo/NTU_IBM_Q_Hub_Logo.png" alt="IBM Quantum Hub at National Taiwan University" width="500"></p>

---

## Environment

![Available Python Version](https://img.shields.io/badge/Python-3.9_|_3.10_|_3.11-blue?logo=python&logoColor=white)
![Available System](https://img.shields.io/badge/Ubuntu-18.04+-purple?logo=Ubuntu&logoColor=white) ![Available System](https://img.shields.io/badge/Ubuntu_on_Windows_WSL-18.04+-purple?logo=Ubuntu&logoColor=white)

 <!-- ![Available System](https://img.shields.io/badge/Windows-10_|_11-purple?logo=Windows&logoColor=white) -->

- **Recommended `Python 3.9.7+` installed by Anaconda**

  - on

    - **Ubuntu 18.04+ LTS** on `x86_64` **(recommended)**
    - **Ubuntu 18.04+ LTS on Windows 10/11 WSL2** on `x86_64` **(recommended)**
      - We strongly recommend to use Linux based system, due to the paralell calculation function only works on Unix-like currently and the GPU acceleration of `Qiskit`, `qiskit-aer-gpu` only works with Nvidia CUDA on Linux.
    - ~~**Windows 10/11** on `x86_64`~~
      - currently with issues on `multiprocessing` module on Windows.
    - **MacOS 12+** on **`arm64 (Apple Silicon, M1 chips)`**
    - **MacOS 12+** on **`x86_64 (Intel chips)`**
      - Maybe some unknown python issues exist.

  - with required modules:

    - `qiskit`

  - with optional modules:
    - `qiskit-aer-gpu`: when use Linux

---

## Install

### Maually by Git

**This method is installed from source**, since we introduce Rust, **it will require "Rust complier" you need to install first.**

You can install rust quickly by the following command:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Then, you can install `qurry` by the following command:

```bash
git clone https://github.com/harui2019/qurry.git --recursive
cd qurry
pip install -e .
```

We have pytest for testing, you can run the following command to test:

```bash
pytest
```

After you finish the installation and want to comfirm the installation.

### By PyPI

Not available now, but coming soon

---

## Measurement

### `qurrent` - The Renyi Entropy Measurement

The main function to measure the entropy.
The following is the methods used to measure.

- Hadamard Test

  - Used in:
    **Entanglement spectroscopy on a quantum computer** - Sonika Johri, Damian S. Steiger, and Matthias Troyer, [PhysRevB.96.195136](https://doi.org/10.1103/PhysRevB.96.195136)

- Haar Randomized Measure
  - From:
    **Statistical correlations between locally randomized measurements: A toolbox for probing entanglement in many-body quantum states** - A. Elben, B. Vermersch, C. F. Roos, and P. Zoller, [PhysRevA.99.052323](https://doi.org/10.1103/PhysRevA.99.052323)

### `qurrech` - The Loschmidt Echo Measurement

It's similar to `qurrent`.

- Hadamard Test

  - Used in:
    **Entanglement spectroscopy on a quantum computer** - Sonika Johri, Damian S. Steiger, and Matthias Troyer, [PhysRevB.96.195136](https://doi.org/10.1103/PhysRevB.96.195136)

- Haar Randomized Measure
  - From:
    **Statistical correlations between locally randomized measurements: A toolbox for probing entanglement in many-body quantum states** - A. Elben, B. Vermersch, C. F. Roos, and P. Zoller, [PhysRevA.99.052323](https://doi.org/10.1103/PhysRevA.99.052323)

<!-- ### `qurmagsq` - The Magnetization Squared

- Magnetization Squared

### `qurstrop` - The String Operators

- String Operators
  - Used in:
    **Crossing a topological phase transition with a quantum computer** - Smith, Adam and Jobst, Bernhard and Green, Andrew G. and Pollmann, Frank, [PhysRevResearch.4.L022020](https://link.aps.org/doi/10.1103/PhysRevResearch.4.L022020) -->

- More wait for adding...
