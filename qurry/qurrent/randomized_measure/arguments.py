"""
===========================================================
EntropyMeasureRandomized - Arguments
(:mod:`qurry.qurrent.randomized_measure.arguments`)
===========================================================

"""

from typing import Optional
from dataclasses import dataclass

from ...qurrium.experiment import ArgumentsPrototype
from ...declare import BasicArgs
from ...tools import DEFAULT_POOL_SIZE


@dataclass(frozen=True)
class EntropyMeasureRandomizedArguments(ArgumentsPrototype):
    """Arguments for the experiment."""

    exp_name: str = "exps"
    """The name of the experiment.
    Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
    This name is also used for creating a folder to store the exports.
    Defaults to `'experiment'`."""
    times: int = 100
    """The number of random unitary operator. 
    It will denote as `N_U` in the experiment name."""
    measure: Optional[tuple[int, int]] = None
    """The measure range."""
    unitary_loc: Optional[tuple[int, int]] = None
    """The range of the unitary operator."""
    workers_num: int = DEFAULT_POOL_SIZE
    """The number of workers for multiprocessing."""


class EntropyMeasureRandomizedMeasureArgs(BasicArgs):
    """Output arguments for :meth:`output`."""

    exp_name: str
    """The name of the experiment.
    Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
    This name is also used for creating a folder to store the exports.
    Defaults to `'experiment'`."""
    times: int
    """The number of random unitary operator. 
    It will denote as `N_U` in the experiment name."""
    measure: Optional[tuple[int, int]]
    """The measure range."""
    unitary_loc: Optional[tuple[int, int]]
    """The range of the unitary operator."""
    workers_num: int
    """The number of workers for multiprocessing."""


SHORT_NAME = "qurrent_randomized"
