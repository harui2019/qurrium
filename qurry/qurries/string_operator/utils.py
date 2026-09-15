"""String Operator - Utilities (:mod:`qurry.qurries.string_operator.utils`)"""

from typing import Literal, TypedDict
import numpy as np

from qiskit import QuantumCircuit, ClassicalRegister

from ...qurrium import WCKeyable, naming_circuit

DEFAULT_CLASSICAL_REGISTER_NAME = "m0"
"""The default name for classical register used for measurement."""

StringOperatorUnits = tuple[Literal["rx", "ry", "rz"], float] | None
"""Available string operator units.

- tuple[Literal["rx", "ry", "rz"], float]: A tuple containing:

    - "rx": Rotation around the x-axis.
    - "ry": Rotation around the y-axis.
    - "rz": Rotation around the z-axis.
    - float: The angle of rotation in radians.

    and do the measurement on the qubit.

- None: No operation and measurement is performed on the qubit.
"""


class StringOperatorLib(TypedDict):
    r"""String Operator Library.

    Which is defined by following the equation:

    .. math::

        S^O(g) = \langle\psi|\hat{O_i}
            \left(\prod_{j = i+2}^{k-2} \hat{\sigma}_j^x \right) \hat{O_i}|\psi\rangle

    -   i: When :math:`\hat{O_i} = \hat{O'_k} = \mathbb{1}`,
        denoted as :math:`S^{\mathbb{1}}(g)`, i for identity operator.

    -   zy: When :math:`\hat{O_i} = \hat{\sigma}_i^z\hat{\sigma}_{i+1}^y` and
        :math:`\hat{O'_i} = \hat{\sigma}_{k-1}^y\hat{\sigma}_k^y`,
        denoted as :math:`S^{\sigma^{zy}}(g)` for ZY operator.
    """

    i: dict[int | Literal["filling"], StringOperatorUnits]
    r"""Identity string operator.

    .. math::

        \hat{O_i} = \hat{O'_k} = \mathbb{1}
    """
    zy: dict[int | Literal["filling"], StringOperatorUnits]
    r"""ZY string operator.

    .. math::
        \hat{O'_i} = \hat{\sigma}_{k-1}^y\hat{\sigma}_k^y,
        \hat{O'_i} = \hat{\sigma}_{k-1}^y\hat{\sigma}_k^y
    """


StringOperatorLibType = Literal["i", "zy"]
"""Available string operator types. 

- "i": Identity string operator.
- "zy": ZY string operator.
"""

StringOperatorDirection = Literal["x", "y"]
"""Available string operator directions.

- "x": String operator in the X direction.
- "y": String operator in the Y direction.
"""


STRING_OPERATOR: dict[StringOperatorDirection, StringOperatorLib] = {
    "x": {
        "i": {
            0: None,
            "filling": ("ry", -np.pi / 2),
            -1: None,
        },
        "zy": {
            0: ("rz", 0),
            1: ("rx", np.pi / 2),
            "filling": ("ry", -np.pi / 2),
            -2: ("rx", np.pi / 2),
            -1: ("rz", 0),
        },
    },
    "y": {
        "i": {
            0: None,
            "filling": ("rx", np.pi / 2),
            -1: None,
        },
        "zy": {
            0: ("rz", 0),
            1: ("ry", -np.pi / 2),
            "filling": ("rx", np.pi / 2),
            -2: ("ry", -np.pi / 2),
            -1: ("rz", 0),
        },
    },
}
r"""Available string operator library.

- "x": Available string operator library for the X direction.
- "y": Available string operator library for the Y direction.

.. math::

    S^O(g) = \langle\psi|\hat{O_i}
        \left(\prod_{j = i+2}^{k-2} \hat{\sigma}_j^x \right) \hat{O_i}|\psi\rangle

-   i: When :math:`\hat{O_i} = \hat{O'_k} = \mathbb{1}`,
    denoted as :math:`S^{\mathbb{1}}(g)`, i for identity operator.

-   zy: When :math:`\hat{O_i} = \hat{\sigma}_i^z\hat{\sigma}_{i+1}^y` and
    :math:`\hat{O'_i} = \hat{\sigma}_{k-1}^y\hat{\sigma}_k^y`,
    denoted as :math:`S^{\sigma^{zy}}(g)` for ZY operator.
"""


def circuit_method(
    target_circuit: QuantumCircuit,
    target_key: WCKeyable,
    exp_name: str,
    i: int,
    k: int,
    str_op: StringOperatorLibType = "i",
    on_dir: StringOperatorDirection = "x",
) -> QuantumCircuit:
    """Build the circuit for the experiment.

    Args:
        target_circuit (QuantumCircuit): Target circuit.
        target_key (WCKeyable): Target key.
        exp_name (str): Experiment name.
        i (int): The index of beginning qubits in the quantum circuit.
        k (int): The index of ending qubits in the quantum circuit.
        str_op (StringOperatorLibType): The string operator.
        on_dir (StringOperatorDirection): The direction of the string operator, either "x" or "y".

    Returns:
        QuantumCircuit: The circuit for the experiment.
    """
    if i >= k:
        raise ValueError(f"i: {i} is not less than k: {k}.")
    if on_dir not in STRING_OPERATOR:
        raise ValueError("The `on_dir` must be either 'x' or 'y'.")
    if str_op not in STRING_OPERATOR[on_dir]:
        raise ValueError(f"The `str_op` must be one of {list(STRING_OPERATOR[on_dir])}.")
    if k - i + 1 < len(STRING_OPERATOR[on_dir][str_op]):
        raise ValueError(
            f"The `k - i` must be greater than or equal to {len(STRING_OPERATOR[on_dir][str_op])}. "
            f"But got k: {k} - i: {i} = {k - i}."
        )

    qc_exp1 = target_circuit.copy(
        naming_circuit(target_circuit, target_key, f"{exp_name}_{i}_{k}_{str_op}_{on_dir}")
    )
    c_meas1 = ClassicalRegister(k - i + 1, DEFAULT_CLASSICAL_REGISTER_NAME)
    qc_exp1.add_register(c_meas1)

    qc_exp1.barrier()

    string_op_lib = STRING_OPERATOR[on_dir][str_op]
    index_map = {op + ((k + 1) if op < 0 else i): op for op in string_op_lib if isinstance(op, int)}
    operations = {
        idx: string_op_lib[index_map.get(idx, "filling")]  # type: ignore
        for idx in range(i, k + 1)
    }

    for ci, (qi, move) in enumerate(operations.items()):
        if move is None:
            continue

        if move[0] == "rx":
            qc_exp1.rx(move[1], qi)
        elif move[0] == "ry":
            qc_exp1.ry(move[1], qi)
        qc_exp1.measure(qc_exp1.qubits[qi], c_meas1[ci])

    return qc_exp1
