# Qurry 🍛 - The Quantum Experiment Manager for Qiskit and The Measuring Tool for Renyi Entropy, Loschmidt Echo, and More


This is a tool to measure the Renyi entropy, Loschmidt Echo, and Magnetization Squared of given wave function. Running on **IBM Qiskit** with the function from constructing experiment object to pending the jobs to IBMQ automatically.

---

## Acknowledgments

_It's a great thanks for [National Center for Theoretical Sciences, Physics Division](https://phys.ncts.ntu.edu.tw/) located [National Taiwan University](https://www.ntu.edu.tw/), which funded the development of this tool during the author [@harui2019](https://github.com/harui2019/) worked at this institution as Research Assistiant, and i also a great thanks for [IBM Quantum Hub at National Taiwan University](https://quantum.ntu.edu.tw/) providing the access right of [IBM Quantum](https://quantum-computing.ibm.com/), let us can fully test this tool and execute our experiments._

<p><img src="https://phys.ncts.ntu.edu.tw/uploads/site/site_logo/607fe6dd1d41c87eae000023/logo橘_網頁2.png" alt="National Center for Theoretical Sciences, Physics Division" width="500" ></p>
<p><img src="https://quantum.ntu.edu.tw/wp-content/uploads/elementor/thumbs/NTU-IBMQ_LOGO1-p9ym8ap0ujw64l3clhzokyfcks6gk8jqq8h148kjk6.png" alt="IBM Quantum Hub at National Taiwan University" width="500"></p>

---

## Environment

![Available Python Version](https://img.shields.io/badge/Python-3.9_|_3.10_|_3.11-blue?logo=python&logoColor=white)

![Available System](https://img.shields.io/badge/Ubuntu-18.04+-purple?logo=Ubuntu&logoColor=white) ![Available System](https://img.shields.io/badge/Ubuntu_on_Windows_WSL-18.04+-purple?logo=Ubuntu&logoColor=white) ![Available System](https://img.shields.io/badge/Windows-10_|_11-purple?logo=Windows&logoColor=white)

- **Recommended `Python 3.9.7+` installed by Anaconda**
  - on
    - **Ubuntu 18.04+ LTS** on `x86_64` **(recommended)**
    - **Ubuntu 18.04+ LTS on Windows 10/11 WSL2** on `x86_64` **(recommended)**
      - We recommend to use Linux based system, due to the GPU acceleration of `Qiskit`, `qiskit-aer-gpu` only works with Nvidia CUDA on Linux.
    - **Windows 10/11** on `x86_64`

  - currently with issues on
    - **MacOS 12 Monterey** on **`arm64 (Apple Silicon, M1 chips)`**
    - **MacOS 12 Monterey** on **`x86_64 (Intel chips)`**
      - Some python issues are not fixed and waiting to fix.

  - with required modules:
    - `qiskit`

  - with optional modules:
    - `qiskit-aer-gpu`: when use Linux
    - `torch`: when use Nvidia CUDA and checks availability on Linux.

---

## Install

### Maually by Git

```bash
git clone https://github.com/harui2019/qurry.git --recursive
cd qurry
pip install -e .
```

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