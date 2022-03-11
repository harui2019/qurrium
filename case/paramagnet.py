from qiskit import QuantumCircuit, QuantumRegister
from qiskit.quantum_info import Operator
from qiskit.circuit.controlledgate import ControlledGate
from qiskit.circuit.gate import Gate
from qiskit.circuit.quantumcircuit import Qubit
from qiskit.circuit.library.standard_gates.z import ZGate

from .case import Case

import numpy as np
from typing import Union, Sequence, Optional

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
        """_summary_

        Returns:
            QuantumCircuit: _description_
        """
        q = QuantumRegister(self.num_qubits, "q")
        qc = QuantumCircuit(q)
        [qc.h(q[i]) for i in range(self.num_qubits)]

        return qc

    def __init__(
        self,
        numQubits: int,
    ) -> None:
        """_summary_

        Args:
            numQubits (int): _description_
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
        """_summary_

        Returns:
            QuantumCircuit: _description_
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
        """_summary_

        Args:
            numQubits (int): _description_
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
        """_summary_

        Returns:
            QuantumCircuit: _description_
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
        boundaryCond: str = "period",
    ) -> None:
        """_summary_

        Args:
            numQubits (int): _description_
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
