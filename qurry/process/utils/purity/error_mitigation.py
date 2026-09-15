"""Post Processing - Utils - Purity - Error Mitigation
(:mod:`qurry.process.utils.purity.error_mitigation`)

Reference:
    -   Simple mitigation of global depolarizing errors in quantum simulations -
        Vovrosh, Joseph and Khosla, Kiran E. and Greenaway, Sean and Self,
        Christopher and Kim, M. S. and Knolle, Johannes,
        `PhysRevE.104.035309 <https://link.aps.org/doi/10.1103/PhysRevE.104.035309>`_

    .. code-block:: bibtex

        @article{PhysRevE.104.035309,
            title = {Simple mitigation of global depolarizing errors in quantum simulations},
            author = {Vovrosh, Joseph and Khosla, Kiran E. and Greenaway, Sean and Self,
            Christopher and Kim, M. S. and Knolle, Johannes},
            journal = {Phys. Rev. E},
            volume = {104},
            issue = {3},
            pages = {035309},
            numpages = {8},
            year = {2021},
            month = {Sep},
            publisher = {American Physical Society},
            doi = {10.1103/PhysRevE.104.035309},
            url = {https://link.aps.org/doi/10.1103/PhysRevE.104.035309}
        }

"""

from typing import TypeVar, TypedDict
import numpy as np
import numpy.typing as npt

AllowedMitigatedInput = npt.NDArray[np.float64] | np.float64 | float
"""Allowed input type for the mitigation functions."""

MitigatedInputT = TypeVar("MitigatedInputT", bound=AllowedMitigatedInput)
"""Type variable for the mitigation functions."""


def solve_p(
    meas_system: MitigatedInputT, subsystem_size: int
) -> tuple[MitigatedInputT, MitigatedInputT]:
    """Solve the equation of p from all system size and subsystem size.

    Args:
        meas_system (_InputT): Measured Systems.
        subsystem_size (int): Subsystem size.

    Returns:
        Two solutions of p.
    """
    b = np.float64(1) / 2 ** (subsystem_size - 1) - 2
    a = np.float64(1) + 1 / 2**subsystem_size - 1 / 2 ** (subsystem_size - 1)
    c = 1 - meas_system
    ppser = (-b + np.sqrt(b**2 - 4 * a * c)) / 2 / a
    pnser = (-b - np.sqrt(b**2 - 4 * a * c)) / 2 / a

    return ppser, pnser


def mitigation_equation(
    p_series: MitigatedInputT, meas_system: MitigatedInputT, subsystem_size: int
) -> MitigatedInputT:
    """Calculate the mitigation equation.

    Args:
        p_series (_InputT): Solution of p.
        meas_system (_InputT): Measured Systems.
        subsystem_size (int): Subsystem size.

    Returns:
        Mitigated series.
    """
    psq = np.square(p_series, dtype=np.float64)
    return (
        meas_system - psq / 2**subsystem_size - (p_series - psq) / 2 ** (subsystem_size - 1)
    ) / np.square(1 - p_series, dtype=np.float64)


class MitigatedResult(TypedDict):
    """The return type of the post-processing for entangled entropy with error mitigation."""

    # mitigated info
    error_rate: AllowedMitigatedInput
    """The error rate of the measurement from depolarizing error migigation calculated."""
    mitigated_purity: AllowedMitigatedInput
    """The mitigated purity."""
    mitigated_entropy: AllowedMitigatedInput
    """The mitigated entropy."""


def depolarizing_error_mitgation(
    meas_system: MitigatedInputT, all_system: MitigatedInputT, subsystem_size: int, system_size: int
) -> MitigatedResult:
    """Depolarizing error mitigation.

    Args:
        meas_system (AllowedMitigatedInput): Value of the measured subsystem.
        all_system (AllowedMitigatedInput): Value of the whole system.
        subsystem_size (int): The size of the subsystem.
        system_size (int): The size of the system.

    Returns:
        Error rate, mitigated purity, mitigated entropy.
    """

    _, pn = solve_p(all_system, system_size)
    mitiga = mitigation_equation(pn, meas_system, subsystem_size)

    return MitigatedResult(
        error_rate=pn,
        mitigated_purity=mitiga,
        mitigated_entropy=-np.log2(mitiga, dtype=np.float64),
    )
