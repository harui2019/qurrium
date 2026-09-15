"""Paramagnet (:mod:`qurecipe.simple.paramagnet`)

The circuits :class:`~qurecipe.simple.paramagnet.TrivialParamagnet` and
:class:`~qurecipe.simple.paramagnet.TopologicalParamagnet`,
which has been mentioned in the following reference.

Reference:
    -   Measurement of the Entanglement Spectrum of a Symmetry-Protected Topological State
        Using the IBM Quantum Computer - Choo, Kenny and von Keyserlingk, Curt W. and
        Regnault, Nicolas and Neupert, Titus
        `doi:10.1103/PhysRevLett.121.086808 <https://doi.org/10.1103/PhysRevLett.121.086808>`_

    .. code-block:: bibtex

        @article{PhysRevLett.121.086808,
            title = {
                Measurement of the Entanglement Spectrum of a Symmetry-Protected Topological State
                Using the IBM Quantum Computer},
            author = {
                Choo, Kenny and von Keyserlingk, Curt W. and Regnault, Nicolas and Neupert, Titus},
            journal = {Phys. Rev. Lett.},
            volume = {121},
            issue = {8},
            pages = {086808},
            numpages = {5},
            year = {2018},
            month = {Aug},
            publisher = {American Physical Society},
            doi = {10.1103/PhysRevLett.121.086808},
            url = {https://link.aps.org/doi/10.1103/PhysRevLett.121.086808}
        }


"""

from typing import Literal

from qiskit import QuantumCircuit


def trivial_paramagnet(num_qubits: int, name: str = "trivial_paramagnet") -> QuantumCircuit:
    r"""The product state circuit.

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

    .. math:: {|+\rangle}^{\otimes N}, N = 8

    Args:
        num_qubits (int): Number of qubits.
        name (str, optional): Name of case. Defaults to "trivial_paramagnet".
    """

    qc = QuantumCircuit(num_qubits, name=name)
    if num_qubits == 0:
        return qc

    for i in range(num_qubits):
        qc.h(i)
    return qc


class TopologicalParamagnet(QuantumCircuit):
    """The entangled circuit :class:`~qurecipe.simple.paramagnet.TopologicalParamagnet`."""

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
        super().__init__(num_qubits, name=name)
        self.border_cond = border_cond


def topological_paramagnet(
    num_qubits: int, border_cond: Literal["open", "period"] = "period", name: str = "cluster"
) -> TopologicalParamagnet:
    r"""The entangled circuit.

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

    qc = TopologicalParamagnet(num_qubits=num_qubits, border_cond=border_cond, name=name)
    if num_qubits == 0:
        return qc

    for i in range(num_qubits):
        qc.h(i)
    iter_range = num_qubits - 1 if border_cond == "open" else num_qubits
    for i in range(0, iter_range, 2):
        qc.cz(i, (i + 1) % num_qubits)
    for i in range(1, iter_range, 2):
        qc.cz(i, (i + 1) % num_qubits)

    return qc


def cluster(
    num_qubits: int, border_cond: Literal["open", "period"] = "period", name: str = "cluster"
) -> TopologicalParamagnet:
    r"""The entangled circuit with open boundary condition.


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
    return topological_paramagnet(num_qubits=num_qubits, border_cond=border_cond, name=name)
