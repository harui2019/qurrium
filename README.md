# Qurry 🍛 - The Quantum Experiment Manager for Qiskit and The Measuring Tool for Renyi Entropy, Wave Function Overlap, and More

This is a tool to measure the Renyi entropy, Wave Function Overlap, and Magnetization Squared of given wave function. Running on **IBM Qiskit** with the function from constructing experiment object to pending the jobs to IBMQ automatically.

---

## Acknowledgments

_It's a great thanks for
[National Chengchi University](https://www.nccu.edu.tw/), [NSTC-Quantum Virtual Machine project](https://www.nstc.gov.tw/),
and [National Center for Theoretical Sciences, Physics Division](https://phys.ncts.ntu.edu.tw/) located [National Taiwan University](https://www.ntu.edu.tw/)
, which funded the development of this tool during the author [@harui2019](https://github.com/harui2019/) worked at this institution as Research Assistiant, and i also a great thanks for [IBM Quantum Hub at National Taiwan University](https://quantum.ntu.edu.tw/) providing the access right of [IBM Quantum](https://quantum-computing.ibm.com/), let us can fully test this tool and execute our experiments._

<p><img src="https://raw.githubusercontent.com/harui2019/harui2019/main/docs/image/logo/NCCU_Physics_Logo.png" href="https://phys.nccu.edu.tw/" alt="National Chengchi University" width="500" ></p>

<p><img src="https://raw.githubusercontent.com/harui2019/harui2019/main/docs/image/logo/NSTC_Logo.png" href="https://www.nstc.gov.tw/" alt="NSTC" width="500" ></p>

<p><img src="https://raw.githubusercontent.com/harui2019/harui2019/main/docs/image/logo/NCTS_Phys_Logo.png" href="https://phys.ncts.ntu.edu.tw/" alt="National Center for Theoretical Sciences, Physics Division" width="500" ></p>

<p><img src="https://raw.githubusercontent.com/harui2019/harui2019/main/docs/image/logo/NTU_IBM_Q_Hub_Logo.png" href="https://quantum.ntu.edu.tw/" alt="IBM Quantum Hub at National Taiwan University" width="500"></p>

---

## Environment

![Available Python Version](https://img.shields.io/badge/Python-3.9_|_3.10_|_3.11_|_3.12-blue?logo=python&logoColor=white)

![Available System](https://img.shields.io/badge/Ubuntu-18.04+-purple?logo=Ubuntu&logoColor=white) ![Available System](https://img.shields.io/badge/Ubuntu_on_WSL-18.04+-purple?logo=Ubuntu&logoColor=white)

![Available System](https://img.shields.io/badge/Windows-10_|_11-purple?logo=Windows&logoColor=white) ![Available System](https://img.shields.io/badge/MacOS-11+-purple?logo=Apple&logoColor=white)

- **Ubuntu 18.04+ LTS (All ManyLinux 2014 compatible distro)**
  - on `x86_64` **(recommended)**
  - on `x86_64` Windows 10/11 WSL2 **(recommended)**
  - on `aarch64`
  - We strongly recommend to use Linux based system, due to Python multiprocessing may exist some unknown issue on Windows and the GPU acceleration of `Qiskit`, `qiskit-aer-gpu` only works with Nvidia CUDA on Linux.
- **Windows 10/11**
  - on `x86_64`
- **MacOS 11+**
  - on `aarch64 (Apple Silicon, M1/M2/M3 chips)` **(recommended)**
  - on `x86_64 (Intel chips)`

- with required modules:
  - `qiskit`, `qiskit-aer`, `tqdm`, `requests`
- with optional modules:
  - `qiskit-aer-gpu`: when use Linux
  - `qiskit-ibm-provider`: when use IBM Quantum
  - `qiskit-ibmq-provider`: when use IBM Quantum, the deprecated version of `qiskit-ibm-provider`

---

## Install

### By PyPI

Not available now, but coming soon

### By TestPyPI

```bash
pip install qiskit qiskit-aer tqdm requests 
# the installation from testPyPI can' t find these dependencies
pip install -i https://test.pypi.org/simple/ qurry
```

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

### `qurrech` - The Wave Function Overlap Measurement

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
