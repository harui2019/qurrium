"""Post Processing - Randomized Measure - Wavefunction Overlap V1 - Wavefunction Overlap
(:mod:`qurry.process.randomized_measure.wavefunction_overlap_v1.wavefunction_overlap`)
This is a deprecated version of the wavefunction overlap.

"""

from typing import TypedDict
import numpy as np
import tqdm

from .echo_core import overlap_echo_core, DEFAULT_PROCESS_BACKEND
from ...availability import PostProcessingBackendLabel
from ...utils import FloatType


class WaveFuctionOverlapResultV1(TypedDict):
    """The return type of the post-processing for wavefunction overlap."""

    echo: FloatType
    """The overlap value."""
    echoSD: FloatType
    """The overlap standard deviation."""
    echoCells: dict[int, np.float64] | dict[int, float]
    """The overlap of each single count."""
    degree: tuple[int, int] | int | None
    """The range of partition."""
    measureActually: tuple[int, int]
    """The range of partition refer to all qubits."""
    bitStringRange: tuple[int, int] | list[int]
    """The range of partition on the bitstring."""

    countsNum: int
    """The number of first counts and second counts."""
    takingTime: float
    """The calculation time."""


def randomized_overlap_echo_v1(
    shots: int,
    counts: list[dict[str, int]],
    degree: tuple[int, int] | int | None = None,
    measure: tuple[int, int] | None = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    workers_num: int | None = None,
    pbar: tqdm.tqdm | None = None,
) -> WaveFuctionOverlapResultV1:
    """Calculate wavefunction overlap
    a.k.a. loschmidt echo when processes time evolution system.

    Reference:
        -   Statistical correlations between locally randomized measurements:
            A toolbox for probing entanglement in many-body quantum states -
            A. Elben, B. Vermersch, C. F. Roos, and P. Zoller,
            `PhysRevA.99.052323 <https://doi.org/10.1103/PhysRevA.99.052323>`_

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
            Shots of the counts.
        counts (list[dict[str, int]]):
            Counts from randomized measurement results.
        degree (tuple[int, int] | int | None, optional):
            The range of partition.
        measure (tuple[int, int] | None, optional):
            The range that implemented the measuring gate.
            If not specified, then use all qubits.
            This will affect the range of partition
            when you not implement the measuring gate on all qubit.
            Defaults to None.
        backend (PostProcessingBackendLabel, optional):
            Backend for the post-processing.
            Defaults to DEFAULT_PROCESS_BACKEND.
        workers_num (int | None, optional):
            Number of multi-processing workers, it will be ignored if backend is Rust.
            if sets to 1, then disable to using multi-processing;
            if not specified, then use the number of all cpu counts by `os.cpu_count()`.
            This only works for Python and Cython backend.
            Defaults to None.
        pbar (tqdm.tqdm | None, optional):
            The progress bar API,
            you can use put a `tqdm.tqdm <https://tqdm.github.io/>` object here.
            This function will update the progress bar description.
            Defaults to None.

    Returns:
        A dictionary contains purity, entropy,
        a list of each overlap, puritySD, degree, actual measure range, bitstring range.
    """

    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description_str(f"Calculate overlap with {len(counts)} counts.")

    (echo_cell_dict, bitstring_range, measure_range, _msg_of_process, taken) = overlap_echo_core(
        shots=shots,
        counts=counts,
        degree=degree,
        measure=measure,
        backend=backend,
        multiprocess_pool_size=workers_num,
    )
    echo_cell_list: list[np.float64] = list(echo_cell_dict.values())  # type: ignore

    echo = np.mean(echo_cell_list, dtype=np.float64)
    purity_sd = np.std(echo_cell_list, dtype=np.float64)

    return {
        "echo": echo,
        "echoSD": purity_sd,
        "echoCells": echo_cell_dict,
        "degree": degree,
        "measureActually": measure_range,
        "bitStringRange": bitstring_range,
        "countsNum": len(counts),
        "takingTime": taken,
    }
