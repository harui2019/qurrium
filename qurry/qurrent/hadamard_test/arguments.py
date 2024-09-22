"""
===========================================================
EntropyMeasureHadamard - Arguments
(:mod:`qurry.qurrent.hadamard_test.arguments`)
===========================================================

"""

from typing import Optional
from dataclasses import dataclass

from ...qurrium.experiment import ArgumentsPrototype
from ...declare import BasicOutputArgs


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


class EntropyMeasureHadamardOutputArgs(BasicOutputArgs):
    """Output arguments for :meth:`output`."""

    exp_name: str
    """The name of the experiment.
    Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
    This name is also used for creating a folder to store the exports.
    Defaults to `'experiment'`."""
    degree: Optional[tuple[int, int]]
    """The degree range."""


SHORT_NAME = "qurrent_hadamard"
