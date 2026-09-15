"""EchoListenRandomized - Arguments (:mod:`qurry.qurries.echo_randomized.arguments`)"""

from typing import Any
from dataclasses import dataclass

from qiskit import QuantumCircuit
from qiskit.providers import Backend
from qiskit.transpiler.passmanager import PassManager

from ...qurrium import ArgumentsPrototype, BasicArgs, OutputArgs, TranspileArgs, WCKeyable
from ...tools import backend_name_getter
from ...process.utils import QubitSelectionType


@dataclass(frozen=True)
class ELRArguments(ArgumentsPrototype):
    """Arguments for
    :class:`~qurry.qurries.echo_randomized.experiment.ELRExperiment`."""

    exp_name: str
    """The name of the experiment.
    Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
    This name is also used for creating a folder to store the exports.
    Defaults to `'experiment'`."""
    times: int
    """The number of random unitary operator. 
    It will denote as :math:`N_U` in the experiment name."""
    qubits_measured_1: list[int]
    """The measure range for the first quantum circuit."""
    qubits_measured_2: list[int]
    """The measure range for the second quantum circuit."""
    registers_mapping_1: dict[int, int]
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
    registers_mapping_2: dict[int, int]
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
    actual_num_qubits_1: int
    """The actual number of qubits of the first quantum circuit."""
    actual_num_qubits_2: int
    """The actual number of qubits of the second quantum circuit."""
    unitary_located_mapping_1: dict[int, int]
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
    unitary_located_mapping_2: dict[int, int]
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
    second_backend: Backend | str | None
    """The extra backend for the second quantum circuit.
    If None, then use the same backend as the first quantum circuit.
    """
    second_transpile_args: TranspileArgs | None
    """Arguments of :func:`~qiskit.compiler.transpile` 
    or :class:`~qiskit.transpiler.passmanager.PassManager` for the second quantum circuit.
    And it only works when the second backend is given.
    """
    random_unitary_seeds: dict[int, dict[int, int]] | None = None
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
    you can use the function 
    :func:`~qurry.process.randomized_measure.utils.generate_random_unitary_seeds`
    in :mod:`qurry.process.randomized_measure.utils`.

    .. code-block:: python

        from qurry import generate_random_unitary_seeds

        random_unitary_seeds = generate_random_unitary_seeds(100, 2)
    """

    def export(self) -> dict[str, Any]:
        """The arguments as dictionary."""
        tmp = self.asdict()
        if isinstance(self.second_backend, Backend):
            tmp["second_backend"] = backend_name_getter(self.second_backend)
        elif isinstance(self.second_backend, str):
            tmp["second_backend"] = self.second_backend
        else:
            tmp["second_backend"] = None
        return tmp

    @classmethod
    def ingest(cls, raw_dict: dict[str, Any]):
        """Ingest from a serialized dictionary.

        Args:
            raw_dict (dict[str, Any]): The raw read dictionary.
        """
        missing_fields = set(cls.dataclass_fields()) - set(raw_dict.keys())
        if missing_fields:
            raise ValueError(f"Missing fields for {cls.__name__}: {', '.join(missing_fields)}")

        return cls(
            exp_name=raw_dict["exp_name"],
            times=raw_dict["times"],
            qubits_measured_1=raw_dict["qubits_measured_1"],
            qubits_measured_2=raw_dict["qubits_measured_2"],
            registers_mapping_1={
                int(k): int(v) for k, v in raw_dict["registers_mapping_1"].items()
            },
            registers_mapping_2={
                int(k): int(v) for k, v in raw_dict["registers_mapping_2"].items()
            },
            actual_num_qubits_1=raw_dict["actual_num_qubits_1"],
            actual_num_qubits_2=raw_dict["actual_num_qubits_2"],
            unitary_located_mapping_1={
                int(k): int(v) for k, v in raw_dict["unitary_located_mapping_1"].items()
            },
            unitary_located_mapping_2={
                int(k): int(v) for k, v in raw_dict["unitary_located_mapping_2"].items()
            },
            second_backend=raw_dict["second_backend"],
            second_transpile_args=raw_dict["second_transpile_args"],
            random_unitary_seeds=(
                {
                    int(k): {int(kk): vv for kk, vv in v.items()}
                    for k, v in raw_dict["random_unitary_seeds"].items()
                }
                if raw_dict.get("random_unitary_seeds") is not None
                else None
            ),
        )

    def replace_second_backend(self, backend: Backend | str | None) -> "ELRArguments":
        """Return a new instance with replaced second_backend.

        Args:
            backend (Backend | str | None): The backend to replace.

        Returns:
            ELRArguments: The new instance with replaced second_backend.
        """
        return ELRArguments(
            exp_name=self.exp_name,
            times=self.times,
            qubits_measured_1=self.qubits_measured_1,
            qubits_measured_2=self.qubits_measured_2,
            registers_mapping_1=self.registers_mapping_1,
            registers_mapping_2=self.registers_mapping_2,
            actual_num_qubits_1=self.actual_num_qubits_1,
            actual_num_qubits_2=self.actual_num_qubits_2,
            unitary_located_mapping_1=self.unitary_located_mapping_1,
            unitary_located_mapping_2=self.unitary_located_mapping_2,
            second_backend=backend,
            second_transpile_args=self.second_transpile_args,
            random_unitary_seeds=self.random_unitary_seeds,
        )


class ELRMeasureArgs(BasicArgs, total=False):
    """Input fields for
    :meth:`~qurry.qurries.echo_randomized.qurry.EchoListenRandomized.measure`
    and :meth:`~qurry.qurrium.qurrium.QurriumPrototype.multiOutput`."""

    wave1: QuantumCircuit | WCKeyable
    """The key or the circuit to execute."""
    wave2: QuantumCircuit | WCKeyable
    """The key or the circuit to execute."""
    times: int
    """The number of random unitary operator. 
    It will denote as :math:`N_U` in the experiment name."""
    measure_1: QubitSelectionType
    """The measure range for the first quantum circuit."""
    measure_2: QubitSelectionType
    """The measure range for the second quantum circuit."""
    unitary_loc_1: QubitSelectionType
    """The range of the unitary operator for the first quantum circuit."""
    unitary_loc_2: QubitSelectionType
    """The range of the unitary operator for the second quantum circuit."""
    unitary_loc_not_cover_measure: bool
    """Whether the range of the unitary operator is not cover the measure range."""
    second_backend: Backend | None
    """The extra backend for the second group of quantum circuits.
    If None, then use the same backend as the first quantum circuit.
    """
    second_transpile_args: TranspileArgs | None
    """The transpile arguments for the second group of quantum circuits."""
    second_passmanager: str | PassManager | tuple[str, PassManager] | None
    """The passmanager for the second quantum circuit."""
    random_unitary_seeds: dict[int, dict[int, int]] | None
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
    you can use the function 
    :func:`~qurry.process.randomized_measure.utils.generate_random_unitary_seeds`
    in :mod:`qurry.process.randomized_measure.utils`.

    .. code-block:: python

        from qurry import generate_random_unitary_seeds

        random_unitary_seeds = generate_random_unitary_seeds(100, 2)
    """


class ELROutputArgs(OutputArgs):
    """Output arguments for
    :meth:`~qurry.qurries.echo_randomized.qurry.EchoListenRandomized.output`."""

    times: int
    """The number of random unitary operator. 
    It will denote as :math:`N_U` in the experiment name."""
    measure_1: QubitSelectionType
    """The measure range for the first quantum circuit."""
    measure_2: QubitSelectionType
    """The measure range for the second quantum circuit."""
    unitary_loc_1: QubitSelectionType
    """The range of the unitary operator for the first quantum circuit."""
    unitary_loc_2: QubitSelectionType
    """The range of the unitary operator for the second quantum circuit."""
    unitary_loc_not_cover_measure: bool
    """Confirm that not all unitary operator are covered by the measure."""
    second_backend: Backend | None
    """The extra backend for the second quantum circuit.
    If None, then use the same backend as the first quantum circuit.
    """
    second_transpile_args: TranspileArgs | None
    """The transpile arguments for the second group of quantum circuits."""
    random_unitary_seeds: dict[int, dict[int, int]] | None
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
    you can use the function 
    :func:`~qurry.process.randomized_measure.utils.generate_random_unitary_seeds`
    in :mod:`qurry.process.randomized_measure.utils`.

    .. code-block:: python

        from qurry import generate_random_unitary_seeds

        random_unitary_seeds = generate_random_unitary_seeds(100, 2)
    """
    second_passmanager_pair: tuple[str, PassManager] | None
    """The passmanager for the second quantum circuit."""


SHORT_NAME = "echo_randomized"
"""The short name of :class:`~qurry.qurries.echo_randomized.qurry.EchoListenRandomized`."""

ACRONYM = "ELR"
"""The abbreviation of :class:`~qurry.qurries.echo_randomized.qurry.EchoListenRandomized`."""
