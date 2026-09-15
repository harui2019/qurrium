"""Build Tools (:mod:`qurry.qurrium.utils.build`)"""

from qiskit import QuantumCircuit, ClassicalRegister


def decomposer(qc: QuantumCircuit, reps: int = 2) -> QuantumCircuit:
    """Decompose the circuit with giving times.

    Args:
        qc (QuantumCircuit): The circuit wanted to be decomposed.
        reps (int, optional): Decide the times of decomposing the circuit.
            Draw quantum circuit with composed circuit. Defaults to 2.

    Returns:
        QuantumCircuit: The decomposed circuit.
    """

    return qc.decompose(reps=reps)


def is_cregs_name_collision(
    circuit: QuantumCircuit, new_creg_or_name: ClassicalRegister | str
) -> bool:
    """Whether the name of the new classical register collides with existing ones.

    Args:
        circuit (QuantumCircuit): The quantum circuit to check.
        new_creg_or_name (ClassicalRegister | str): The new classical register or its name.

    Raises:
        TypeError: If `new_creg_or_name` is neither a `ClassicalRegister` nor a `str`.

    Returns:
        bool: True if there is a name collision, False otherwise.
    """
    if isinstance(new_creg_or_name, ClassicalRegister):
        return circuit.has_register(new_creg_or_name)
    if isinstance(new_creg_or_name, str):
        return new_creg_or_name in [reg.name for reg in circuit.cregs]
    raise TypeError(
        "The argument new_creg_or_name should be either a ClassicalRegister or a string."
    )


def check_cregs_name_collision(
    circuit: QuantumCircuit, new_creg_or_name: ClassicalRegister | str
) -> None:
    """Check whether the name of the new classical register collides with existing ones.

    Args:
        circuit (QuantumCircuit): The quantum circuit to check.
        new_creg_or_name (ClassicalRegister | str): The new classical register or its name.

    Raises:
        ValueError: If there is a name collision.
    """
    if is_cregs_name_collision(circuit, new_creg_or_name):
        name = (
            new_creg_or_name.name
            if isinstance(new_creg_or_name, ClassicalRegister)
            else new_creg_or_name
        )
        raise ValueError(
            "The name of the new classical register collides with existing ones, "
            + f"the name '{name}' already exists in the circuit, "
            + "which is reserved for measurement. Due to the limitation of Qiskit, "
            + "the classical registers are globally in each circuit operation, "
            + "so we can not rename the existing classical registers for it will corrupt. "
            + "Please create another quantum circuit with different classical register names."
        )
