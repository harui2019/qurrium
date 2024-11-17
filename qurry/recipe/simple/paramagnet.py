"""
================================================================
Paramagnet (:mod:`qurry.recipe.library.simple.paramagnet`)
================================================================

"""

from typing import Literal

from ..n_body import OneBody


class TrivialParamagnet(OneBody):
    """The product state circuit :cls:`TrivialParamagnet`.
    Introduce in https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.121.086808 .

    .. code-block:: text

        # At 8 qubits:
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

    Args:
        num_qubits (int): Number of qubits.
        name (str, optional): Name of case. Defaults to "trivial_paramagnet".

    """

    def __init__(
        self,
        num_qubits: int,
        name: str = "trivial_paramagnet",
    ) -> None:
        """Initializing the case.

        Args:
            num_qubits (int): Number of qubits.
            name (str, optional): Name of case. Defaults to "trivial_paramagnet".
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


class TopologicalParamagnet(OneBody):
    """The entangled circuit :cls:`Topological paramagnet`.
    Introduce in https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.121.086808 .

    .. code-block:: text

        # With ACTUAL CZGate, Open boundary at 8 qubits:
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

    .. code-block:: text

        # With ACTUAL CZGate, Open boundary at 5 qubits:
            ┌───┐
        q0: ┤ H ├─■────
            ├───┤ │
        q1: ┤ H ├─■──■─
            ├───┤    │
        q2: ┤ H ├─■──■─
            ├───┤ │
        q3: ┤ H ├─■──■─
            ├───┤    │
        q4: ┤ H ├────■─
            └───┘


    .. code-block:: text

        # With ACTUAL CZGate, Period boundary at 8 qubits:
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

    .. code-block:: text

        # With ACTUAL CZGate, Period boundary at 5 qubits:
            ┌───┐
        q0: ┤ H ├─■──■────
            ├───┤ │  │
        q1: ┤ H ├─■──┼──■─
            ├───┤    │  │
        q2: ┤ H ├─■──┼──■─
            ├───┤ │  │
        q3: ┤ H ├─■──┼──■─
            ├───┤    │  │
        q4: ┤ H ├────■──■─
            └───┘

    Args:
        num_qubits (int): Number of qubits.
        border_cond (str, optional): Boundary condition is `open` or `period`.
            Defaults to "period".
        name (str, optional): Name of case. Defaults to "cluster".

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
        name: str = "cluster",
    ) -> None:
        """Initializing the case.

        Args:
            num_qubits (int): Number of qubits.
            border_cond (str, optional): Boundary condition is `open` or `period`.
                Defaults to "period".
            name (str, optional): Name of case. Defaults to "cluster".

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
        iter_range = num_qubits - 1 if self.border_cond == "open" else num_qubits
        for i in range(0, iter_range, 2):
            self.cz(i, (i + 1) % num_qubits)
        for i in range(1, iter_range, 2):
            self.cz(i, (i + 1) % num_qubits)


class Cluster(TopologicalParamagnet):
    """:cls:`Cluster`, another name of The entangled circuit :cls:`Topological paramagnet`.
    Introduce in https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.121.086808 .

    .. code-block:: text

        # With ACTUAL `CZGate`, Open boundary at 8 qubits:
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


    .. code-block:: text

        # With ACTUAL `CZGate`, Period boundary at 8 qubits:
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

    Args:
        num_qubits (int): Number of qubits.
        border_cond (str, optional): Boundary condition is `open` or `period`.
            Defaults to "period".
        name (str, optional): Name of case. Defaults to "cluster".

    Raises:
        ValueError: When given number of qubits is not even.

    """
