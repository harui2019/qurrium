"""Circuit Cases for testing. (:mod:`utilities.circuits`)

This module contains the circuit cases for testing the qurry package.

"""

from typing import Literal

from qiskit import QuantumCircuit, ClassicalRegister
from qiskit.circuit.classical import expr

from qurry.recipe import intracell


def add_cnot_dyn(
    qc: QuantumCircuit,
    control_qubit: int,
    target_qubit: int,
    c1: ClassicalRegister,
    c2: ClassicalRegister,
    add_barriers: bool = True,
    reset_between_bell_pairs: bool = True,
) -> QuantumCircuit:
    """Generate a CNOT gate bewteen data qubit control_qubit and
    data qubit target_qubit using Bell Pairs.

    Post processing is used to enable the CNOT gate
    via the provided classicial registers c1 and c2

    Assumes that the long-range CNOT gate will be spanning a 1D chain of n-qubits subject
    to nearest-neighbor connections only with the chain starting
    at the control qubit and finishing at the target qubit.

    Assumes that `control_qubit < target_qubit (as integers)` and
    that the provided circuit qc has |0> set
    qubits `control_qubit+1`, ..., `target_qubit-1`

    `n = target_qubit - control_qubit - 1` : Number of qubits between the target and control qubits
    `k = int(n/2)` : Number of Bell pairs created

    .. code-block:: bibtex

        @article{B_umer_2024,
            title={Efficient Long-Range Entanglement Using Dynamic Circuits},
            volume={5},
            ISSN={2691-3399},
            url={http://dx.doi.org/10.1103/PRXQuantum.5.030339},
            DOI={10.1103/prxquantum.5.030339},
            number={3},
            journal={PRX Quantum},
            publisher={American Physical Society (APS)},
            author={
                Bäumer, Elisa and Tripathi, Vinay and Wang, Derek S. and Rall,
                Patrick and Chen, Edward H. and Majumder, Swarnadeep and Seif,
                Alireza and Minev, Zlatko K.},
            year={2024},
            month=aug
        }

    Args:
        qc (QuantumCicruit):
            A Quantum Circuit to add the long range localized unitary CNOT
        control_qubit (int):
            The qubit used as the control.
        target_qubi (int):
            The qubit targeted by the gate.
        c1 (ClassicialRegister):
            Required if n > 1. Register requires k bits
        c2 (ClassicalRegister):
            Required if n > 0. Register requires n - k bits
        add_barriers (bool, optional):
            Default = True. Include barriers before and after long range CNOT
        reset_between_bell_pairs (bool, optional):
            Default = False. Reset the qubits between Bell pairs

    Returns:
        QuantumCircuit: The circuit with the long range CNOT added.
    """
    assert target_qubit > control_qubit
    n = target_qubit - control_qubit - 1
    t = int(n / 2)

    if add_barriers is True:
        qc.barrier()

    # Deteremine where to start the bell pairs and
    # add an extra CNOT when n is odd
    if n % 2 == 0:
        x0 = 1
    else:
        x0 = 2
        qc.cx(0, 1)

    # Create t Bell pairs
    for i in range(t):
        qc.h(x0 + 2 * i)
        qc.cx(x0 + 2 * i, x0 + 2 * i + 1)

    # Entangle Bell pairs and data qubits and measure
    for i in range(t + 1):
        qc.cx(x0 - 1 + 2 * i, x0 + 2 * i)

    parity_control = None
    parity_target = None

    for i in range(1, t + x0):
        qc.h(2 * i + 1 - x0)
        qc.measure(2 * i + 1 - x0, c2[i - 1])
        parity_control = expr.lift(c2[i - 1]) if i == 1 else expr.bit_xor(c2[i - 1], parity_control)

    for i in range(t):
        qc.measure(2 * i + x0, c1[i])
        parity_target = expr.lift(c1[i]) if i == 0 else expr.bit_xor(c1[i], parity_target)

    if n > 0:
        with qc.if_test(parity_control):  # type: ignore
            qc.z(0)

    if n > 1:
        with qc.if_test(parity_target):  # type: ignore
            qc.x(-1)

    if reset_between_bell_pairs is True:
        for i in range(t):
            qc.reset(x0 + 2 * i)
            qc.reset(x0 + 2 * i + 1)
        if n % 2 != 0:
            qc.reset(1)

    if add_barriers is True:
        qc.barrier()

    return qc


def cx_dyn_comparing(
    num_qubits: int,
    mode: Literal["dynamic", "comparison"] = "dynamic",
    reset_between_bell_pairs: bool = True,
    name: str | None = None,
) -> QuantumCircuit:
    """Generate a circuit with a CNOT gate between the first and last qubits
    using either the dynamic CNOT method or a comparison CNOT method.

    This circuit used to test the dynamic CNOT gate
    against a standard CNOT gate in a comparison experiment.

    Args:
        num_qubits (int): The number of qubits in the circuit.
        mode (Literal["dynamic", "comparison"], optional):
            The mode of the circuit. Defaults to "dynamic".
        reset_between_bell_pairs (bool, optional):
            Whether to reset qubits between Bell pairs. Defaults to True.
        name (str | None, optional): The name of the circuit. Defaults to None.

    Raises:
        ValueError: If num_qubits is not between 4 and 8.
    """
    if num_qubits < 4 or num_qubits > 8:
        raise ValueError("Number of qubits must be between 4 and 8")

    qc = QuantumCircuit(num_qubits, name=name)
    qc.h(0)

    c1 = ClassicalRegister(int((num_qubits - 2) / 2), name="c1")
    c2 = ClassicalRegister(num_qubits - 2 - int((num_qubits - 2) / 2), name="c2")
    qc.add_register(c1)
    qc.add_register(c2)

    if mode == "dynamic":
        return add_cnot_dyn(
            qc,
            control_qubit=0,
            target_qubit=num_qubits - 1,
            c1=c1,
            c2=c2,
            reset_between_bell_pairs=reset_between_bell_pairs,
        )

    if mode == "comparison":
        qc.cx(0, num_qubits - 1)
        return qc

    raise ValueError("Invalid mode. Choose 'dynamic' or 'comparison'.")


def dummy_two_body_measurement(
    num_qubits: int,
    clbit_num_cluster: int = 4,
    name: str | None = None,
) -> QuantumCircuit:
    """A dummy circuit to simulate a two-body interaction
    with dedicated classical bits and reset gate.
    But the last 2 qubits will be not measured and reset.

    - The dummy circuit with dedicated classical bits and reset gate

    .. code-block:: text
        # At 6 qubits with 2 classical registers:
              ┌───┐ ░ ┌─┐          ░
        q1_0: ┤ X ├─░─┤M├──────────░──|0>─
              └───┘ ░ └╥┘┌─┐       ░
        q1_1: ──────░──╫─┤M├───────░──|0>─
              ┌───┐ ░  ║ └╥┘┌─┐    ░
        q1_2: ┤ X ├─░──╫──╫─┤M├────░──|0>─
              └───┘ ░  ║  ║ └╥┘┌─┐ ░
        q1_3: ──────░──╫──╫──╫─┤M├─░──|0>─
              ┌───┐ ░  ║  ║  ║ └╥┘ ░
        q1_4: ┤ X ├─░──╫──╫──╫──╫──░──────
              └───┘ ░  ║  ║  ║  ║  ░
        q1_5: ──────░──╫──╫──╫──╫──░──────
                    ░  ║  ║  ║  ║  ░
        c2: 4/═════════╩══╩══╬══╬═════════
                       0  1  ║  ║
        c3: 4/═══════════════╩══╩═════════
                             1  2

    Args:
        num_qubits (int):
            The number of qubits in the circuit.
        clbit_num_cluster (int, optional):
            The number of classical bits in each cluster. Defaults to 4.
        name (str | None, optional):
            The name of the circuit. Defaults to None.
    """

    if num_qubits % 2 != 0:
        raise ValueError("Number of qubits must be even number")
    if num_qubits < 4:
        raise ValueError(
            "Number of qubits must be greater than 4, "
            + "otherwise it will not any classical bits introduced."
        )
    if clbit_num_cluster < 1:
        raise ValueError("Number of classical bits must be greater than 0")

    qc = QuantumCircuit(num_qubits, name=name)

    for i in range(0, num_qubits, 2):
        qc.x(i)

    qc.barrier()

    for i in range(0, num_qubits - 2, 2):
        tmp_c = ClassicalRegister(clbit_num_cluster, f"c{i}")
        qc.add_register(tmp_c)

        qc.measure(i, tmp_c[(0 + int(i / 2)) % clbit_num_cluster])
        qc.measure(i + 1, tmp_c[(1 + int(i / 2)) % clbit_num_cluster])

    qc.barrier()

    for i in range(0, num_qubits - 2):
        qc.reset(i)

    return qc


def make_ghz_overlap_case(
    num_qubits: int,
    use_case: (str | Literal["00", "01", "10", "11", "x-init-ghz", "intracell-plus", "singlet"]),
) -> QuantumCircuit:
    """Generate a GHZ overlap test case.

    Args:
        num_qubits (int): The number of qubits.
        use_case (str | Literal["00", "01", "10", "11", "x-init-ghz", "intracell-plus", "singlet"]):
            The use case to generate. Options are:
            - "00", "01", "10", "11": GHZ states with different initializations.
            - "x-init-ghz": GHZ state with X gate on the first qubit before Hadamard and CNOTs.
            - "intracell-plus": Intracell recipe with plus state.
            - "singlet": Intracell recipe with singlet state.

    Returns:
        QuantumCircuit: The generated GHZ overlap test case.
    """

    if num_qubits % 2 != 0:
        raise ValueError("Number of qubits must be even number")
    if num_qubits < 0:
        raise ValueError("Number of qubits must be greater than 0")

    if use_case == "intracell-plus":
        return intracell(num_qubits, "plus", name="ghz_intracell_plus")
    if use_case == "singlet":
        return intracell(num_qubits, "singlet", name="ghz_singlet")
    if use_case == "x-init-ghz":
        qc = QuantumCircuit(num_qubits, name="ghz_x_init")
        qc.x(0)
        qc.h(0)
        for i in range(num_qubits - 1):
            qc.cx(i, i + 1)

        return qc

    if use_case not in ["00", "01", "10", "11"]:
        raise ValueError(f"Invalid case name: {use_case}.")

    qc = QuantumCircuit(num_qubits, name=f"ghz_{use_case}")

    for i in range(0, num_qubits, 2):
        if use_case[i % 2] == "1":
            qc.x(i)
        if use_case[(i + 1) % 2] == "1":
            qc.x(i + 1)

    return qc


def preparing_circuits_lib(
    raw_circuits_lib: dict[str, QuantumCircuit],
) -> dict[str, QuantumCircuit]:
    """Prepare a library of circuits for testing.

    Args:
        raw_circuits_lib (dict[str, QuantumCircuit]):
            A dictionary of circuit names and their corresponding QuantumCircuit objects.

    Returns:
        A dictionary of circuit names and their corresponding QuantumCircuit objects.
    """
    circuits_lib: dict[str, QuantumCircuit] = {}

    for circ_name, circuit in raw_circuits_lib.items():
        circuit.name = circ_name
        circuits_lib[circ_name] = circuit

    return circuits_lib
