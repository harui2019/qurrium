from qiskit import QuantumCircuit, QuantumRegister
from qiskit.quantum_info import Operator
from qiskit.circuit.gate import Gate
from typing import Union


def trivialParamagnet(
    numQubits: int,
    runBy: str = "gate",
) -> Union[Gate, Operator]:
    
    q = QuantumRegister(numQubits)
    qc = QuantumCircuit(q)
    [qc.h(q[i]) for i in range(numQubits)]
    
    GatedQC = qc.to_gate()
    GatedQC.name = f"trivPM"
    
    return (GatedQC if runBy == "gate" else Operator(qc))
