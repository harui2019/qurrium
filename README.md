# Qurry 🍛 - The python package for measuring quantum entanglement entropy and wave function overlap. 
## *The python package that makes the randomized measurement easy.*

The major function includes the measurement of quantum Renyi Entropy and Wave Function Overlap based on the randomized measurement protocol. 
When interfaced with **IBM Qiskit**, the package automates the workflow from creating experiment objects, job submission and recall and postprocessing.  
There are several additional features, such as measurement of magnetization and error mitigation. Please check them out!



![Available Python Version](https://img.shields.io/badge/Python-3.9_|_3.10_|_3.11_|_3.12-blue?logo=python&logoColor=white) [![Downloads](https://static.pepy.tech/badge/qurrium)](https://pepy.tech/project/qurrium)
![Available System](https://img.shields.io/badge/Ubuntu-18.04+-purple?logo=Ubuntu&logoColor=white) ![Available System](https://img.shields.io/badge/Ubuntu_on_WSL-18.04+-purple?logo=Ubuntu&logoColor=white)
![Available System](https://img.shields.io/badge/Windows-10_|_11-purple?logo=Windows&logoColor=white) ![Available System](https://img.shields.io/badge/MacOS-11+-purple?logo=Apple&logoColor=white)

## Installation

### By PyPI - Stable Release

- The package can be found in `pip list` as `qurrium-x.y.z`
- Pip downloads the most stable release, but not necessarily the latest version.

```bash
pip install qurrium
```

### By TestPyPI - Nightly Release

- This package can be found in `pip list` as `qurry-x.y.z.devW`
- This version includes new features and minor bug fixes, but may not be stable.

```bash
pip install qiskit tqdm requests
# the installation from testPyPI can' t find these dependencies
pip install -i https://test.pypi.org/simple/ qurry
```

### Maually by Git

**Qurry can be installed from source**. Since this package relies on Cython and Rust, **it requires "C complier" and "Rust complier" which you need to install first.**

To install rust,  run the following command:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Then install `qurry` by the following command:

```bash
git clone https://github.com/harui2019/qurry-preview.git --recursive
cd qurry
pip install -e .
```

#### Test Installation

`pytest` is used for testing. Simply run the following command after the installation:

```bash
pytest
```



---



## Environment

**Qurry currently <ins>SUPPORT qiskit 0.46.0+ and qiskit 1.0.0+</ins>, other lower versions are no longer available. 
The package has been tested on the following systems.**

- **Ubuntu 18.04+ LTS (All ManyLinux 2014 compatible distro)**
  - on `x86_64` **(recommended)**
  - on `x86_64` Windows 10/11 WSL2 **(recommended)**
  - on `aarch64`
  - We strongly recommend to use Linux based systems because Python multiprocessing may exist issues on Windows and the NVIDIA CUDA acceleration of `Qiskit`, `qiskit-aer-gpu` are supported only on Linux.
- **Windows 10/11**
  - on `x86_64`
- **MacOS 11+**

  - on `aarch64 (Apple Silicon, M1/M2/M3/M4 chips)`
  - on `x86_64 (Intel chips)`
  - 
**The depedent modules are as follows.**
- with required modules:
  - [`qiskit`](https://pypi.org/project/qiskit/), [`tqdm`](https://pypi.org/project/tqdm/), [`requests`](https://pypi.org/project/requests/)
- with optional modules:
  - `qiskit-aer`: The complete simulator package of `qiskit`
  - `qiskit-aer-gpu`: The gpu acceleration of `qiskit-aer` on Linux with Nvidia GPU
    - `qiskit-aer-gpu-cu11`:  A package for CUDA 11
  - `qiskit-ibm-runtime`: The API to access IBM Quantum Device
  - `qiskit-ibm-provider`: The API to access IBM Quantum Device, but will be deprecated soon.
  - `qiskit-ibmq-provider`: The API to access IBM Quantum Device, which has been deprecated.

---

## Measurement -- made randomized measurement easy. 

### `qurrent` - The Quantum Renyi Entropy Measurement

The major function of this module is to measure the quantum Renyi entropy to quantify entanglement.


### `qurrech` - The Wave Function Overlap Measurement
This module evaluates the overlap between any two given quantum states. 

In each of the modules, two methods are implemented to perform the measurements:
- Hadamard Test
  - Ref:
    **Entanglement spectroscopy on a quantum computer** - Sonika Johri, Damian S. Steiger, and Matthias Troyer, [PhysRevB.96.195136](https://doi.org/10.1103/PhysRevB.96.195136)

- Haar Randomized Measure
  - Ref:
    **Statistical correlations between locally randomized measurements: A toolbox for probing entanglement in many-body quantum states** - A. Elben, B. Vermersch, C. F. Roos, and P. Zoller, [PhysRevA.99.052323](https://doi.org/10.1103/PhysRevA.99.052323)




<!-- ### `qurmagsq` - The Magnetization Squared

- Magnetization Squared

### `qurstrop` - The String Operators

- String Operators
  - Used in:
    **Crossing a topological phase transition with a quantum computer** - Smith, Adam and Jobst, Bernhard and Green, Andrew G. and Pollmann, Frank, [PhysRevResearch.4.L022020](https://link.aps.org/doi/10.1103/PhysRevResearch.4.L022020) -->


---
## Citation

If you use this tool in your research, please cite the following paper in your publication:

```bibtex
@misc{chang2024probing,
  title         = {Probing entanglement dynamics and topological transitions on noisy intermediate-scale quantum computers},
  author        = {Huai-Chun Chang and Hsiu-Chuan Hsu and Yu-Cheng Lin},
  year          = {2024},
  eprint        = {2406.10159},
  archiveprefix = {arXiv},
  primaryclass  = {quant-ph},
  url           = {https://arxiv.org/abs/2406.10159}
}

```

---
## Acknowledgments

The authors acknowledge the support from [National Chengchi University](https://www.nccu.edu.tw/), [NSTC-Quantum Virtual Machine project](https://www.nstc.gov.tw/), [National Center for Theoretical Sciences (NCTS)](https://phys.ncts.ntu.edu.tw/).
and  [IBM Quantum Hub at National Taiwan University (NTU)](https://quantum.ntu.edu.tw/).  

Special thank to [IBM Quantum Hub at NTU](https://quantum.ntu.edu.tw/) for providing the access right of [IBM Quantum](https://quantum-computing.ibm.com/) that allows us to fully test the tool and execute our experiments.

The author [@harui2019](https://github.com/harui2019/) is grateful to the NTU hub of [NCTS](https://phys.ncts.ntu.edu.tw/) that supported him as a Research Assistiant in the early stage of the development.

<p><img src="https://raw.githubusercontent.com/harui2019/harui2019/main/docs/image/logo/NCCU_Physics_Logo.png" href="https://phys.nccu.edu.tw/" alt="National Chengchi University" width="400" ></p>

<p><img src="https://raw.githubusercontent.com/harui2019/harui2019/main/docs/image/logo/NSTC_Logo.png" href="https://www.nstc.gov.tw/" alt="NSTC" width="400" ></p>

<p><img src="https://raw.githubusercontent.com/harui2019/harui2019/main/docs/image/logo/NCTS_Phys_Logo.png" href="https://phys.ncts.ntu.edu.tw/" alt="National Center for Theoretical Sciences, Physics Division" width="400" ></p>

<p><img src="https://raw.githubusercontent.com/harui2019/harui2019/main/docs/image/logo/NTU_IBM_Q_Hub_Logo.png" href="https://quantum.ntu.edu.tw/" alt="IBM Quantum Hub at National Taiwan University" width="400"></p>

---
### Stay connected. More features coming soon...