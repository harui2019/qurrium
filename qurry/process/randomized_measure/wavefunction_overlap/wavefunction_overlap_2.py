"""
=========================================================================================
Postprocessing - Randomized Measure - Wavefunction Overlap - Wavefunction Overlap 2
(:mod:`qurry.process.randomized_measure.wavefunction_overlap.wavefunction_overlap_2`)
=========================================================================================

"""

from typing import Union, Optional, TypedDict, Iterable
import numpy as np
import tqdm

from .echo_core_2 import overlap_echo_core_2, DEFAULT_PROCESS_BACKEND
from ...availability import PostProcessingBackendLabel

GenericFloatType = Union[np.float64, float]
"""The generic float type by numpy or python."""


class WaveFuctionOverlapResult(TypedDict):
    """The return type of the post-processing for wavefunction overlap."""

    echo: np.float64
    """The overlap value."""
    echoSD: np.float64
    """The overlap standard deviation."""
    echoCells: dict[int, np.float64]
    """The overlap of each single count."""
    num_classical_registers: int
    """The number of classical registers."""
    classical_registers: Optional[list[int]]
    """The list of the index of the selected classical registers."""
    classical_registers_actually: list[int]
    """The list of the index of the selected classical registers which is actually used."""
    # refactored
    counts_num: int
    """The number of first counts and second counts."""
    taking_time: float
    """The calculation time."""


def randomized_overlap_echo(
    shots: int,
    first_counts: list[dict[str, int]],
    second_counts: list[dict[str, int]],
    selected_classical_registers: Optional[Iterable[int]] = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    pbar: Optional[tqdm.tqdm] = None,
) -> WaveFuctionOverlapResult:
    """Calculate wavefunction overlap
    a.k.a. loschmidt echo when processes time evolution system.

    .. note::

        - Statistical correlations between locally randomized measurements:
        A toolbox for probing entanglement in many-body quantum states -
        A. Elben, B. Vermersch, C. F. Roos, and P. Zoller,
        [PhysRevA.99.052323](
            https://doi.org/10.1103/PhysRevA.99.052323
        )

    .. code-block:: bibtex

        @article{PhysRevA.99.052323,
            title = {Statistical correlations between locally randomized measurements:
            A toolbox for probing entanglement in many-body quantum states},
            author = {Elben, A. and Vermersch, B. and Roos, C. F. and Zoller, P.},
            journal = {Phys. Rev. A},
            volume = {99},
            issue = {5},
            pages = {052323},
            numpages = {12},
            year = {2019},
            month = {May},
            publisher = {American Physical Society},
            doi = {10.1103/PhysRevA.99.052323},
            url = {https://link.aps.org/doi/10.1103/PhysRevA.99.052323}
        }

    Args:
        shots (int):
            Shots of the experiment on quantum machine.
        first_counts (list[dict[str, int]]):
            Counts of the experiment on quantum machine.
        second_counts (list[dict[str, int]]):
            Counts of the experiment on quantum machine.
        selected_classical_registers (Optional[Iterable[int]], optional):
            The list of **the index of the selected_classical_registers**.
        backend (ExistingProcessBackendLabel, optional):
            Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.
        pbar (Optional[tqdm.tqdm], optional):
            The progress bar API, you can use put a :cls:`tqdm` object here.
            This function will update the progress bar description.
            Defaults to None.


    Returns:
        WaveFuctionOverlapResult: A dictionary contains purity, entropy,
            a list of each overlap, puritySD, degree, actual measure range, bitstring range.
    """

    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description_str(
            f"Calculate selected classical registers: {selected_classical_registers}."
        )
    (
        echo_cell_dict,
        selected_classical_registers_actual,
        _msg,
        taken,
    ) = overlap_echo_core_2(
        shots=shots,
        first_counts=first_counts,
        second_counts=second_counts,
        selected_classical_registers=selected_classical_registers,
        backend=backend,
    )
    echo_cell_list: list[Union[float, np.float64]] = list(echo_cell_dict.values())  # type: ignore

    echo: np.float64 = np.mean(echo_cell_list, dtype=np.float64)  # type: ignore
    purity_sd: np.float64 = np.std(echo_cell_list, dtype=np.float64)  # type: ignore

    num_classical_registers = len(list(first_counts[0].keys())[0])

    quantity: WaveFuctionOverlapResult = {
        "echo": echo,
        "echoSD": purity_sd,
        "echoCells": echo_cell_dict,
        "num_classical_registers": num_classical_registers,
        "classical_registers": (
            selected_classical_registers
            if selected_classical_registers is None
            else list(selected_classical_registers)
        ),
        "classical_registers_actually": selected_classical_registers_actual,
        "counts_num": len(first_counts),
        "taking_time": taken,
    }

    return quantity
