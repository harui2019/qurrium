from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit.quantumcircuit import Qubit
from typing import Union, Sequence, Literal
from .case import Case

# Qubit type annotations.
QubitSpecifier = Union[
    Qubit,
    QuantumRegister,
    int,
    slice,
    Sequence[Union[Qubit, int]],
]


class trivialParamagnet(Case):
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

    """

    def _circuit(self) -> QuantumCircuit:
        """Construct the example circuit.

        Returns:
            QuantumCircuit: The example circuit.
        """
        q = QuantumRegister(self.num_qubits, "q")
        qc = QuantumCircuit(q)
        [qc.h(q[i]) for i in range(self.num_qubits)]

        return qc

    def __init__(
        self,
        numQubits: int,
    ) -> None:
        """Initializing the case.

        Args:
            numQubits (int): The number of qubits for constructing the example circuit.
        """

        super().__init__(
            name=f"trivialParamagnet",
            num_qubits=numQubits,
            params={},
            expected={
                'purity': {
                    'all': 0,
                },
                'entropy': {
                    'all': 1,
                },
            },
        )


class cat(Case):
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

    """

    def _circuit(self) -> QuantumCircuit:
        """Construct the example circuit.

        Returns:
            QuantumCircuit: The example circuit.
        """
        q = QuantumRegister(self.num_qubits, "q")
        qc = QuantumCircuit(q)
        qc.h(q[0])
        [qc.cx(q[i], q[i+1]) for i in range(self.num_qubits-1)]

        return qc

    def __init__(
        self,
        numQubits: int,
    ) -> None:
        """Initializing the case.

        Args:
            numQubits (int): The number of qubits for constructing the example circuit.
        """

        super().__init__(
            name=f"cat",
            num_qubits=numQubits,
            params={},
            expected={
                'purity': {
                    'half': 0.5,
                    '0': None,
                    'other': 0.5,
                },
                'entropy': {
                    'half': 1,
                    '0': None,
                    'other': 1,
                },
            },
        )


class topParamagnet(Case):
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
        boundaryCond (str, optional): Boundary condition is `open` or `period`.
            Defaults to "period".

    Raises:
        ValueError: When given number of qubits is not even.

    """

    def _circuit(self) -> QuantumCircuit:
        """Construct the example circuit.

        Returns:
            QuantumCircuit: The example circuit.
        """

        qPairNum = int(self.num_qubits/2)
        boundaryCond = self.params['boundaryCond']

        q = QuantumRegister(self.num_qubits, "q")
        qc = QuantumCircuit(q)
        [qc.h(q[i]) for i in range(self.num_qubits)]
        [qc.cz(q[2*j], q[2*j+1]) for j in range(qPairNum)]
        [qc.cz(q[(2*j+1)], q[(2*j+2) % (2*qPairNum)]) for j in range(
            qPairNum if boundaryCond == 'period' else qPairNum-1
        )]

        return qc

    def __init__(
        self,
        numQubits: int,
        boundaryCond: Literal['period', 'open'] = "period",
    ) -> None:
        """Initializing the case.

        Args:
            numQubits (int): Number of qubits.
            boundaryCond (str, optional): Boundary condition is `open` or `period`.
                Defaults to "period".

        Raises:
            ValueError: When given number of qubits is not even.
        """

        if numQubits % 2 != 0:
            raise ValueError("Only lattices can construct using this gate.")

        super().__init__(
            name=f"topParamagnet",
            num_qubits=numQubits,
            params={
                'boundaryCond': boundaryCond,
            },
            expected={
                'purity': {
                    ('open', 'half'): 0.5,
                    ('open', '0'): 0.5,
                    ('open', 'other'): 0.5,
                    ('period', 'half'): 0.25,
                    ('period', '0'): 0.25,
                    ('period', '1'): 0.5,
                    ('period', 'other'): 1,
                },
                'entropy': {
                    ('open', 'half'): 1,
                    ('open', '0'): 1,
                    ('open', 'other'): 1,
                    ('period', 'half'): 2,
                    ('period', '0'): 2,
                    ('period', '1'): 1,
                    ('period', 'other'): 0,
                },
            },
        )
