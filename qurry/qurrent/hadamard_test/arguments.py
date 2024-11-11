"""
===========================================================
EntropyMeasureHadamard - Arguments
(:mod:`qurry.qurrent.hadamard_test.arguments`)
===========================================================

"""

from typing import Optional, Union
from collections.abc import Hashable
from dataclasses import dataclass

from qiskit import QuantumCircuit

from ...qurrium.experiment import ArgumentsPrototype
from ...declare import BasicArgs, OutputArgs, AnalyzeArgs


@dataclass(frozen=True)
class EntropyMeasureHadamardArguments(ArgumentsPrototype):
    """Arguments for the experiment."""

    exp_name: str = "exps"
    """The name of the experiment.
    Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
    This name is also used for creating a folder to store the exports.
    Defaults to `'experiment'`."""
    degree: Optional[tuple[int, int]] = None
    """The degree range."""


class EntropyMeasureHadamardMeasureArgs(BasicArgs, total=False):
    """Output arguments for :meth:`output`."""

    wave: Optional[Union[QuantumCircuit, Hashable]]
    """The key or the circuit to execute."""
    degree: Optional[Union[int, tuple[int, int]]]
    """The degree range."""


class EntropyMeasureHadamardOutputArgs(OutputArgs):
    """Output arguments for :meth:`output`."""

    degree: Optional[Union[int, tuple[int, int]]]
    """The degree range."""


class EntropyMeasureHadamardAnalyzeArgs(AnalyzeArgs, total=False):
    """The input of the analyze method.

    The post-processing of Hadamard test does not need any input.
    """


SHORT_NAME = "qurrent_hadamard"
