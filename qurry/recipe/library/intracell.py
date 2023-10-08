from qiskit import QuantumCircuit, QuantumRegister
from typing import Literal, NamedTuple

from ..recipe import Qurecipe


class Intracell(Qurecipe):
    """The entangled circuit `intracell`.

    ### `intracell-minus`, `singlet` At 8 qubits:

    ```
        ┌───┐┌───┐     
    q0: ┤ X ├┤ H ├──■──
        ├───┤└───┘┌─┴─┐
    q1: ┤ X ├─────┤ X ├
        ├───┤┌───┐└───┘
    q2: ┤ X ├┤ H ├──■──
        ├───┤└───┘┌─┴─┐
    q3: ┤ X ├─────┤ X ├
        ├───┤┌───┐└───┘
    q4: ┤ X ├┤ H ├──■──
        ├───┤└───┘┌─┴─┐
    q5: ┤ X ├─────┤ X ├
        ├───┤┌───┐└───┘
    q6: ┤ X ├┤ H ├──■──
        ├───┤└───┘┌─┴─┐
    q7: ┤ X ├─────┤ X ├
        └───┘     └───┘
    ```

    ### `intracell-plus` At 8 qubits:

    ```
        ┌───┐     
    q0: ┤ H ├──■──
        ├───┤┌─┴─┐
    q1: ┤ X ├┤ X ├
        ├───┤└───┘
    q2: ┤ H ├──■──
        ├───┤┌─┴─┐
    q3: ┤ X ├┤ X ├
        ├───┤└───┘
    q4: ┤ H ├──■──
        ├───┤┌─┴─┐
    q5: ┤ X ├┤ X ├
        ├───┤└───┘
    q6: ┤ H ├──■──
        ├───┤┌─┴─┐
    q7: ┤ X ├┤ X ├
        └───┘└───┘
    ```

    Args:
        num_qubits (int): Number of qubits.
        state (str, optional): 
            Choosing the state. There are 'singlet', 'minus', 'plus' which 'minus' is same as 'singlet'.
            Defaults to "singlet".
        name (str, optional): Name of case. Defaults to "intracell".

    Raises:
        ValueError: When given number of qubits is not even.

    """

    def method(self) -> list[QuantumCircuit]:
        """Construct the example circuit.

        Returns:
            QuantumCircuit: The example circuit.
        """
        q = QuantumRegister(self.params.num_qubits)
        qc = QuantumCircuit(q)
        qc.name = self.case_name

        # intracell
        for i in range(0, self.params.num_qubits, 2):
            if self.params.state == 'minus' or self.params.state == 'singlet':
                qc.x(i)
            elif self.params.state == 'plus':
                ...
            else:
                raise ValueError(
                    f"Initial state is invalid: '{self.params.state}'.")
            qc.h(i)
            qc.x(i+1)
            qc.cx(i, i+1)

        return [qc]

    class arguments(NamedTuple):
        num_qubits: int = 1
        name: str = ''

        state: Literal['singlet', 'minus', 'plus'] = 'singlet'

    def __init__(
        self,
        num_qubits: int,
        state: Literal['singlet', 'minus', 'plus'] = 'singlet',
        name: str = "intracell",
    ) -> None:
        """Initializing the case.

        Args:
            num_qubits (int): Number of qubits.
            state (str, optional): 
                Choosing the state. There are 'singlet', 'minus', 'plus' which 'minus' is same as 'singlet'.
                Defaults to "singlet".
            name (str, optional): Name of case. Defaults to "intracell".

        Raises:
            ValueError: When given number of qubits is not even.
        """

        if num_qubits % 2 != 0:
            raise ValueError("Only lattices can construct using this gate.")

        self.case_name = f'intracell_{state}'
        self.params: Intracell.arguments
        self._initialize(
            name=name,
            num_qubits=num_qubits,
            state=state,
        )


def Singlet(
    num_qubits: int,
    name: str = "singlet",
) -> Intracell:
    """One of the state 'singlet' of The entangled circuit `intracell`.

    ### `intracell-minus`, `singlet` At 8 qubits:

    ```
        ┌───┐┌───┐     
    q0: ┤ X ├┤ H ├──■──
        ├───┤└───┘┌─┴─┐
    q1: ┤ X ├─────┤ X ├
        ├───┤┌───┐└───┘
    q2: ┤ X ├┤ H ├──■──
        ├───┤└───┘┌─┴─┐
    q3: ┤ X ├─────┤ X ├
        ├───┤┌───┐└───┘
    q4: ┤ X ├┤ H ├──■──
        ├───┤└───┘┌─┴─┐
    q5: ┤ X ├─────┤ X ├
        ├───┤┌───┐└───┘
    q6: ┤ X ├┤ H ├──■──
        ├───┤└───┘┌─┴─┐
    q7: ┤ X ├─────┤ X ├
        └───┘     └───┘
    ```

    Args:
        num_qubits (int): Number of qubits.
        name (str, optional): Name of case. Defaults to "intracell".

    Raises:
        ValueError: When given number of qubits is not even.
    """
    return Intracell(
        num_qubits=num_qubits,
        state='singlet',
        name=name,
    )
