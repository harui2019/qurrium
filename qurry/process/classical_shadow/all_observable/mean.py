"""Post Processing - Classical Shadow - All Observable Calculation - Mean of Rho
(:mod:`qurry.process.classical_shadow.all_observable.mean`)

"""

from typing import Literal
from collections.abc import Iterable
import tqdm

from .container_kind import ClassicalShadowBasic
from ..rho_process import (
    RhoMethodType,
    DEFAULT_RHO_METHOD,
    rho_core,
    ShadowBasisType,
    DEFAULT_SHADOW_BASIS,
    mean_rho_core,
)
from ..utils import check_random_basis_array


def mean_rho(
    shots: int,
    counts: list[dict[str, int]],
    random_basis_array: list[list[Literal[0, 1, 2] | int]],
    selected_classical_registers: Iterable[int] | None = None,
    rho_method: RhoMethodType = DEFAULT_RHO_METHOD,
    shadow_basis: ShadowBasisType = DEFAULT_SHADOW_BASIS,
    use_projector: bool = False,
    pbar: tqdm.tqdm | None = None,
) -> ClassicalShadowBasic:
    r"""Calculate the mean of Rho.

    Reference:
        -   Predicting many properties of a quantum system from very few measurements -
            Huang, Hsin-Yuan and Kueng, Richard and Preskill, John
            `doi:10.1038/s41567-020-0932-7 <https://doi.org/10.1038/s41567-020-0932-7>`_

        .. code-block:: bibtex

            @article{cite-key,
                abstract = {
                    Predicting the properties of complex,
                    large-scale quantum systems is essential for developing quantum technologies.
                    We present an efficient method for constructing an approximate classical
                    description of a quantum state using very few measurements of the state.
                    different properties; order
                    {\$}{\$}{\{}{$\backslash$}mathrm{\{}log{\}}{\}}{$\backslash$},(M){\$}{\$}
                    measurements suffice to accurately predict M different functions of the state
                    with high success probability. The number of measurements is independent of
                    the system size and saturates information-theoretic lower bounds. Moreover,
                    target properties to predict can be
                    selected after the measurements are completed.
                    We support our theoretical findings with extensive numerical experiments.
                    We apply classical shadows to predict quantum fidelities,
                    entanglement entropies, two-point correlation functions,
                    expectation values of local observables and the energy variance of
                    many-body local Hamiltonians.
                    The numerical results highlight the advantages of classical shadows relative to
                    previously known methods.},
                author = {Huang, Hsin-Yuan and Kueng, Richard and Preskill, John},
                date = {2020/10/01},
                date-added = {2024-12-03 15:00:55 +0800},
                date-modified = {2024-12-03 15:00:55 +0800},
                doi = {10.1038/s41567-020-0932-7},
                id = {Huang2020},
                isbn = {1745-2481},
                journal = {Nature Physics},
                number = {10},
                pages = {1050--1057},
                title = {Predicting many properties of a quantum system from very few measurements},
                url = {https://doi.org/10.1038/s41567-020-0932-7},
                volume = {16},
                year = {2020},
                bdsk-url-1 = {https://doi.org/10.1038/s41567-020-0932-7}
            }

    Args:
        shots (int):
            The number of shots.
        counts (list[dict[str, int]]):
            The list of the counts.
        random_basis_array (list[list[Literal[0, 1, 2] | int]]):
            The random basis for classical shadow.
        selected_classical_registers (Iterable[int] | None, optional):
            The list of **the index of the selected_classical_registers**.
            Defaults to None.
        rho_method (RhoMethodType, optional):
            For the "multi_shots" methods, the counts and random basis are used as is.
            For the "single_shots" methods, the counts and random basis are
            converted to single shot per snapshot for classical shadow post-processing.

            **Warning: Although larger snapshots number means more accurate values.**
            **But if your shots number is large, this may significantly increase memory usage,**
            **require a lot of computing resource, and may run out of memory.**
            **Please consider carefully for performance.**

            Default to :data:`DEFAULT_RHO_METHOD`.
        shadow_basis (ShadowBasisType, optional):
            The shadow basis to use. Defaults to :data:`DEFAULT_SHADOW_BASIS`.

            Here are the built-in basis sets:
            - `RY_RX_RZ`:
                Uses :math:`R_Y(-\frac{\pi}{2})`, :math:`R_X(\frac{\pi}{2})`,
                and :math:`R_Z(0)` gates.
            - `H_H-Sdg_I`:
                Uses :math:`H`, :math:`H` followed by :math:`S^\dagger`,
                and Identity gates.
        use_projector (bool):
            Use the projecter :math:`P_m` instead of the precomputed :math:`\rho_m`.
            Refer to
            :func:`qurry.process.classical_shadow.rho_process.rho_m_cell.rho_m_cell_precomputed`
            for more details.
            Default is False, which means using the precomputed :math:`\rho_{mk}^{i}`.

        pbar (tqdm.tqdm | None, optional):
            The progress bar. Defaults to None.

    Returns:
        ClassicalShadowMeanRho: The expectation value of Rho.
    """

    check_random_basis_array(random_basis_array, len(counts), len(next(iter(counts[0].keys()))))

    rho_m_list, selected_classical_registers_sorted, shadow_basis_obj, taken = rho_core(
        shots=shots,
        counts=counts,
        random_unitary_array=random_basis_array,
        selected_classical_registers=selected_classical_registers,
        rho_method=rho_method,
        shadow_basis=shadow_basis,
        use_projector=use_projector,
    )
    if pbar is not None:
        pbar.set_description(f"| taking time of all rho_m: {taken:.4f} sec")

    expect_rho = mean_rho_core(
        rho_m_list=rho_m_list,
        selected_classical_registers_sorted=selected_classical_registers_sorted,
    )

    return ClassicalShadowBasic(
        average_snapshots_rho_list=rho_m_list,
        classical_registers_actually=selected_classical_registers_sorted,
        taking_time=taken,
        rho_method=rho_method,
        random_basis_data=shadow_basis_obj.export(),
        # The mean of Rho
        mean_of_rho=expect_rho,
        use_projector=use_projector,
    )
