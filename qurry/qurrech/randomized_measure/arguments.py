"""
===========================================================
EchoListenRandomized - Arguments
(:mod:`qurry.qurrech.randomized_measure.arguments`)
===========================================================

"""

from typing import Optional, Union, Iterable, Any
from collections.abc import Hashable
from dataclasses import dataclass

from qiskit import QuantumCircuit
from qiskit.providers import Backend

from ...qurrium.experiment import ArgumentsPrototype
from ...process.randomized_measure.wavefunction_overlap import (
    PostProcessingBackendLabel,
)
from ...tools import backend_name_getter
from ...declare import BasicArgs, OutputArgs, AnalyzeArgs


@dataclass(frozen=True)
class EchoListenRandomizedArguments(ArgumentsPrototype):
    """Arguments for the experiment."""

    exp_name: str = "exps"
    """The name of the experiment.
    Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
    This name is also used for creating a folder to store the exports.
    Defaults to `'experiment'`."""
    times: int = 100
    """The number of random unitary operator. 
    It will denote as `N_U` in the experiment name."""
    qubits_measured_1: Optional[list[int]] = None
    """The measure range for the first quantum circuit."""
    qubits_measured_2: Optional[list[int]] = None
    """The measure range for the second quantum circuit."""
    registers_mapping_1: Optional[dict[int, int]] = None
    """The mapping of the classical registers with quantum registers.
    for the first quantum circuit.

    .. code-block:: python
        {
            0: 0, # The quantum register 0 is mapped to the classical register 0.
            1: 1, # The quantum register 1 is mapped to the classical register 1.
            5: 2, # The quantum register 5 is mapped to the classical register 2.
            7: 3, # The quantum register 7 is mapped to the classical register 3.
        }

    The key is the index of the quantum register with the numerical order.
    The value is the index of the classical register with the numerical order.
    """
    registers_mapping_2: Optional[dict[int, int]] = None
    """The mapping of the classical registers with quantum registers.
    for the second quantum circuit.

    .. code-block:: python
        {
            0: 0, # The quantum register 0 is mapped to the classical register 0.
            1: 1, # The quantum register 1 is mapped to the classical register 1.
            5: 2, # The quantum register 5 is mapped to the classical register 2.
            7: 3, # The quantum register 7 is mapped to the classical register 3.
        }

    The key is the index of the quantum register with the numerical order.
    The value is the index of the classical register with the numerical order.
    """
    actual_num_qubits_1: int = 0
    """The actual number of qubits of the first quantum circuit."""
    actual_num_qubits_2: int = 0
    """The actual number of qubits of the second quantum circuit."""
    unitary_located_mapping_1: Optional[dict[int, int]] = None
    """The range of the unitary operator for the first quantum circuit.

    .. code-block:: python
        {
            0: 0, # The quantum register 0 is used for the unitary operator 0.
            1: 1, # The quantum register 1 is used for the unitary operator 1.
            5: 2, # The quantum register 5 is used for the unitary operator 2.
            7: 3, # The quantum register 7 is used for the unitary operator 3.
        }

    The key is the index of the quantum register with the numerical order.
    The value is the index of the unitary operator with the numerical order.
    """
    unitary_located_mapping_2: Optional[dict[int, int]] = None
    """The range of the unitary operator for the second quantum circuit.

    .. code-block:: python
        {
            0: 0, # The quantum register 0 is used for the unitary operator 0.
            1: 1, # The quantum register 1 is used for the unitary operator 1.
            5: 2, # The quantum register 5 is used for the unitary operator 2.
            7: 3, # The quantum register 7 is used for the unitary operator 3.
        }

    The key is the index of the quantum register with the numerical order.
    The value is the index of the unitary operator with the numerical order.
    """
    second_backend: Optional[Union[Backend, str]] = None
    """The extra backend for the second quantum circuit.
    If None, then use the same backend as the first quantum circuit.
    """
    random_unitary_seeds: Optional[dict[int, dict[int, int]]] = None
    """The seeds for all random unitary operator.
    This argument only takes input as type of `dict[int, dict[int, int]]`.
    The first key is the index for the random unitary operator.
    The second key is the index for the qubit.

    .. code-block:: python
        {
            0: {0: 1234, 1: 5678},
            1: {0: 2345, 1: 6789},
            2: {0: 3456, 1: 7890},
        }

    If you want to generate the seeds for all random unitary operator,
    you can use the function `generate_random_unitary_seeds` 
    in `qurry.qurrium.utils.random_unitary`.

    .. code-block:: python
        from qurry.qurrium.utils.random_unitary import generate_random_unitary_seeds
        random_unitary_seeds = generate_random_unitary_seeds(100, 2)
    """

    def _asdict(self) -> dict[str, Any]:
        """The arguments as dictionary."""
        tmp = self.__dict__.copy()
        if isinstance(self.second_backend, Backend):
            tmp["second_backend"] = backend_name_getter(self.second_backend)
        elif isinstance(self.second_backend, str):
            tmp["second_backend"] = self.second_backend
        else:
            tmp["second_backend"] = None
        return tmp


class EchoListenRandomizedMeasureArgs(BasicArgs, total=False):
    """Output arguments for :meth:`output`."""

    wave1: Optional[Union[QuantumCircuit, Hashable]]
    """The key or the circuit to execute."""
    wave2: Optional[Union[QuantumCircuit, Hashable]]
    """The key or the circuit to execute."""
    times: int
    """The number of random unitary operator. 
    It will denote as `N_U` in the experiment name."""
    measure_1: Optional[Union[tuple[int, int], int, list[int]]]
    """The measure range for the first quantum circuit."""
    measure_2: Optional[Union[tuple[int, int], int, list[int]]]
    """The measure range for the second quantum circuit."""
    unitary_loc_1: Optional[Union[tuple[int, int], int, list[int]]]
    """The range of the unitary operator for the first quantum circuit."""
    unitary_loc_2: Optional[Union[tuple[int, int], int, list[int]]]
    """The range of the unitary operator for the second quantum circuit."""
    unitary_loc_not_cover_measure: bool
    """Whether the range of the unitary operator is not cover the measure range."""
    second_backend: Optional[Backend]
    """The extra backend for the second quantum circuit.
    If None, then use the same backend as the first quantum circuit.
    """
    random_unitary_seeds: Optional[dict[int, dict[int, int]]]
    """The seeds for all random unitary operator.
    This argument only takes input as type of `dict[int, dict[int, int]]`.
    The first key is the index for the random unitary operator.
    The second key is the index for the qubit.

    .. code-block:: python
        {
            0: {0: 1234, 1: 5678},
            1: {0: 2345, 1: 6789},
            2: {0: 3456, 1: 7890},
        }

    If you want to generate the seeds for all random unitary operator,
    you can use the function `generate_random_unitary_seeds` 
    in `qurry.qurrium.utils.random_unitary`.

    .. code-block:: python
        from qurry.qurrium.utils.random_unitary import generate_random_unitary_seeds
        random_unitary_seeds = generate_random_unitary_seeds(100, 2)
    """


class EchoListenRandomizedOutputArgs(OutputArgs):
    """Output arguments for :meth:`output`."""

    times: int
    """The number of random unitary operator. 
    It will denote as `N_U` in the experiment name."""
    measure_1: Optional[Union[tuple[int, int], int, list[int]]]
    """The measure range for the first quantum circuit."""
    measure_2: Optional[Union[tuple[int, int], int, list[int]]]
    """The measure range for the second quantum circuit."""
    unitary_loc_1: Optional[Union[tuple[int, int], int, list[int]]]
    """The range of the unitary operator for the first quantum circuit."""
    unitary_loc_2: Optional[Union[tuple[int, int], int, list[int]]]
    """The range of the unitary operator for the second quantum circuit."""
    unitary_loc_not_cover_measure: bool
    """Confirm that not all unitary operator are covered by the measure."""
    second_backend: Optional[Backend]
    """The extra backend for the second quantum circuit.
    If None, then use the same backend as the first quantum circuit.
    """
    random_unitary_seeds: Optional[dict[int, dict[int, int]]]
    """The seeds for all random unitary operator.
    This argument only takes input as type of `dict[int, dict[int, int]]`.
    The first key is the index for the random unitary operator.
    The second key is the index for the qubit.

    .. code-block:: python
        {
            0: {0: 1234, 1: 5678},
            1: {0: 2345, 1: 6789},
            2: {0: 3456, 1: 7890},
        }

    If you want to generate the seeds for all random unitary operator,
    you can use the function `generate_random_unitary_seeds` 
    in `qurry.qurrium.utils.random_unitary`.

    .. code-block:: python
        from qurry.qurrium.utils.random_unitary import generate_random_unitary_seeds
        random_unitary_seeds = generate_random_unitary_seeds(100, 2)
    """


class EchoListenRandomizedAnalyzeArgs(AnalyzeArgs, total=False):
    """The input of the analyze method."""

    selected_classical_registers: Optional[Iterable[int]]
    """The list of **the index of the selected_classical_registers**.
    It's not the qubit index of first or second quantum circuit,
    but their corresponding classical registers."""
    backend: PostProcessingBackendLabel
    """The backend for the process."""
    counts_used: Optional[Iterable[int]]
    """The index of the counts used."""


SHORT_NAME = "qurrech_randomized"
