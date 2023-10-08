from qiskit import QuantumCircuit, QuantumRegister
from typing import Literal, NamedTuple, Union

from ..recipe import Qurecipe


class TrivialParamagnet(Qurecipe):
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
        num_qubits (int): Number of qubits.
        name (str, optional): Name of case. Defaults to "trivialParamagnet".

    """

    def method(self) -> list[QuantumCircuit]:
        """Construct the example circuit.

        Returns:
            QuantumCircuit: The example circuit.
        """
        q = QuantumRegister(self.params.num_qubits, "q")
        qc = QuantumCircuit(q)
        qc.name = self.case_name
        
        [qc.h(q[i]) for i in range(self.params.num_qubits)]

        return [qc]

    def __init__(
        self,
        num_qubits: int,
        name: str = 'trivialPM',
    ) -> None:
        """Initializing the case.

        Args:
            num_qubits (int): The number of qubits for constructing the example circuit.
            name (str, optional): Name of case. Defaults to "trivialParamagnet".
        """

        self.case_name = 'trivialPM'
        self._initialize(
            name=name,
            num_qubits=num_qubits,
        )


class GHZ(Qurecipe):
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
        num_qubits (int): The number of qubits for constructing the example circuit.
        name (str, optional): Name of case. Defaults to "cat".

    """

    def method(self) -> list[QuantumCircuit]:
        """Construct the example circuit.

        Returns:
            QuantumCircuit: The example circuit.
        """
        q = QuantumRegister(self.params.num_qubits, "q")
        qc = QuantumCircuit(q)
        qc.h(q[0])
        [qc.cx(q[i], q[i+1]) for i in range(self.params.num_qubits-1)]

        return [qc]

    def __init__(
        self,
        num_qubits: int,
        name: str = 'cat', 
    ) -> None:
        """Initializing the case.

        Args:
            num_qubits (int): The number of qubits for constructing the example circuit.
            name (str, optional): Name of case. Defaults to "cat".
        """

        self.case_name = 'cat'
        self._initialize(
            name=name,
            num_qubits=num_qubits,
        )


class TopologicalParamagnet(Qurecipe):
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

    - Period boundary at 8 qubits:

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
        num_qubits (int): Number of qubits.
        border_cond (str, optional): Boundary condition is `open` or `period`.
            Defaults to "period".
            name (str, optional): Name of case. Defaults to "topParamagnet".

    Raises:
        ValueError: When given number of qubits is not even.

    """

    def method(self) -> list[QuantumCircuit]:
        """Construct the example circuit.

        Returns:
            QuantumCircuit: The example circuit.
        """

        qPairNum = int(self.params.num_qubits/2)
        border_cond = self.params.border_cond

        q = QuantumRegister(self.params.num_qubits, "q")
        qc = QuantumCircuit(q)
        [qc.h(q[i]) for i in range(self.params.num_qubits)]
        [qc.cz(q[2*j], q[2*j+1]) for j in range(qPairNum)]
        [qc.cz(q[(2*j+1)], q[(2*j+2) % (2*qPairNum)]) for j in range(
            qPairNum if border_cond == 'period' else qPairNum-1
        )]

        return [qc]

    class arguments(NamedTuple):
        num_qubits: int = 2
        """Number of qubits. Defaults to 2."""
        name: str = ''
        """Name of the circuit. Defaults to ''."""
        border_cond: Literal['open', 'period'] = 'open'
        """Border condition is 'open' or 'period'. Defaults to `'open`."""

    def __init__(
        self,
        num_qubits: int,
        border_cond: Literal['period', 'open'] = "period",
        name: str = "topParamagnet",
    ) -> None:
        """Initializing the case.

        Args:
            num_qubits (int): Number of qubits.
            border_cond (str, optional): Boundary condition is `open` or `period`.
                Defaults to "period".
            name (str, optional): Name of case. Defaults to "topParamagnet".

        Raises:
            ValueError: When given number of qubits is not even.
        """

        if num_qubits % 2 != 0:
            raise ValueError("Only lattices can construct using this gate.")

        self.case_name = f'cluster_{border_cond}'
        self.params: TopologicalParamagnet.arguments
        self._initialize(
            name=name,
            num_qubits=num_qubits,
            border_cond=border_cond,
        )


def Cluster(
    num_qubits: int,
    border_cond: Literal['period', 'open'] = "period",
    name: str = "topParamagnet",
) -> TopologicalParamagnet:
    """Another name of The entangled circuit `Topological paramagnet`.
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
        num_qubits (int): Number of qubits.
        border_cond (str, optional): Boundary condition is `open` or `period`.
            Defaults to "period".
            name (str, optional): Name of case. Defaults to "topParamagnet".

    Raises:
        ValueError: When given number of qubits is not even.
    """    
    
    return TopologicalParamagnet(
        num_qubits=num_qubits,
        border_cond=border_cond,
        name=name,
    )