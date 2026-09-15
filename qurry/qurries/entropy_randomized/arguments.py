"""EntropyMeasureRandomized - Arguments (:mod:`qurry.qurries.entropy_randomized.arguments`)"""

from typing import Any
from dataclasses import dataclass

from qiskit import QuantumCircuit

from ...qurrium import ArgumentsPrototype, BasicArgs, OutputArgs, WCKeyable
from ...process.utils import QubitSelectionType


@dataclass(frozen=True)
class EMRArguments(ArgumentsPrototype):
    """Arguments for
    :class:`~qurry.qurries.entropy_randomized.experiment.EMRExperiment`."""

    exp_name: str
    """The name of the experiment.
    Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
    This name is also used for creating a folder to store the exports.
    Defaults to `'experiment'`."""
    times: int
    """The number of random unitary operator. 
    It will denote as :math:`N_U` in the experiment name."""
    qubits_measured: list[int]
    """The measure range."""
    registers_mapping: dict[int, int]
    """The mapping of the classical registers of measurement with quantum registers.

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
    actual_num_qubits: int
    """The actual number of qubits."""
    unitary_located: list[int]
    """The range of the unitary operator."""
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
            qubits_measured=raw_dict["qubits_measured"],
            registers_mapping={int(k): int(v) for k, v in raw_dict["registers_mapping"].items()},
            actual_num_qubits=raw_dict["actual_num_qubits"],
            unitary_located=raw_dict["unitary_located"],
            random_unitary_seeds={
                int(k): {int(kk): vv for kk, vv in v.items()}
                for k, v in raw_dict["random_unitary_seeds"].items()
            }
            if raw_dict.get("random_unitary_seeds") is not None
            else None,
        )


class EMRMeasureArgs(BasicArgs, total=False):
    """Input fields for
    :meth:`~qurry.qurries.entropy_randomized.qurry.EntropyMeasureRandomized.measure`
    and :meth:`~qurry.qurrium.qurrium.QurriumPrototype.multiOutput`."""

    wave: QuantumCircuit | WCKeyable
    """The key or the circuit to execute."""
    times: int
    """The number of random unitary operator. 
    It will denote as :math:`N_U` in the experiment name."""
    measure: QubitSelectionType
    """The measure range."""
    unitary_loc: QubitSelectionType
    """The range of the unitary operator."""
    unitary_loc_not_cover_measure: bool
    """Whether the range of the unitary operator is not cover the measure range."""
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


class EMROutputArgs(OutputArgs):
    """Output arguments for
    :meth:`~qurry.qurries.entropy_randomized.qurry.EntropyMeasureRandomized.output`."""

    times: int
    """The number of random unitary operator. 
    It will denote as :math:`N_U` in the experiment name."""
    measure: QubitSelectionType
    """The measure range."""
    unitary_loc: QubitSelectionType
    """The range of the unitary operator."""
    unitary_loc_not_cover_measure: bool
    """Whether the range of the unitary operator is not cover the measure range."""
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


SHORT_NAME = "entropy_randomized"
"""The short name of
:class:`~qurry.qurries.entropy_randomized.qurry.EntropyMeasureRandomized`."""

ACRONYM = "EMR"
"""The abbreviation of
:class:`~qurry.qurries.entropy_randomized.qurry.EntropyMeasureRandomized`."""
