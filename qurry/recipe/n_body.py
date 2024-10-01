"""
================================================================
Two Body Library (qurry.recipe.library.two_body)
================================================================

"""

from qiskit import QuantumRegister
from qiskit.circuit.library import BlueprintCircuit


class OneBody(BlueprintCircuit):
    """The product state circuit `one_body`. This is an abstract class."""

    @property
    def num_qubits(self) -> int:
        """The number of qubits.

        Returns:
            The number of qubits in the circuit.
        """
        return super().num_qubits

    @num_qubits.setter
    def num_qubits(self, num_qubits: int) -> None:
        """Set the number of qubits.

        Note that this changes the registers of the circuit.

        Args:
            num_qubits: The new number of qubits.
        """
        if num_qubits != self.num_qubits:
            self._invalidate()

            self.qregs = []
            if num_qubits is not None and num_qubits > 0:
                self.qregs = [QuantumRegister(num_qubits, name="q")]

    def _check_configuration(self, raise_on_failure: bool = True) -> bool:
        """Check if the current configuration is valid."""
        valid = True
        if self.num_qubits is None:
            valid = False
            if raise_on_failure:
                raise AttributeError("The number of qubits has not been set.")
        return valid


class TwoBody(BlueprintCircuit):
    """The entangled circuit `two_body`. This is an abstract class."""

    @property
    def num_qubits(self) -> int:
        """The number of qubits.

        Returns:
            The number of qubits in the circuit.
        """
        return super().num_qubits

    @num_qubits.setter
    def num_qubits(self, num_qubits: int) -> None:
        """Set the number of qubits.

        Note that this changes the registers of the circuit.

        Args:
            num_qubits: The new number of qubits.

        Raises:
            ValueError: If num_qubits is not even.
        """
        if num_qubits % 2 != 0:
            raise ValueError("Number of qubits must be even.")
        if num_qubits != self.num_qubits:
            self._invalidate()

            self.qregs = []
            if num_qubits is not None and num_qubits > 0:
                self.qregs = [QuantumRegister(num_qubits, name="q")]

    def _check_configuration(self, raise_on_failure: bool = True) -> bool:
        """Check if the current configuration is valid."""
        valid = True
        if self.num_qubits is None:
            valid = False
            if raise_on_failure:
                raise AttributeError("The number of qubits has not been set.")
        return valid
