# Qurrent - Entangled Entropy Measure Tool

This is a tool to measure the Renyi entropy of given wave function. Running on **IBM Qiskit** with the function from constructing experiment object to pending the jobs to IBMQ automatically.

## `qurrent`

The main function to measure the entropy.
The following is the methods used to measure.

- Hadamard Test
  - Used in:
    **Entanglement spectroscopy on a quantum computer** - Sonika Johri, Damian S. Steiger, and Matthias Troyer, [PhysRevB.96.195136](https://doi.org/10.1103/PhysRevB.96.195136)

- Haar Randomized Measure
  - From:
    **Statistical correlations between locally randomized measurements: A toolbox for probing entanglement in many-body quantum states** - A. Elben, B. Vermersch, C. F. Roos, and P. Zoller, [PhysRevA.99.052323](https://doi.org/10.1103/PhysRevA.99.052323)

## `case`

Some examples for the experiments.

- Trivial Paramagenet
- cat (as known as GHZ)
- Topological Paramagnet
  - From:
    **Measurement of the Entanglement Spectrum of a Symmetry-Protected Topological State Using the IBM Quantum Computer** - Kenny Choo, Curt W. von Keyserlingk, Nicolas Regnault, and Titus Neupert, [PhysRevLett.121.086808](https://doi.org/10.1103/PhysRevLett.121.086808)

- More wait for adding...

## `tool`

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
