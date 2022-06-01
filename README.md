# Qurry 🍛 - The Measuring Tool for Renyi Entropy, Loschmidt Echo, and Magnetization Squared, The Library of Some Common Cases

This is a tool to measure the Renyi entropy, Loschmidt Echo, and Magnetization Squared of given wave function. Running on **IBM Qiskit** with the function from constructing experiment object to pending the jobs to IBMQ automatically.

---

## Configurate Environment

- **`Python 3.9.7+` installed by Anaconda**
  - on
    - **Ubuntu 20.04 LTS/18.04 LTS** on `x86_64` **(recommended)**
    - **Ubuntu 20.04 LTS/18.04 LTS on Windows 10/11 WSL2** on `x86_64` **(recommended)**
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

### `qurmagsq` - The Magnetization Squared

- Magnetization Squared

### `qurstrop` - The String Operators

- String Operators
  - Used in:
    **Crossing a topological phase transition with a quantum computer** - Smith, Adam and Jobst, Bernhard and Green, Andrew G. and Pollmann, Frank, [PhysRevResearch.4.L022020](https://link.aps.org/doi/10.1103/PhysRevResearch.4.L022020)

---

## The Library of Some Common Case & Other tools

### `case`

Some examples for the experiments.

- Trivial Paramagenet
- cat (as known as GHZ)
- Topological Paramagnet
  - From:
    **Measurement of the Entanglement Spectrum of a Symmetry-Protected Topological State Using the IBM Quantum Computer** - Kenny Choo, Curt W. von Keyserlingk, Nicolas Regnault, and Titus Neupert, [PhysRevLett.121.086808](https://doi.org/10.1103/PhysRevLett.121.086808)

- More wait for adding...

### `tool`

- `command`
  - `auto_cmd`: Use command in anywhere, no matter it's in `.ipynb` or '.py'.
  - `pytorchCUDACheck`: Via pytorch to check Nvidia CUDA available.

- `configuration`
  - `Configuration`: Set the default parameters dictionary for multiple experiment.

- `datasaving`
  - `argset`: A python `dict` with attributes of each parameters like a javascript `object`.

- `draw`
  - `yLimDecider`: Give the `ylim` of the plot.
  - `drawEntropyPlot`: Draw the figure of the result from entropy measuring with its time evolution as x-axis.
  - `drawEntropyErrorBar`: Draw the figure of the error analysis from entropy measuring with multile waves as x-axis.
  - `drawEntropyErrorPlot`: Draw the figure of the error analysis from entropy measuring with stand deviations of each wave as y-axis.
