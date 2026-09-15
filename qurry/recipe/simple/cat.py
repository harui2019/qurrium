"""GHZ state (:mod:`qurecipe.simple.cat`)

The entangled circuit :class:`~qurecipe.simple.cat.GHZ`
as known as :class:`~qurecipe.simple.cat.Cat`,
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

from qiskit import QuantumCircuit


def ghz(num_qubits: int, name: str = "ghz") -> QuantumCircuit:
    r"""Generate the GHZ state circuit.

    .. code-block:: text

        # Open boundary at 8 qubits:
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

    .. math::

        \frac{1}{\sqrt{2}}
            \left({|01\rangle} - {|10\rangle} \right)^{\otimes N/2}, N = 8

    Args:
        num_qubits (int): The number of qubits for constructing the example circuit.
        name (str, optional): Name of case. Defaults to "ghz".

    Returns:
        QuantumCircuit: The GHZ state circuit.
    """
    qc = QuantumCircuit(num_qubits, name=name)
    if num_qubits == 0:
        return qc

    qc.h(0)
    for i in range(1, num_qubits):
        qc.cx(i - 1, i)

    return qc
