"""
=========================================================================================
Postprocessing - Randomized Measure - Wavefunction Overlap - Wavefunction Overlap
(:mod:`qurry.process.randomized_measure.wavefunction_overlap.wavefunction_overlap`)
=========================================================================================

"""

from typing import Union, Optional
import numpy as np
import tqdm

from .echo_core import overlap_echo_core, DEFAULT_PROCESS_BACKEND
from ...availability import PostProcessingBackendLabel


def randomized_overlap_echo(
    shots: int,
    counts: list[dict[str, int]],
    degree: Optional[Union[tuple[int, int], int]] = None,
    measure: Optional[tuple[int, int]] = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    workers_num: Optional[int] = None,
    pbar: Optional[tqdm.tqdm] = None,
) -> dict[str, float]:
    """Calculate entangled entropy.

    - Reference:
        - Used in:
            Statistical correlations between locally randomized measurements:
            A toolbox for probing entanglement in many-body quantum states -
            A. Elben, B. Vermersch, C. F. Roos, and P. Zoller,
            [PhysRevA.99.052323](https://doi.org/10.1103/PhysRevA.99.052323)

        - `bibtex`:

    ```bibtex
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
        ```

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
        degree (Union[tuple[int, int], int]): Degree of the subsystem.
        measure (tuple[int, int], optional): Measuring range on quantum circuits. Defaults to None.
        workers_num (Optional[int], optional):
            Number of multi-processing workers,
            if sets to 1, then disable to using multi-processing;
            if not specified, then use the number of all cpu counts - 2 by `cpu_count() - 2`.
            Defaults to None.
        pbar (Optional[tqdm.tqdm], optional): Progress bar. Defaults to None.
        all_system_source (Optional['EntropyRandomizedAnalysis'], optional):
            The source of the all system. Defaults to None.
        use_cython (bool, optional): Use cython to calculate purity cell. Defaults to True.

    Returns:
        dict[str, float]: A dictionary contains purity, entropy,
            a list of each overlap, puritySD, degree, actual measure range, bitstring range.
    """

    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description_str(f"Calculate overlap with {len(counts)} counts.")

    (
        echo_cell_dict,
        bitstring_range,
        measure_range,
        _msg_of_process,
        taken,
    ) = overlap_echo_core(
        shots=shots,
        counts=counts,
        degree=degree,
        measure=measure,
        backend=backend,
        multiprocess_pool_size=workers_num,
    )
    echo_cell_list: Union[list[float], list[np.float64]] = list(
        echo_cell_dict.values()
    )  # type: ignore

    echo = np.mean(echo_cell_list, dtype=np.float64)
    purity_sd = np.std(echo_cell_list, dtype=np.float64)

    quantity = {
        "echo": echo,
        "echoCells": echo_cell_dict,
        "echoSD": purity_sd,
        "degree": degree,
        "measureActually": measure_range,
        "bitStringRange": bitstring_range,
        "countsNum": len(counts),
        "takingTime": taken,
    }

    return quantity
