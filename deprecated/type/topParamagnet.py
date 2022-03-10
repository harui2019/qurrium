from qiskit import QuantumCircuit, QuantumRegister
from qiskit.quantum_info import Operator
from qiskit.circuit.gate import Gate
from qiskit.circuit.quantumcircuit import Qubit
from typing import Union, Sequence

QubitSpecifier = Union[
    Qubit,
    QuantumRegister,
    int,
    slice,
    Sequence[Union[Qubit, int]],
]


def CZEntangled(
    qc: QuantumCircuit,
    q0: QubitSpecifier,
    q1: QubitSpecifier,
) -> Gate:
    """[summary]

    The Original CZGate of qiskit is

    q1_0:   ───────■───────
            ┌───┐┌─┴─┐┌───┐
    q1_1:   ┤ H ├┤ X ├┤ H ├
            └───┘└───┘└───┘
    But we need

            ┌───┐     ┌───┐
    q1_0:   ┤ H ├──■──┤ H ├
            ├───┤┌─┴─┐├───┤
    q1_1:   ┤ H ├┤ X ├┤ H ├
            └───┘└───┘└───┘
    """

    qDummy = QuantumRegister(2)
    qcDummy = QuantumCircuit(qDummy)
    qcDummy.h(qDummy[0])
    qcDummy.cz(qDummy[0], qDummy[1])
    qcDummy.h(qDummy[0])

    GatedQC = qcDummy.to_gate()
    GatedQC.name = f"CZEnt"

    return qc.append(GatedQC, [q0, q1])


def topParamagnetWrong(
    numQubits: int,
    runBy: str = "gate",
    boundaryCond: str = "period",
) -> Union[Gate, Operator]:

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
