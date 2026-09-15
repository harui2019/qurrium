"""Intracell (:mod:`qurry.recipe.simple.intracell_cluster`)"""

from typing import Literal

from qiskit import QuantumCircuit


class Intracell(QuantumCircuit):
    r"""The entangled circuit :class:`~qurry.recipe.simple.intracell_cluster.Intracell`."""

    @property
    def state(self) -> Literal["singlet", "minus", "plus"]:
        """The state of the circuit.

        Returns:
            The state of the circuit.
        """
        return self._state

    @state.setter
    def state(self, state: Literal["singlet", "minus", "plus"]) -> None:
        """Set the state of the circuit.

        Args:
            state: The new state of the circuit.
        """
        if hasattr(self, "_state"):
            raise AttributeError("Attribute 'state' is read-only.")
        if state not in ["singlet", "minus", "plus"]:
            raise ValueError(f"Initial state is invalid: '{state}'.")
        self._state: Literal["singlet", "minus", "plus"] = state

    def __init__(
        self,
        num_qubits: int,
        state: Literal["singlet", "minus", "plus"] = "singlet",
        name: str = "intracell",
    ) -> None:
        """Initializing the case.

        Args:
            num_qubits (int): Number of qubits.
            state (str, optional):
                Choosing the state. There are 'singlet', 'minus', 'plus'
                which 'minus' is same as 'singlet'.
                Defaults to "singlet".
            name (str, optional): Name of case. Defaults to "intracell".

        Raises:
            ValueError: When given number of qubits is not even.
            ValueError: When given state is invalid.
        """

        super().__init__(num_qubits, name=name)
        self.state = state


def intracell(
    num_qubits: int, state: Literal["singlet", "minus", "plus"] = "singlet", name: str = "intracell"
) -> Intracell:
    r"""Generate the intracell state circuit.

    .. code-block:: text

        # At state `singlet`, `minus` a.k.a. `Singlet` with 8 qubits:
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

    .. math::

        \frac{1}{\sqrt{2}}
            \left({|01\rangle} - {|10\rangle} \right)^{\otimes N/2}, N = 8

    .. code-block:: text

        # At state `plus` with 8 qubits:
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

    .. math::

        \frac{1}{\sqrt{2}}
            \left({|01\rangle} + {|10\rangle} \right)^{\otimes N/2}, N = 8

    Args:
        num_qubits (int): Number of qubits.
        state (str, optional):
            Choosing the state. There are 'singlet', 'minus', 'plus'
            which 'minus' is same as 'singlet'.
            Defaults to "singlet".
        name (str, optional): Name of case. Defaults to "intracell".

    Returns:
        Intracell: The intracell state circuit.
    """
    qc = Intracell(num_qubits=num_qubits, state=state, name=name)
    if num_qubits == 0:
        return qc

    for i in range(0, num_qubits, 2):
        if qc.state in ["minus", "singlet"]:
            qc.x(i)
        qc.h(i)
        qc.x(i + 1)
        qc.cx(i, i + 1)
    return qc


def singlet(num_qubits: int, name: str = "singlet") -> Intracell:
    r""":class:`~qurry.recipe.simple.intracell_cluster.Singlet`, the entangled circuit
    :class:`~qurry.recipe.simple.intracell_cluster.Intracell` with `singlet` state.

    .. code-block:: text

        # At 8 qubits:
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

    .. math::

        \frac{1}{\sqrt{2}}
            \left({|01\rangle} - {|10\rangle} \right)^{\otimes N/2}, N = 8

    Args:
        num_qubits (int): Number of qubits.
        name (str, optional): Name of case. Defaults to "singlet".

    Raises:
        ValueError: When given number of qubits is not even.
    """
    return intracell(num_qubits=num_qubits, state="singlet", name=name)
