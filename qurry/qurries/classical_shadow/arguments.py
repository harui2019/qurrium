"""ShadowUnveil - Arguments (:mod:`qurry.qurries.classical_shadow.arguments`)"""

from typing import Any
from dataclasses import dataclass

from qiskit import QuantumCircuit

from ...qurrium import ArgumentsPrototype, BasicArgs, OutputArgs, WCKeyable
from ...process.classical_shadow import ShadowBasisType, ShadowRandomBasis
from ...process.utils import QubitSelectionType


@dataclass(frozen=True)
class SUArguments(ArgumentsPrototype):
    """Arguments for :class:`~qurry.qurries.classical_shadow.experiment.SUExperiment`."""

    exp_name: str
    """The name of the experiment.
    Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
    This name is also used for creating a folder to store the exports.
    Defaults to `'experiment'`."""
    snapshots: int
    """The number of random unitary operator, previously called `times`
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

    shadow_basis: ShadowRandomBasis
    """The method to generate random basis for classical shadow.
    It can be set to 
    :class:`~qurry.process.classical_shadow.rho_process.unitary_set.ShadowRandomBasis`
    or :class:`~qurry.process.classical_shadow.rho_process.unitary_set.ShadowBasisMethod`."""
    random_basis: dict[int, dict[int, int]]
    """The random basis for classical shadow.

    This argument only takes input as type of `dict[int, dict[int, int]]`.
    The first key is the index if snapshots.
    The second key is the index for the qubit.

    .. code-block:: python

        {
            0: {0: 1, 1: 0},
            1: {0: 2, 1: 1},
            2: {0: 0, 1: 2},
        }

    If you want to generate the seeds for all random unitary operator,
    you can use the function :func:`generate_random_basis` 
    in :mod:`qurry.process.classical_shadow.utils`.

    .. code-block:: python

        from qurry import generate_random_basis

        random_basis = generate_random_basis(100, [0, 1])
    """

    def export(self) -> dict[str, Any]:
        """Export to a serializable dictionary.

        Returns:
            dict[str, Any]: The exported dictionary.
        """
        return {
            "exp_name": self.exp_name,
            "snapshots": self.snapshots,
            "qubits_measured": self.qubits_measured,
            "registers_mapping": self.registers_mapping,
            "actual_num_qubits": self.actual_num_qubits,
            "unitary_located": self.unitary_located,
            "shadow_basis": self.shadow_basis.export(),
            "random_basis": self.random_basis,
        }

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
            snapshots=raw_dict["snapshots"],
            qubits_measured=raw_dict["qubits_measured"],
            registers_mapping={int(k): int(v) for k, v in raw_dict["registers_mapping"].items()},
            actual_num_qubits=raw_dict["actual_num_qubits"],
            unitary_located=raw_dict["unitary_located"],
            shadow_basis=ShadowRandomBasis.ingest(raw_dict["shadow_basis"]),
            random_basis={
                int(k): {int(kk): vv for kk, vv in v.items()}
                for k, v in raw_dict["random_basis"].items()
            },
        )


class SUMeasureArgs(BasicArgs, total=False):
    """Input fields for
    :meth:`~qurry.qurries.classical_shadow.qurry.ShadowUnveil.measure`
    and :meth:`~qurry.qurrium.qurrium.QurriumPrototype.multiOutput`."""

    wave: QuantumCircuit | WCKeyable
    """The key or the circuit to execute."""
    snapshots: int
    """The number of random unitary operator, previously called `times`
    It will denote as :math:`N_U` in the experiment name."""
    measure: QubitSelectionType
    """The measure range."""
    unitary_loc: QubitSelectionType
    """The range of the unitary operator."""
    unitary_loc_not_cover_measure: bool
    """Whether the range of the unitary operator is not cover the measure range."""
    shadow_basis_method: ShadowBasisType | None
    """The classical shadow basis for sampling.
    It can be set to 
    :class:`~qurry.process.classical_shadow.rho_process.unitary_set.ShadowRandomBasis`
    or :class:`~qurry.process.classical_shadow.rho_process.unitary_set.ShadowBasisMethod`.
    Defaults to None, which use the default Pauli basis
    from :class:`~qurry.process.classical_shadow.rho_process.unitary_set.ShadowBasisMethod`."""
    random_basis: dict[int, dict[int, int]] | None
    """The random basis for classical shadow.

    This argument only takes input as type of `dict[int, dict[int, int]]`.
    The first key is the index if snapshots.
    The second key is the index for the qubit.

    .. code-block:: python

        {
            0: {0: 1, 1: 0},
            1: {0: 2, 1: 1},
            2: {0: 0, 1: 2},
        }

    If you want to generate the seeds for all random unitary operator,
    you can use the function :func:`generate_random_basis` 
    in :mod:`qurry.process.classical_shadow.utils`.

    .. code-block:: python

        from qurry import generate_random_basis

        random_basis = generate_random_basis(100, [0, 1])
    """


class SUOutputArgs(OutputArgs):
    """Output arguments for :meth:`~qurry.qurries.classical_shadow.qurry.ShadowUnveil.output`."""

    snapshots: int
    """The number of random unitary operator, previously called `times`
    It will denote as :math:`N_U` in the experiment name."""
    measure: QubitSelectionType
    """The measure range."""
    unitary_loc: QubitSelectionType
    """The range of the unitary operator."""
    unitary_loc_not_cover_measure: bool
    """Whether the range of the unitary operator is not cover the measure range."""
    shadow_basis_method: ShadowBasisType | None
    """The classical shadow basis for sampling.
    It can be set to 
    :class:`~qurry.process.classical_shadow.rho_process.unitary_set.ShadowRandomBasis`
    or :class:`~qurry.process.classical_shadow.rho_process.unitary_set.ShadowBasisMethod`.
    Defaults to None, which use the default Pauli basis
    from :class:`~qurry.process.classical_shadow.rho_process.unitary_set.ShadowBasisMethod`."""
    random_basis: dict[int, dict[int, int]] | None
    """The random basis for classical shadow.

    This argument only takes input as type of `dict[int, dict[int, int]]`.
    The first key is the index if snapshots.
    The second key is the index for the qubit.

    .. code-block:: python

        {
            0: {0: 1, 1: 0},
            1: {0: 2, 1: 1},
            2: {0: 0, 1: 2},
        }

    If you want to generate the seeds for all random unitary operator,
    you can use the function :func:`generate_random_basis` 
    in :mod:`qurry.process.classical_shadow.utils`.

    .. code-block:: python

        from qurry import generate_random_basis

        random_basis = generate_random_basis(100, [0, 1])
    """


SHORT_NAME = "classical_shadow"
"""The short name of :class:`~qurry.qurries.classical_shadow.qurry.ShadowUnveil`."""

ACRONYM = "SU"
"""The acronym of :class:`~qurry.qurries.classical_shadow.qurry.ShadowUnveil`."""
