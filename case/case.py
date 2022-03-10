from qiskit import QuantumCircuit, QuantumRegister
from qiskit.quantum_info import Operator
from qiskit.circuit.gate import Gate
from qiskit.circuit.quantumcircuit import Qubit
from typing import Union, Sequence, Optional


class Case:
    def _circuit(self) -> QuantumCircuit:
        """_summary_

        Returns:
            QuantumCircuit: _description_
        """
        q = QuantumCircuit(self.num_qubits, "q")
        qc = QuantumCircuit(q)

        return qc

    def __init__(
        self,
        name: str,
        num_qubits: int,
        params: dict = {
            'boundary': None,
        },
        expected: dict = {
            'purity': None,
            'entropy': None,
        },
    ) -> None:
        """_summary_

        Args:
            name (str): _description_
            num_qubits (int): _description_
            params (_type_, optional): _description_. Defaults to { 'boundary': None, }.
            expected (_type_, optional): _description_. Defaults to { 'purity': None, 'entropy': None, }.
        """
        self.name = name
        self.num_qubits = num_qubits
        self.params = params
        self.expected = expected

        self.circuit = self._circuit()

    def gate(self) -> Gate:
        """_summary_

        Returns:
            Gate: _description_
        """

        gated = self.circuit.to_gate()
        gated.name = self.name

        return gated

    def operator(self) -> Operator:
        """_summary_

        Returns:
            Operator: _description_
        """

        return Operator(self.circuit)

    def wave(self) -> QuantumCircuit:
        return self.circuit.copy()
