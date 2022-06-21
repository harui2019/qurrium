from qiskit import QuantumCircuit, QuantumRegister
from qiskit.quantum_info import Operator
from qiskit.circuit.gate import Gate
from qiskit.circuit.quantumcircuit import Qubit
from typing import Union, Sequence, Optional

from qiskit.circuit.controlledgate import ControlledGate
from qiskit.circuit.library.standard_gates.z import ZGate

# Deprecated

# Qubit type annotations.
QubitSpecifier = Union[
    Qubit,
    QuantumRegister,
    int,
    slice,
    Sequence[Union[Qubit, int]],
]


class CZEntangledGate(ControlledGate):
    r"""A specific gate is used in PhysRevLett.121.086808.

    The Original CZGate of qiskit is
    ```
    q1_0:   ───────■───────
            ┌───┐┌─┴─┐┌───┐
    q1_1:   ┤ H ├┤ X ├┤ H ├
            └───┘└───┘└───┘
    ```
    But in https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.121.086808
    It's denoted by this figure.
    ```
            ┌───┐     ┌───┐
    q1_0:   ┤ H ├──■──┤ H ├
            ├───┤┌─┴─┐├───┤
    q1_1:   ┤ H ├┤ X ├┤ H ├
            └───┘└───┘└───┘
    ```

    - *base on the source code of `CZGate`*

    """

    def __init__(self, label: Optional[str] = None, ctrl_state: Optional[Union[str, int]] = None):
        """Create new CZ gate."""
        super().__init__(
            "czEntangled", 2, [], label=label, num_ctrl_qubits=1, ctrl_state=ctrl_state, base_gate=ZGate()
        )

    def _define(self):
        # pylint: disable=cyclic-import
        from qiskit.circuit.quantumcircuit import QuantumCircuit
        from qiskit.circuit.library.standard_gates.h import HGate
        from qiskit.circuit.library.standard_gates.x import CXGate

        q = QuantumRegister(2, "q")
        qc = QuantumCircuit(q, name=self.name)
        rules = [
            (HGate(), [q[0]], []),
            (HGate(), [q[1]], []),
            (CXGate(), [q[0], q[1]], []),
            (HGate(), [q[0]], []),
            (HGate(), [q[1]], []),
        ]
        for instr, qargs, cargs in rules:
            qc._append(instr, qargs, cargs)

        self.definition = qc

    def inverse(self):
        """Return inverted CZ gate (itself)."""
        return CZEntangledGate(ctrl_state=self.ctrl_state)  # self-inverse

    # def __array__(self, dtype=None):
    #     """Return a numpy.array for the CZ gate."""
    #     if self.ctrl_state:
    #         return np.array(
    #             [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, -1]], dtype=dtype
    #         )
    #     else:
    #         return np.array(
    #             [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]], dtype=dtype
    #         )


def CZEntangled(
    qc: QuantumCircuit,
    q0: QubitSpecifier,
    q1: QubitSpecifier,
) -> Gate:
    """A specific gate is used in PhysRevLett.121.086808.

    The Original CZGate of qiskit is
    ```
    q1_0:   ───────■───────
            ┌───┐┌─┴─┐┌───┐
    q1_1:   ┤ H ├┤ X ├┤ H ├
            └───┘└───┘└───┘
    ```
    But in https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.121.086808
    It's denoted by this figure.
    ```
            ┌───┐     ┌───┐
    q1_0:   ┤ H ├──■──┤ H ├
            ├───┤┌─┴─┐├───┤
    q1_1:   ┤ H ├┤ X ├┤ H ├
            └───┘└───┘└───┘
    ```
    """

    qDummy = QuantumRegister(2)
    qcDummy = QuantumCircuit(qDummy)
    qcDummy.h(qDummy[0])
    qcDummy.cz(qDummy[0], qDummy[1])
    qcDummy.h(qDummy[0])

    GatedQC = qcDummy.to_gate()
    GatedQC.name = f"CZEnt"

    return qc.append(GatedQC, [q0, q1])


def trivialParamagnet(
    numQubits: int,
    runBy: str = "gate",
) -> Union[Gate, Operator]:
    """The entangled circuit `trivial paramagnet`.
    Introduce in https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.121.086808 .

    ### At 8 qubits:

    ```
        ┌───┐
    q0: ┤ H ├
        ├───┤
    q1: ┤ H ├
        ├───┤
    q2: ┤ H ├
        ├───┤
    q3: ┤ H ├
        ├───┤
    q4: ┤ H ├
        ├───┤
    q5: ┤ H ├
        ├───┤
    q6: ┤ H ├
        ├───┤
    q7: ┤ H ├
        └───┘      
    ```

    - Measureing entropy on `Aer.get_backend('aer_simulator')`.

    ```txt
        +----------------+---------+--------+---------------+
        | Freedom degree | Entropy | Purity | Method        |
        +================+=========+========+===============+
        | half qubits    | 0       | 1      | hadamard test |
        |                +---------+--------+---------------+
        |                | 0       | 1      | haar measure  |
        +----------------+---------+--------+---------------+
        | any number     | 0       | 1      | hadamard test |
        |                +---------+--------+---------------+
        |                | 0       | 1      | haar measure  |
        +----------------+---------+--------+---------------+
    ```

    Args:
        numQubits (int): Number of qubits.
        runBy (str, optional): Running as `Gate` or `Operator`.
            Defaults to "gate".

    Returns:
        Union[Gate, Operator]: `trivialParamagnet`
    """

    q = QuantumRegister(numQubits)
    qc = QuantumCircuit(q)
    [qc.h(q[i]) for i in range(numQubits)]

    GatedQC = qc.to_gate()
    GatedQC.name = f"trivPM"

    return (GatedQC if runBy == "gate" else Operator(qc))


def cat(
    numQubits: int,
    runBy: str = "gate",
) -> Union[Gate, Operator]:
    """The entangled circuit `GHZ` (as known as `cat`).
    Introduce in https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.121.086808 .

    ### Open boundary at 8 qubits:

    ```
        ┌───┐                                    
    q0: ┤ H ├──■────────────────────────────────
        └───┘┌─┴─┐                              
    q1: ─────┤ X ├──■───────────────────────────
             └───┘┌─┴─┐                         
    q2: ──────────┤ X ├──■──────────────────────
                  └───┘┌─┴─┐                    
    q3: ───────────────┤ X ├──■─────────────────
                       └───┘┌─┴─┐               
    q4: ────────────────────┤ X ├──■────────────
                            └───┘┌─┴─┐          
    q5: ─────────────────────────┤ X ├──■───────
                                 └───┘┌─┴─┐     
    q6: ──────────────────────────────┤ X ├──■──
                                      └───┘┌─┴─┐
    q7: ───────────────────────────────────┤ X ├
                                           └───┘
    ```

    - Measureing entropy on `Aer.get_backend('aer_simulator')`.

    ```txt
    +----------------+---------+--------+---------------+
    | Freedom degree | Entropy | Purity | Method        |
    +================+=========+========+===============+
    | half qubits    | 1       | 0.5    | hadamard test |
    |                +---------+--------+---------------+
    |                | 1       | 0.5    | haar measure  |
    +----------------+---------+--------+---------------+
    | any number     | 1       | 0.5    | hadamard test |
    |                +---------+--------+---------------+
    |                | 1       | 0.5    | haar measure  |
    +----------------+---------+--------+---------------+
    | 0              | Nan     | Nan    | hadamard test |
    |                +---------+--------+---------------+
    |                | Nan     | Nan    | haar measure  |
    +----------------+---------+--------+---------------+
    ```

    Args:
        numQubits (int): Number of qubits.
        runBy (str, optional): Running as `Gate` or `Operator`.
            Defaults to "gate".
        boundaryCond (str, optional): Boundary condition is `open` or `period`.
            Defaults to "period".

    Raises:
        ValueError: When given number of qubits is not even.

    Returns:
        Union[Gate, Operator]: `GHZ` (as known as `cat`)
    """

    q = QuantumRegister(numQubits)
    qc = QuantumCircuit(q)
    qc.h(q[0])
    [qc.cx(q[i], q[i+1]) for i in range(numQubits-1)]

    GatedQC = qc.to_gate()
    GatedQC.name = f"cat"

    return (GatedQC if runBy == "gate" else Operator(qc))


def topParamagnetWrong(
    numQubits: int,
    runBy: str = "gate",
) -> Union[Gate, Operator]:
    """The entangled circuit `trivial paramagnet`.
    Introduce in https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.121.086808 .

    - With `CZEntangled`.

    ### At 8 qubits:

    ```
        ┌───┐┌────────┐                              »
    q0: ┤ H ├┤0       ├──────────────────────────────»
        ├───┤│  CZEnt │┌────────┐                    »
    q1: ┤ H ├┤1       ├┤0       ├────────────────────»
        ├───┤└────────┘│  CZEnt │┌────────┐          »
    q2: ┤ H ├──────────┤1       ├┤0       ├──────────»
        ├───┤          └────────┘│  CZEnt │┌────────┐»
    q3: ┤ H ├────────────────────┤1       ├┤0       ├»
        ├───┤                    └────────┘│  CZEnt │»
    q4: ┤ H ├──────────────────────────────┤1       ├»
        ├───┤                              └────────┘»
    q5: ┤ H ├────────────────────────────────────────»
        ├───┤                                        »
    q6: ┤ H ├────────────────────────────────────────»
        ├───┤                                        »
    q7: ┤ H ├────────────────────────────────────────»
        └───┘                                        »
    «                                  ┌────────┐
    «q0: ──────────────────────────────┤1       ├
    «                                  │        │
    «q1: ──────────────────────────────┤        ├
    «                                  │        │
    «q2: ──────────────────────────────┤        ├
    «                                  │        │
    «q3: ──────────────────────────────┤        ├
    «    ┌────────┐                    │  CZEnt │
    «q4: ┤0       ├────────────────────┤        ├
    «    │  CZEnt │┌────────┐          │        │
    «q5: ┤1       ├┤0       ├──────────┤        ├
    «    └────────┘│  CZEnt │┌────────┐│        │
    «q6: ──────────┤1       ├┤0       ├┤        ├
    «              └────────┘│  CZEnt ││        │
    «q7: ────────────────────┤1       ├┤0       ├
    «                        └────────┘└────────┘
    ```

    - Measureing entropy on `Aer.get_backend('aer_simulator')`.

    ```txt
    +----------------+---------+--------+---------------+
    | Freedom degree | Entropy | Purity | Method        |
    +================+=========+========+===============+
    | half qubits    | 0       | 1      | hadamard test |
    |                +---------+--------+---------------+
    |                | 0       | 1      | haar measure  |
    +----------------+---------+--------+---------------+
    | any number     | 0       | 1      | hadamard test |
    |                +---------+--------+---------------+
    |                | 0       | 1      | haar measure  |
    +----------------+---------+--------+---------------+
    ```

    Args:
        numQubits (int): Number of qubits.
        runBy (str, optional): Running as `Gate` or `Operator`.
            Defaults to "gate".

    Returns:
        Union[Gate, Operator]: `trivialParamagnet`
    """

    q = QuantumRegister(numQubits)
    qc = QuantumCircuit(q)
    [qc.h(q[i]) for i in range(numQubits)]
    [CZEntangled(qc, q[i % numQubits], q[(i+1) % numQubits])
     for i in range(numQubits)]

    GatedQC = qc.to_gate()
    GatedQC.name = f"topPM"

    return (GatedQC if runBy == "gate" else Operator(qc))


def topParamagnet(
    numQubits: int,
    runBy: str = "gate",
    boundaryCond: str = "period",
) -> Union[Gate, Operator]:
    """The entangled circuit `Topological paramagnet`.
    Introduce in https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.121.086808 .

    - With `CZEntangled`.

    ### Open boundary at 8 qubits:

    ```
        ┌───┐┌────────┐          
    q_0:┤ H ├┤0       ├──────────
        ├───┤│  CZEnt │┌────────┐
    q_1:┤ H ├┤1       ├┤0       ├
        ├───┤├────────┤│  CZEnt │
    q_2:┤ H ├┤0       ├┤1       ├
        ├───┤│  CZEnt │├────────┤
    q_3:┤ H ├┤1       ├┤0       ├
        ├───┤├────────┤│  CZEnt │
    q_4:┤ H ├┤0       ├┤1       ├
        ├───┤│  CZEnt │├────────┤
    q_5:┤ H ├┤1       ├┤0       ├
        ├───┤├────────┤│  CZEnt │
    q_6:┤ H ├┤0       ├┤1       ├
        ├───┤│  CZEnt │└────────┘
    q_7:┤ H ├┤1       ├──────────
        └───┘└────────┘         
    ```

    - Measureing entropy on `Aer.get_backend('aer_simulator')`.

    ```txt
        +----------------+---------+--------+---------------+
        | Freedom degree | Entropy | Purity | Method        |
        +================+=========+========+===============+
        | half qubits    | 0       | 1      | hadamard test |
        |                +---------+--------+---------------+
        |                | 0       | 1      | haar measure  |
        +----------------+---------+--------+---------------+
        | any number     | 0       | 1      | hadamard test |
        |                +---------+--------+---------------+
        |                | 0       | 1      | haar measure  |
        +----------------+---------+--------+---------------+
    ```

    - Open boundary at 8 qubits:

    ```
        ┌───┐┌────────┐          ┌────────┐
    q0: ┤ H ├┤0       ├──────────┤1       ├
        ├───┤│  CZEnt │┌────────┐│        │
    q1: ┤ H ├┤1       ├┤0       ├┤        ├
        ├───┤├────────┤│  CZEnt ││        │
    q2: ┤ H ├┤0       ├┤1       ├┤        ├
        ├───┤│  CZEnt │├────────┤│        │
    q3: ┤ H ├┤1       ├┤0       ├┤        ├
        ├───┤├────────┤│  CZEnt ││  CZEnt │
    q4: ┤ H ├┤0       ├┤1       ├┤        ├
        ├───┤│  CZEnt │├────────┤│        │
    q5: ┤ H ├┤1       ├┤0       ├┤        ├
        ├───┤├────────┤│  CZEnt ││        │
    q6: ┤ H ├┤0       ├┤1       ├┤        ├
        ├───┤│  CZEnt │└────────┘│        │
    q7: ┤ H ├┤1       ├──────────┤0       ├
        └───┘└────────┘          └────────┘
    ```

    - Measureing entropy on `Aer.get_backend('aer_simulator')`.

    ```txt
    +----------------+---------+--------+---------------+
    | Freedom degree | Entropy | Purity | Method        |
    +================+=========+========+===============+
    | half qubits    | 0       | 1      | hadamard test |
    |                +---------+--------+---------------+
    |                | 0       | 1      | haar measure  |
    +----------------+---------+--------+---------------+
    | any number     | 0       | 1      | hadamard test |
    |                +---------+--------+---------------+
    |                | 0       | 1      | haar measure  |
    +----------------+---------+--------+---------------+
    ```

    Args:
        numQubits (int): Number of qubits.
        runBy (str, optional): Running as `Gate` or `Operator`.
            Defaults to "gate".
        boundaryCond (str, optional): Boundary condition is `open` or `period`.
            Defaults to "period".

    Raises:
        ValueError: When given number of qubits is not even.

    Returns:
        Union[Gate, Operator]: `Topological paramagnet`
    """

    if numQubits % 2 != 0:
        raise ValueError("Only lattices can construct using this gate.")
    qPairNum = int(numQubits/2)

    q = QuantumRegister(numQubits)
    qc = QuantumCircuit(q)
    [qc.h(q[i]) for i in range(numQubits)]
    [CZEntangled(qc, q[2*j], q[2*j+1]) for j in range(qPairNum)]
    [CZEntangled(qc, q[(2*j+1)], q[(2*j+2) % (2*qPairNum)]) for j in range(
        qPairNum if boundaryCond == 'period' else qPairNum-1
    )]

    GatedQC = qc.to_gate()
    GatedQC.name = f"topPM"

    return (GatedQC if runBy == "gate" else Operator(qc))


def topParamagnetReverse(
    numQubits: int,
    runBy: str = "gate",
    boundaryCond: str = "period",
) -> Union[Gate, Operator]:
    """The entangled circuit `Topological paramagnet`.
    Introduce in https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.121.086808 .

    - With `CZEntangled`.

    ### Open boundary at 8 qubits:

    ```
        ┌───┐          ┌────────┐
    q0: ┤ H ├──────────┤0       ├
        ├───┤┌────────┐│  CZEnt │
    q1: ┤ H ├┤0       ├┤1       ├
        ├───┤│  CZEnt │├────────┤
    q2: ┤ H ├┤1       ├┤0       ├
        ├───┤├────────┤│  CZEnt │
    q3: ┤ H ├┤0       ├┤1       ├
        ├───┤│  CZEnt │├────────┤
    q4: ┤ H ├┤1       ├┤0       ├
        ├───┤├────────┤│  CZEnt │
    q5: ┤ H ├┤0       ├┤1       ├
        ├───┤│  CZEnt │├────────┤
    q6: ┤ H ├┤1       ├┤0       ├
        ├───┤└────────┘│  CZEnt │
    q7: ┤ H ├──────────┤1       ├
        └───┘          └────────┘ 
    ```

    - Measureing entropy on `Aer.get_backend('aer_simulator')`.

    ```txt
        +----------------+---------+--------+---------------+
        | Freedom degree | Entropy | Purity | Method        |
        +================+=========+========+===============+
        | half qubits    | 0       | 1      | hadamard test |
        |                +---------+--------+---------------+
        |                | 0       | 1      | haar measure  |
        +----------------+---------+--------+---------------+
        | any number     | 0       | 1      | hadamard test |
        |                +---------+--------+---------------+
        |                | 0       | 1      | haar measure  |
        +----------------+---------+--------+---------------+
    ```

    ### Open boundary at 8 qubits:

    ```
        ┌───┐          ┌────────┐┌────────┐
    q0: ┤ H ├──────────┤1       ├┤0       ├
        ├───┤┌────────┐│        ││  CZEnt │
    q1: ┤ H ├┤0       ├┤        ├┤1       ├
        ├───┤│  CZEnt ││        │├────────┤
    q2: ┤ H ├┤1       ├┤        ├┤0       ├
        ├───┤├────────┤│        ││  CZEnt │
    q3: ┤ H ├┤0       ├┤        ├┤1       ├
        ├───┤│  CZEnt ││  CZEnt │├────────┤
    q4: ┤ H ├┤1       ├┤        ├┤0       ├
        ├───┤├────────┤│        ││  CZEnt │
    q5: ┤ H ├┤0       ├┤        ├┤1       ├
        ├───┤│  CZEnt ││        │├────────┤
    q6: ┤ H ├┤1       ├┤        ├┤0       ├
        ├───┤└────────┘│        ││  CZEnt │
    q7: ┤ H ├──────────┤0       ├┤1       ├
        └───┘          └────────┘└────────┘
    ```

    - Measureing entropy on `Aer.get_backend('aer_simulator')`.

    ```txt
    +----------------+---------+--------+---------------+
    | Freedom degree | Entropy | Purity | Method        |
    +================+=========+========+===============+
    | half qubits    | 0       | 1      | hadamard test |
    |                +---------+--------+---------------+
    |                | 0       | 1      | haar measure  |
    +----------------+---------+--------+---------------+
    | any number     | 0       | 1      | hadamard test |
    |                +---------+--------+---------------+
    |                | 0       | 1      | haar measure  |
    +----------------+---------+--------+---------------+
    ```

    Args:
        numQubits (int): Number of qubits.
        runBy (str, optional): Running as `Gate` or `Operator`.
            Defaults to "gate".
        boundaryCond (str, optional): Boundary condition is `open` or `period`.
            Defaults to "period".

    Raises:
        ValueError: When given number of qubits is not even.

    Returns:
        Union[Gate, Operator]: `Topological paramagnet`
    """

    if numQubits % 2 != 0:
        raise ValueError("Only lattices can construct using this gate.")
    qPairNum = int(numQubits/2)

    q = QuantumRegister(numQubits)
    qc = QuantumCircuit(q)
    [qc.h(q[i]) for i in range(numQubits)]
    [CZEntangled(qc, q[(2*j+1)], q[(2*j+2) % (2*qPairNum)]) for j in range(
        qPairNum if boundaryCond == 'period' else qPairNum-1
    )]
    [CZEntangled(qc, q[2*j], q[2*j+1]) for j in range(qPairNum)]

    GatedQC = qc.to_gate()
    GatedQC.name = f"topPM"

    return (GatedQC if runBy == "gate" else Operator(qc))


def topParamagnetCZ(
    numQubits: int,
    runBy: str = "gate",
    boundaryCond: str = "period",
) -> Union[Gate, Operator]:
    """The entangled circuit `Topological paramagnet`.
    Introduce in https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.121.086808 .

    - With ACTUAL `CZGate`.

    - Open boundary at 8 qubits:

    ```
        ┌───┐      
    q0: ┤ H ├─■────
        ├───┤ │    
    q1: ┤ H ├─■──■─
        ├───┤    │ 
    q2: ┤ H ├─■──■─
        ├───┤ │    
    q3: ┤ H ├─■──■─
        ├───┤    │ 
    q4: ┤ H ├─■──■─
        ├───┤ │    
    q5: ┤ H ├─■──■─
        ├───┤    │ 
    q6: ┤ H ├─■──■─
        ├───┤ │    
    q7: ┤ H ├─■────
        └───┘         
    ```

    - Measureing entropy on `Aer.get_backend('aer_simulator')`.
        - Haar measure of 1 degree is more stable than other.

    ```txt
    +----------------+---------+--------+---------------+
    | Freedom degree | Entropy | Purity | method        |
    +================+=========+========+===============+
    | half qubits    | 1       | 0.5    | hadamard test |
    |                +---------+--------+---------------+
    |                | 1       | 0.5    | haar measure  |
    +----------------+---------+--------+---------------+
    | other number   | 1       | 0.5    | hadamard test |
    |                +---------+--------+---------------+
    |                | 1       | 0.5    | haar measure  |
    +----------------+---------+--------+---------------+
    | 1              | 1       | 0.5    | hadamard test |
    |                +---------+--------+---------------+
    |                | 1       | 0.5    | haar measure  |
    +----------------+---------+--------+---------------+
    | 0              | 0       | 1      | hadamard test |
    |                +---------+--------+---------------+
    |                | 0       | 1      | haar measure  |
    +----------------+---------+--------+---------------+
    ```

    - Open boundary at 8 qubits:

    ```
        ┌───┐         
    q0: ┤ H ├─■─────■─
        ├───┤ │     │ 
    q1: ┤ H ├─■──■──┼─
        ├───┤    │  │ 
    q2: ┤ H ├─■──■──┼─
        ├───┤ │     │ 
    q3: ┤ H ├─■──■──┼─
        ├───┤    │  │ 
    q4: ┤ H ├─■──■──┼─
        ├───┤ │     │ 
    q5: ┤ H ├─■──■──┼─
        ├───┤    │  │ 
    q6: ┤ H ├─■──■──┼─
        ├───┤ │     │ 
    q7: ┤ H ├─■─────■─
        └───┘              
    ```

    - Measureing entropy on `Aer.get_backend('aer_simulator')`.

    ```txt
    +----------------+---------+--------+---------------+
    | Freedom degree | Entropy | Purity | method        |
    +================+=========+========+===============+
    | half qubits    | 2       | 0.25   | hadamard test |
    |                +---------+--------+---------------+
    |                | 2       | 0.25   | haar measure  |
    +----------------+---------+--------+---------------+
    | other number   | 2       | 0.25   | hadamard test |
    |                +---------+--------+---------------+
    |                | 2       | 0.25   | haar measure  |
    +----------------+---------+--------+---------------+
    | 1              | 1       | 0.5    | hadamard test |
    |                +---------+--------+---------------+
    |                | 1       | 0.5    | haar measure  |
    +----------------+---------+--------+---------------+
    | 0              | 0       | 1      | hadamard test |
    |                +---------+--------+---------------+
    |                | 0       | 1      | haar measure  |
    +----------------+---------+--------+---------------+
    ```

    Args:
        numQubits (int): Number of qubits.
        runBy (str, optional): Running as `Gate` or `Operator`.
            Defaults to "gate".
        boundaryCond (str, optional): Boundary condition is `open` or `period`.
            Defaults to "period".

    Raises:
        ValueError: When given number of qubits is not even.

    Returns:
        Union[Gate, Operator]: `Topological paramagnet`
    """

    if numQubits % 2 != 0:
        raise ValueError("Only lattices can construct using this gate.")
    qPairNum = int(numQubits/2)

    q = QuantumRegister(numQubits)
    qc = QuantumCircuit(q)
    [qc.h(q[i]) for i in range(numQubits)]
    [qc.cz(q[2*j], q[2*j+1]) for j in range(qPairNum)]
    [qc.cz(q[(2*j+1)], q[(2*j+2) % (2*qPairNum)]) for j in range(
        qPairNum if boundaryCond == 'period' else qPairNum-1
    )]

    GatedQC = qc.to_gate()
    GatedQC.name = f"topPMCZ"

    return (GatedQC if runBy == "gate" else Operator(qc))


def topParamagnetCZReverse(
    numQubits: int,
    runBy: str = "gate",
    boundaryCond: str = "period",
) -> Union[Gate, Operator]:
    """The entangled circuit `Topological paramagnet`.
    Introduce in https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.121.086808 .

    - With `CZGate`.

    ### Open boundary at 8 qubits:

    ```
        ┌───┐      
    q0: ┤ H ├────■─
        ├───┤    │ 
    q1: ┤ H ├─■──■─
        ├───┤ │    
    q2: ┤ H ├─■──■─
        ├───┤    │ 
    q3: ┤ H ├─■──■─
        ├───┤ │    
    q4: ┤ H ├─■──■─
        ├───┤    │ 
    q5: ┤ H ├─■──■─
        ├───┤ │    
    q6: ┤ H ├─■──■─
        ├───┤    │ 
    q7: ┤ H ├────■─
        └───┘      
    ```

    - Measureing entropy on `Aer.get_backend('aer_simulator')`.

    ```txt
    +----------------+---------+--------+---------------+
    | Freedom degree | Entropy | Purity | method        |
    +================+=========+========+===============+
    | half qubits    | 1       | 0.5    | hadamard test |
    |                +---------+--------+---------------+
    |                | 1       | 0.5    | haar measure  |
    +----------------+---------+--------+---------------+
    | other number   | 1       | 0.5    | hadamard test |
    |                +---------+--------+---------------+
    |                | 1       | 0.5    | haar measure  |
    +----------------+---------+--------+---------------+
    | 1              | 0       | 1      | hadamard test |
    |                +---------+--------+---------------+
    |                | 0       | 1      | haar measure  |
    +----------------+---------+--------+---------------+
    ```

    ### Open boundary at 8 qubits:

    ```
        ┌───┐         
    q0: ┤ H ├────■──■─
        ├───┤    │  │ 
    q1: ┤ H ├─■──┼──■─
        ├───┤ │  │    
    q2: ┤ H ├─■──┼──■─
        ├───┤    │  │ 
    q3: ┤ H ├─■──┼──■─
        ├───┤ │  │    
    q4: ┤ H ├─■──┼──■─
        ├───┤    │  │ 
    q5: ┤ H ├─■──┼──■─
        ├───┤ │  │    
    q6: ┤ H ├─■──┼──■─
        ├───┤    │  │ 
    q7: ┤ H ├────■──■─
        └───┘        
    ```

    - Measureing entropy on `Aer.get_backend('aer_simulator')`.

    ```txt
    +----------------+---------+--------+---------------+
    | Freedom degree | Entropy | Purity | method        |
    +================+=========+========+===============+
    | half qubits    | 2       | 0.25   | hadamard test |
    |                +---------+--------+---------------+
    |                | 2       | 0.25   | haar measure  |
    +----------------+---------+--------+---------------+
    | other number   | 2       | 0.25   | hadamard test |
    |                +---------+--------+---------------+
    |                | 2       | 0.25   | haar measure  |
    +----------------+---------+--------+---------------+
    | 1              | 1       | 0.5    | hadamard test |
    |                +---------+--------+---------------+
    |                | 1       | 0.5    | haar measure  |
    +----------------+---------+--------+---------------+
    | 0              | 0       | 1      | hadamard test |
    |                +---------+--------+---------------+
    |                | 0       | 1      | haar measure  |
    +----------------+---------+--------+---------------+
    ```

    Args:
        numQubits (int): Number of qubits.
        runBy (str, optional): Running as `Gate` or `Operator`.
            Defaults to "gate".
        boundaryCond (str, optional): Boundary condition is `open` or `period`.
            Defaults to "period".

    Raises:
        ValueError: When given number of qubits is not even.

    Returns:
        Union[Gate, Operator]: `Topological paramagnet`
    """

    if numQubits % 2 != 0:
        raise ValueError("Only lattices can construct using this gate.")
    qPairNum = int(numQubits/2)

    q = QuantumRegister(numQubits)
    qc = QuantumCircuit(q)
    [qc.h(q[i]) for i in range(numQubits)]
    [qc.cz(q[(2*j+1)], q[(2*j+2) % (2*qPairNum)]) for j in range(
        qPairNum if boundaryCond == 'period' else qPairNum-1
    )]
    [qc.cz(q[2*j], q[2*j+1]) for j in range(qPairNum)]

    GatedQC = qc.to_gate()
    GatedQC.name = f"topPMCZ"

    return (GatedQC if runBy == "gate" else Operator(qc))
