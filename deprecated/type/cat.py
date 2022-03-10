from qiskit import QuantumCircuit, QuantumRegister
from qiskit.quantum_info import Operator
from qiskit.circuit.gate import Gate
from typing import Union


def cat(
    numQubits: int,
    runBy: str = "gate",
) -> Union[Gate, Operator]:

    q = QuantumRegister(numQubits)
    qc = QuantumCircuit(q)
    qc.h(q[0])
    [qc.cx(q[i], q[i+1]) for i in range(numQubits-1)]

    GatedQC = qc.to_gate()
    GatedQC.name = f"cat"

    return (GatedQC if runBy == "gate" else Operator(qc))
