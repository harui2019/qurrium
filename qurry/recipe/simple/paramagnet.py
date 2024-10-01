"""
================================================================
Paramagnet (:mod:`qurry.recipe.library.simple.paramagnet`)
================================================================

"""

from typing import Literal

from ..n_body import OneBody, TwoBody


class TrivialParamagnet(OneBody):
    """The product state circuit `trivial paramagnet`.
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

    def __init__(
        self,
        num_qubits: int,
        name: str = "trivialParamagnet",
    ) -> None:
        """Initializing the case.

        Args:
            num_qubits (int): Number of qubits.
            name (str, optional): Name of case. Defaults to "trivialParamagnet".

        """
        super().__init__(name=name)
        self.num_qubits = num_qubits

    def _build(self) -> None:
        if self._is_built:
            return
        super()._build()

        num_qubits = self.num_qubits
        if num_qubits == 0:
            return

        for i in range(num_qubits):
            self.h(i)


class TopologicalParamagnet(TwoBody):
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

    @property
    def border_cond(self) -> Literal["open", "period"]:
        """The border condition."""
        return self._border_cond

    @border_cond.setter
    def border_cond(self, value: Literal["open", "period"]) -> None:
        if hasattr(self, "_border_cond"):
            raise AttributeError("The border_cond can't be changed.")
        if value not in ["open", "period"]:
            raise ValueError("The border_cond must be 'open' or 'period'.")
        self._border_cond: Literal["open", "period"] = value

    def __init__(
        self,
        num_qubits: int,
        border_cond: Literal["open", "period"] = "period",
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
        super().__init__(name=name)
        self.border_cond = border_cond
        self.num_qubits = num_qubits

    def _build(self) -> None:
        if self._is_built:
            return
        super()._build()

        num_qubits = self.num_qubits
        if num_qubits == 0:
            return

        for i in range(num_qubits):
            self.h(i)
        for i in range(0, num_qubits, 2):
            self.cz(i, (i + 1) % num_qubits)
        for i in range(1, (num_qubits - 1 if self.border_cond == "open" else num_qubits), 2):
            self.cz(i, (i + 1) % num_qubits)


class Cluster(TopologicalParamagnet):
    """Another name of The entangled circuit `Topological paramagnet`."""
