"""
================================================================
Postprocessing - Renyi Entropy - Randomized Measure - 
Error Mitigation
(:mod:`qurry.process.randomized_measure.error_mitigation`)
================================================================

"""

from typing import overload
import numpy as np


# Randomized measure error mitigation
@overload
def solve_p(meas_series: np.ndarray, n_a: int) -> tuple[np.ndarray, np.ndarray]:
    ...


@overload
def solve_p(meas_series: float, n_a: int) -> tuple[float, float]:
    ...


def solve_p(meas_series, n_a):
    """Solve the equation of p from all system size and subsystem size.

    Args:
        meas_series (Union[np.ndarray, float]): Measured series.
        n_a (int): Subsystem size.

    Returns:
        Union[tuple[np.ndarray, np.ndarray], tuple[float, float]]:
            Two solutions of p.
    """
    b = np.float64(1) / 2 ** (n_a - 1) - 2
    a = np.float64(1) + 1 / 2**n_a - 1 / 2 ** (n_a - 1)
    c = 1 - meas_series
    ppser = (-b + np.sqrt(b**2 - 4 * a * c)) / 2 / a
    pnser = (-b - np.sqrt(b**2 - 4 * a * c)) / 2 / a

    return ppser, pnser


@overload
def mitigation_equation(
    pser: np.ndarray, meas_series: np.ndarray, n_a: int
) -> np.ndarray:
    ...


@overload
def mitigation_equation(pser: float, meas_series: float, n_a: int) -> float:
    ...


def mitigation_equation(pser, meas_series, n_a):
    """Calculate the mitigation equation.

    Args:
        pser (Union[np.ndarray, float]): Solution of p.
        meas_series (Union[np.ndarray, float]): Measured series.
        n_a (int): Subsystem size.

    Returns:
        Union[np.ndarray, float]: Mitigated series.
    """
    psq = np.square(pser, dtype=np.float64)
    return (meas_series - psq / 2**n_a - (pser - psq) / 2 ** (n_a - 1)) / np.square(
        1 - pser, dtype=np.float64
    )


@overload
def depolarizing_error_mitgation(
    meas_system: float,
    all_system: float,
    n_a: int,
    system_size: int,
) -> dict[str, float]:
    ...


@overload
def depolarizing_error_mitgation(
    meas_system: np.ndarray,
    all_system: np.ndarray,
    n_a: int,
    system_size: int,
) -> dict[str, np.ndarray]:
    ...


def depolarizing_error_mitgation(meas_system, all_system, n_a, system_size):
    """Depolarizing error mitigation.

    Args:
        meas_system (Union[float, np.ndarray]): Value of the measured subsystem.
        all_system (Union[float, np.ndarray]): Value of the whole system.
        n_a (int): The size of the subsystem.
        system_size (int): The size of the system.

    Returns:
        Union[dict[str, float], dict[str, np.ndarray]]:
            Error rate, mitigated purity, mitigated entropy.
    """

    _, pn = solve_p(all_system, system_size)
    mitiga = mitigation_equation(pn, meas_system, n_a)

    return {
        "errorRate": pn,
        "mitigatedPurity": mitiga,
        "mitigatedEntropy": -np.log2(mitiga, dtype=np.float64),
    }
