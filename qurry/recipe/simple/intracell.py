"""
================================================================
Intracell (:mod:`qurry.recipe.library.simple.intracell`)
================================================================

"""

from typing import Literal

from ..n_body import TwoBody


class Intracell(TwoBody):
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
            Choosing the state. There are 'singlet', 'minus', 'plus'
            which 'minus' is same as 'singlet'.
            Defaults to "singlet".
        name (str, optional): Name of case. Defaults to "intracell".
    """

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
        super().__init__(name=name)
        if state not in ["singlet", "minus", "plus"]:
            raise ValueError(f"Initial state is invalid: '{state}'.")
        self.num_qubits = num_qubits
        self.state = state

    def _build(self) -> None:
        if self._is_built:
            return
        super()._build()

        num_qubits = self.num_qubits
        if num_qubits == 0:
            return

        for i in range(0, num_qubits, 2):
            if self.state in ["minus", "singlet"]:
                self.x(i)
            self.h(i)
            self.x(i + 1)
            self.cx(i, i + 1)


class Singlet(Intracell):
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

    def __init__(self, num_qubits: int, name: str = "intracell") -> None:
        """Initializing the case.

        Args:
            num_qubits (int): Number of qubits.
            name (str, optional): Name of case. Defaults to "intracell".

        Raises:
            ValueError: When given number of qubits is not even.
        """
        super().__init__(num_qubits, "singlet", name)
