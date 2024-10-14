"""
================================================================
GHZ state (:mod:`qurry.recipe.library.simple.cat`)
================================================================

"""

from ..n_body import OneBody


class GHZ(OneBody):
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

    def __init__(self, num_qubits: int, name: str = "cat") -> None:
        super().__init__(name=name)
        self.num_qubits = num_qubits

    def _build(self) -> None:
        if self._is_built:
            return
        super()._build()

        num_qubits = self.num_qubits
        if num_qubits == 0:
            return

        self.h(0)
        for i in range(1, num_qubits):
            self.cx(i - 1, i)


class Cat(GHZ):
    """Anothor name of `GHZ` state."""
