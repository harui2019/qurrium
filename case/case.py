from qiskit import QuantumCircuit, QuantumRegister
from qiskit.quantum_info import Operator
from qiskit.circuit.gate import Gate
from qiskit.circuit.quantumcircuit import Qubit
from typing import Union, Sequence, Optional


class Case:
    def _circuit(self) -> QuantumCircuit:
        """Construct the example circuit.

        Returns:
            QuantumCircuit: The example circuit.
        """
        q = QuantumCircuit(self.num_qubits, "q")
        qc = QuantumCircuit(q)

        return qc

    def __init__(
        self,
        name: str,
        num_qubits: int,
        params: dict = {
            'boundaryCond': None,
        },
        expected: dict = {
            'purity': None,
            'entropy': None,
        },
    ) -> None:
        """Initializing the case.

        Args:
            name (str): The name of this circuit.
            num_qubits (int): The number of qubits for constructing the example circuit.
            params (dict, optional): Other parameters for this example, like boundary condition. 
                Defaults to { 'boundaryCond': None, }.
            expected (dict, optional): 
                Exact result of measure. 
                
                IF IT'S STILL UNKNOWN THEN DO NOT ENTER ANY VALUE.
                TO PREVENT THE MISLEADING OTHER USERS.
                
                Defaults to { 'purity': None, 'entropy': None, }.
        """
        self.name = name
        self.num_qubits = num_qubits
        self.params = params
        self.expected = expected

        self.circuit = self._circuit()

    def gate(self) -> Gate:
        """Return the example circuit as `Gate`.

        Returns:
            Gate: The example circuit.
        """

        gated = self.circuit.to_gate()
        gated.name = self.name

        return gated

    def operator(self) -> Operator:
        """Return the example circuit as `Operator`.

        Returns:
            Operator: The example circuit.
        """

        return Operator(self.circuit)

    def wave(self) -> QuantumCircuit:
        """Return a copy of the example circuit.

        Returns:
            QuantumCircuit: The example circuit.
        """        
        return self.circuit.copy()
