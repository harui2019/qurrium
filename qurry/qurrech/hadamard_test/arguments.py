"""
===========================================================
EchoListenHadamard - Arguments
(:mod:`qurry.qurrech.randomized_measure.arguments`)
===========================================================

"""

from typing import Optional
from dataclasses import dataclass

from ...qurrium.experiment import ArgumentsPrototype
from ...declare import BasicArgs


@dataclass(frozen=True)
class EchoListenHadamardArguments(ArgumentsPrototype):
    """Arguments for the experiment."""

    exp_name: str = "exps"
    """The name of the experiment.
    Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
    This name is also used for creating a folder to store the exports.
    Defaults to `'experiment'`."""
    degree: Optional[tuple[int, int]] = None
    """The degree range."""


class EchoListenHadamardOutputArgs(BasicArgs):
    """Output arguments for :meth:`output`."""

    exp_name: str
    """The name of the experiment.
    Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
    This name is also used for creating a folder to store the exports.
    Defaults to `'experiment'`."""
    degree: Optional[tuple[int, int]]
    """The degree range."""


SHORT_NAME = "qurrech_hadamard"
