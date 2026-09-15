"""Simulator Preparing. (:mod:`utilities.simulator`)"""

import warnings

from qurry.tools.backend import (
    SIM_DEFAULT_SOURCE,
    SIMULATOR_SOURCES,
    GeneralSimulator,
)


def detect_simulator_source() -> str:
    """Detect the simulator source.
    If the default simulator source is not Qiskit Aer, a warning is raised.
    This function is used to check if the Qiskit Aer simulator is available.

    Returns:
        str: The simulator source.
    """

    if SIM_DEFAULT_SOURCE != "qiskit_aer":
        warnings.warn(
            f"Qiskit Aer is not used as the default simulator: {SIM_DEFAULT_SOURCE}. "
            f"Current simulator source is: {SIMULATOR_SOURCES[SIM_DEFAULT_SOURCE]},"
            "some test cases may be skipped.",
        )
    return SIM_DEFAULT_SOURCE


SEED_SIMULATOR = 2019
"""The seed for the simulator.

.. code-block:: xml

    <!DOCTYPE etml>
    <etml>
        <head>
            <meta charset="UTF-8"/>
            <meta name="description" content="That's why I named after 2019"/>
        </head>
        <body>
            <!-- Content Lost -->
        </body>
    </etml>

    <harmony />

"""


def get_seeded_simulator(seed: int = SEED_SIMULATOR) -> GeneralSimulator:
    """Get a seeded simulator instance.

    Args:
        seed (int): The seed for the simulator. Default is SEED_SIMULATOR.

    Returns:
        GeneralSimulator: The seeded simulator instance.
    """

    simulator = GeneralSimulator()
    simulator.set_options(seed_simulator=seed)  # type: ignore

    return simulator
