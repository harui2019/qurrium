"""Post Processing - Classical Shadow - Rho Process - Unitary Set
(:mod:`qurry.process.classical_shadow.rho_process.unitary_set`)

The followings are unitary operators for our classical shadow implementation.
"""

from typing import TypedDict
from collections.abc import Sequence
from dataclasses import dataclass
import functools as ft
import numpy as np
import numpy.typing as npt

from qiskit import QuantumCircuit
from qiskit.circuit.gate import Gate
from qiskit.circuit.parameter import Parameter
from qiskit.circuit.library import (
    HGate,
    IGate,
    RGate,
    RXGate,
    RYGate,
    RZGate,
    SGate,
    SdgGate,
    SXGate,
    SXdgGate,
    TGate,
    TdgGate,
    UGate,
    XGate,
    YGate,
    ZGate,
)

from ...utils import BaseMethodEnum
from ...utils.bloch_vector import PAULI_X, PAULI_Y, PAULI_Z

PAULI = [PAULI_X, PAULI_Y, PAULI_Z]
"""The list of Pauli matrices in the order of X, Y, Z. """


def combine_gates(*gates: Gate) -> Gate:
    """Combine multiple single-qubit gates into a single gate.

    Args:
        *gates (Gate): Variable number of Gate objects to combine.

    Returns:
        Gate: The combined gate.
    """
    name = "-".join(gate.name for gate in gates)
    qc = QuantumCircuit(1, name=name)
    for gate in gates:
        qc.append(gate, [0])
    combined_gate = qc.to_gate(label=name)
    return combined_gate


def combine_gate_matrices(*gates: Gate) -> npt.NDArray[np.complex128]:
    """Combine the matrix representations of multiple gates.

    Args:
        *gates (Gate): Variable number of Gate objects to combine.

    Returns:
        npt.NDArray[np.complex128]: The combined matrix representation.
    """
    return ft.reduce(np.dot, [gate.to_matrix() for gate in reversed(gates)])


def get_basis_allow_gates() -> dict[str, Gate]:
    """Return a mapping of standard gate names to their corresponding gate objects.

    The allowed gates include commonly used single-qubit gates,
    which has defined in Qiskit with matrix representations.

    The allowed gates are:
    - HGate
    - IGate
    - RGate
    - RXGate
    - RYGate
    - RZGate
    - SGate
    - SdgGate
    - SXGate
    - SXdgGate
    - TGate
    - TdgGate
    - UGate
    - XGate
    - YGate
    - ZGate

    Returns:
        dict[str, Gate]: A dictionary mapping gate names to Gate objects.
    """

    lam = Parameter("λ")
    theta = Parameter("ϴ")
    phi = Parameter("φ")

    gates = [
        HGate(),
        IGate(),
        RGate(theta, phi),
        RXGate(theta),
        RYGate(theta),
        RZGate(phi),
        SGate(),
        SdgGate(),
        SXGate(),
        SXdgGate(),
        TGate(),
        TdgGate(),
        UGate(theta, phi, lam),
        XGate(),
        YGate(),
        ZGate(),
    ]
    return {gate.name: gate for gate in gates}


BASIS_ALLOW_GATES = get_basis_allow_gates()
r"""A dictionary mapping standard gate names to their corresponding Gate objects.

The allowed gates include commonly used single-qubit gates,
which has defined in Qiskit with matrix representations.

The allowed gates are:
- HGate
- IGate
- RGate
- RXGate
- RYGate
- RZGate
- SGate
- SdgGate
- SXGate
- SXdgGate
- TGate
- TdgGate
- UGate
- XGate
- YGate
- ZGate
"""


OUTER_PRODUCT: dict[str, npt.NDArray[np.int32]] = {
    "0": np.array(
        [
            [1, 0],
            [0, 0],
        ]
    ),
    "1": np.array(
        [
            [0, 0],
            [0, 1],
        ]
    ),
}
r"""The :class:`~numpy.typing.NDArray[~numpy.int32]` objects 
for the outer product of :math:`|0\rangle` and :math:`|1\rangle`.

The set of outer product will represent by following dictionary
with the matrix representation:

- `0`: :math:`|0\rangle\langle0|`
- `1`: :math:`|1\rangle\langle1|`

.. math::
    |0\rangle\langle0| = \begin{pmatrix} 1 & 0 \\ 0 & 0 \end{pmatrix} \\
    |1\rangle\langle1| = \begin{pmatrix} 0 & 0 \\ 0 & 1 \end{pmatrix}

Here is the output of when you run the code in jupyter notebook:

.. code-block:: console

    {
        0: array([
            [1, 0], 
            [0, 0]
        ]),
        1: array([
            [0, 0], 
            [0, 1]
        ]),
    }
"""

IDENTITY: npt.NDArray[np.int32] = np.array(
    [
        [1, 0],
        [0, 1],
    ],
)
r"""The :class:`~numpy.typing.NDArray[~numpy.int32]` objects for the identity matrix.

It's just :math:`\mathbb{I} = \begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix}`.

What a simple matrix!

Here is the output of when you run the code in jupyter notebook:

.. code-block:: console

    array([
        [1, 0],
        [0, 1]
    ])

"""


class ShadowRandomBasisData(TypedDict):
    """TypedDict for exporting and loading ShadowRandomBasis data."""

    name: str
    """The name of the ShadowRandomBasis."""
    gate_name_and_params: Sequence[list[tuple[str, list[float]]]]
    """The gate names and parameters for each basis."""


def _remapper(
    content: dict[tuple[int, str], npt.NDArray[np.complex128]],
) -> dict[int, npt.NDArray[np.complex128]]:
    """Remap the keys of a dictionary from (direction, b_k) to direction * 10 + ord(b_k) - 48.

    Args:
        content (dict[tuple[int, str], npt.NDArray[np.complex128]]):
            The original dictionary with keys as (direction, b_k).

    Returns:
        dict[int, npt.NDArray[np.complex128]]:
            The remapped dictionary with keys as direction * 10 + ord(b_k) - 48.
    """
    return {direction * 10 + ord(b_k) - 48: matrix for (direction, b_k), matrix in content.items()}


@dataclass(frozen=True, init=False)
class ShadowRandomBasis:
    """Class for handling random basis selection for classical shadows."""

    gates_tuple: tuple[tuple[Gate, ...], tuple[Gate, ...], tuple[Gate, ...]]
    """The original tuples of Gate objects for each basis. """
    gates: tuple[Gate, Gate, Gate]
    """The combined Gate objects for each basis. """
    matrices: tuple[
        npt.NDArray[np.complex128], npt.NDArray[np.complex128], npt.NDArray[np.complex128]
    ]
    """The combined matrix representations for each basis. """

    name: str
    """The name of the ShadowRandomBasis. """
    gate_name_and_params: tuple[
        list[tuple[str, list[float]]],
        list[tuple[str, list[float]]],
        list[tuple[str, list[float]]],
    ]
    """The gate names and parameters for each basis. """

    basis_projecters: dict[tuple[int, str], npt.NDArray[np.complex128]]
    r"""The basis projectors for each basis and bitstring. 
    
    The basis projectors are defined as:

    .. math::
        P_{mk}^{i} = U_{mi}^{\dagger} |b_k \rangle\langle b_k| U_{mi}
    """
    basis_precomputed_rho_m_k_i: dict[tuple[int, str], npt.NDArray[np.complex128]]
    r"""The precomputed :math:`\rho_{mk}^{i}` matrices for each basis and bitstring.

    The precomputed :math:`\rho_{mk}^{i}` matrices are defined as:

    .. math::
        P_{mk}^{i} = U_{mi}^{\dagger} |b_k \rangle\langle b_k| U_{mi} \\
        \rho_{mk}^{i} = 3 P_{mk}^{i} - \mathbb{I}  
    """
    pauli_projecters: dict[tuple[int, str], npt.NDArray[np.complex128]]
    r"""The Pauli projectors for each basis and bitstring.
    
    The Pauli projectors are defined as:

    .. math::
        P_{mk}^{i}' = \frac{1}{2}((1 - 2 b_k)\sigma_{i} + \mathbb{I})

    where :math:`\sigma_{i}` is the Pauli operator for the i-th qubit.
    """
    pauli_precomputed_rho_m_k_i: dict[tuple[int, str], npt.NDArray[np.complex128]]
    r"""The precomputed :math:`\rho_{mk}^{i}` matrices
    for each Pauli basis and bitstring (tuple key).

    The precomputed :math:`\rho_{mk}^{i}` matrices are defined as:

    .. math::
        P_{mk}^{i}' = \frac{1}{2}((1 - 2 b_k)\sigma_{i} + \mathbb{I}) \\
        \rho_{mk}^{i} = 3 P_{mk}^{i}' - \mathbb{I}
        
    Why :math:`P_{mk}^{i}'` can be equivalent to :math:`P_{mk}^{i}` like the following
    
    .. math::
        P_{mk}^{i} = U_{mi}^{\dagger} |b_k \rangle\langle b_k| U_{mi} \\
        P_{mk}^{i}' = \frac{1}{2}((1 - 2 b_k)\sigma_{i} + \mathbb{I}) \\
        U_{mi}^{\dagger} |b_k \rangle\langle b_k| U_{mi} = 
        \frac{1}{2}((1 - 2 b_k)\sigma_{i} + \mathbb{I})

    You can refer 
    `Unraveling the Mystery 
<https://pennylane.ai/demos/tutorial_diffable_shadows#unraveling-the-mystery>`_
    """

    basis_projecters_2: dict[int, npt.NDArray[np.complex128]]
    r"""The basis projectors for each basis and bitstring (int key).
    
    This is the same as :attr:`basis_projecters` but with a single integer key
    ``direction * 10 + ord(b_k) - 48`` instead of a tuple, for vectorized computation.
    """

    basis_precomputed_rho_m_k_i_2: dict[int, npt.NDArray[np.complex128]]
    r"""The precomputed :math:`\rho_{mk}^{i}` matrices for each Pauli basis and bitstring (int key).

    This is the same as :attr:`pauli_precomputed_rho_m_k_i` but with a single integer key
    ``direction * 10 + ord(b_k) - 48`` instead of a tuple, for vectorized computation.
    """

    pauli_projecters_2: dict[int, npt.NDArray[np.complex128]]
    r"""The Pauli basis projectors for each Pauli basis and bitstring (int key).

    This is the same as :attr:`pauli_projecters` but with a single integer key
    ``direction * 10 + ord(b_k) - 48`` instead of a tuple, for vectorized computation.
    """

    pauli_precomputed_rho_m_k_i_2: dict[int, npt.NDArray[np.complex128]]
    r"""The precomputed :math:`\rho_{mk}^{i}` matrices for each Pauli basis and bitstring (int key).
    
    This is the same as :attr:`pauli_precomputed_rho_m_k_i` but with a single integer key
    ``direction * 10 + ord(b_k) - 48`` instead of a tuple, for vectorized computation.
    """

    basis_precomputed_rho_m_k_i_array: npt.NDArray[np.complex128]
    r"""Shape ``(3, 2, 2, 2)`` array for NumPy fancy-index lookup.

    ``basis_precomputed_rho_m_k_i_array[direction, bit_int]`` returns the
    :math:`\rho_{mk}^{i}` ``(2, 2)`` matrix, enabling vectorized
    construction of ``single_matrices`` without a Python loop.
    """

    basis_projecters_array: npt.NDArray[np.complex128]
    r"""Shape ``(3, 2, 2, 2)`` array for NumPy fancy-index lookup.

    ``basis_projecters_array[direction, bit_int]`` returns the projector
    :math:`P_{mk}^{i}` ``(2, 2)`` matrix, mirroring
    :attr:`basis_precomputed_rho_m_k_i_array` for the projecter variant.
    """

    @staticmethod
    def validate_basis_gates(basis_gates: tuple[Gate, ...]) -> None:
        """Validate that all gates in the basis_gates tuple are allowed.

        Args:
            basis_gates (tuple[Gate, ...]): Tuple of Gate objects to validate.

        Raises:
            ValueError: If any gate in basis_gates is not in BASIS_ALLOW_GATES.
        """
        if not isinstance(basis_gates, tuple):
            raise ValueError(
                "Each basis_gates must be a tuple of Gate objects to keep immutability."
            )
        if len(basis_gates) < 1:
            raise ValueError("Each basis_gates tuple must contain at least one Gate object.")

        if any(not isinstance(gate, Gate) for gate in basis_gates):
            raise ValueError("All elements in basis_gates tuples must be Gate objects.")
        if any(not hasattr(gate, "__array__") for gate in basis_gates):
            raise ValueError("All Gate objects must have a matrix representation.")
        if any(isinstance(param, Parameter) for gate in basis_gates for param in gate.params):
            raise ValueError(
                "All Gate objects must have concrete parameter values, not Parameters."
            )

        for gate in basis_gates:
            if gate.name not in BASIS_ALLOW_GATES:
                raise ValueError(
                    f"Gate '{gate.name}' is not allowed. "
                    f"Allowed gates are: {list(BASIS_ALLOW_GATES.keys())}."
                )
            if not isinstance(gate, BASIS_ALLOW_GATES[gate.name].__class__):
                raise ValueError("All elements in basis_gates must be Gate objects.")

    def __init__(
        self,
        *,
        basis_0_gates: tuple[Gate, ...],
        basis_1_gates: tuple[Gate, ...],
        basis_2_gates: tuple[Gate, ...],
        name: str | None = None,
    ) -> None:
        """Initialize the ShadowRandomBasis with specified basis gates.

        Args:
            basis_0_gates (tuple[Gate, ...]):
                Tuple of Gate objects representing the 1st measurement basis.
            basis_1_gates (tuple[Gate, ...]):
                Tuple of Gate objects representing the 2nd measurement basis.
            basis_2_gates (tuple[Gate, ...]):
                Tuple of Gate objects representing the 3rd measurement basis.
            name (str | None, optional):
                The name of the ShadowRandomBasis. If None, a name will be generated
                based on the gates used. Defaults to None.
        """
        self.validate_basis_gates(basis_0_gates)
        self.validate_basis_gates(basis_1_gates)
        self.validate_basis_gates(basis_2_gates)

        def quick_setter(oattr, value):
            object.__setattr__(self, oattr, value)

        quick_setter("gates_tuple", (basis_0_gates, basis_1_gates, basis_2_gates))
        quick_setter(
            "gates",
            (
                combine_gates(*self.gates_tuple[0]),
                combine_gates(*self.gates_tuple[1]),
                combine_gates(*self.gates_tuple[2]),
            ),
        )
        quick_setter(
            "matrices",
            (
                combine_gate_matrices(*self.gates_tuple[0]),
                combine_gate_matrices(*self.gates_tuple[1]),
                combine_gate_matrices(*self.gates_tuple[2]),
            ),
        )
        quick_setter(
            "name", "_".join(self.gates[i].name for i in range(3)) if name is None else name
        )

        quick_setter(
            "gate_name_and_params",
            (
                [(gate.name, gate.params) for gate in self.gates_tuple[0]],
                [(gate.name, gate.params) for gate in self.gates_tuple[1]],
                [(gate.name, gate.params) for gate in self.gates_tuple[2]],
            ),
        )

        # tuple key of (direction, b_k) -> matrix

        _basis_proj = {
            (direction, b_k): (
                self.matrices[direction].conj().T @ OUTER_PRODUCT[b_k] @ self.matrices[direction]
            )
            for direction in [0, 1, 2]
            for b_k in ["0", "1"]
        }
        quick_setter("basis_projecters", _basis_proj)
        quick_setter("basis_projecters_2", _remapper(_basis_proj))

        _basis_rho_m_k_i = {k: (3 * v) - IDENTITY for k, v in _basis_proj.items()}
        quick_setter("basis_precomputed_rho_m_k_i", _basis_rho_m_k_i)
        quick_setter("basis_precomputed_rho_m_k_i_2", _remapper(_basis_rho_m_k_i))
        quick_setter(
            "basis_precomputed_rho_m_k_i_array",
            np.array(
                [[_basis_rho_m_k_i[(d, "0")], _basis_rho_m_k_i[(d, "1")]] for d in range(3)],
                dtype=np.complex128,
            ),
        )
        quick_setter(
            "basis_projecters_array",
            np.array(
                [[_basis_proj[(d, "0")], _basis_proj[(d, "1")]] for d in range(3)],
                dtype=np.complex128,
            ),
        )

        _pauli_proj = {
            (direction, b_k): ((1 / 2) * ((1 - 2 * int(b_k)) * PAULI[direction] + IDENTITY))
            for direction in [0, 1, 2]
            for b_k in ["0", "1"]
        }
        quick_setter("pauli_projecters", _pauli_proj)
        quick_setter("pauli_projecters_2", _remapper(_pauli_proj))

        _pauli_rho_m_k_i = {k: (3 * v) - IDENTITY for k, v in _pauli_proj.items()}
        quick_setter("pauli_precomputed_rho_m_k_i", _pauli_rho_m_k_i)
        quick_setter("pauli_precomputed_rho_m_k_i_2", _remapper(_pauli_rho_m_k_i))

    # I/O methods for exporting and ingesting ShadowRandomBasis data.
    def export(self) -> ShadowRandomBasisData:
        """Export the ShadowRandomBasis data as a dictionary.

        Returns:
            ShadowRandomBasisData: A dictionary containing the ShadowRandomBasis data.
        """

        gate_name_and_params_export = (
            [
                (gate_name, [float(v) for v in gate_params])
                for gate_name, gate_params in self.gate_name_and_params[0]
            ],
            [
                (gate_name, [float(v) for v in gate_params])
                for gate_name, gate_params in self.gate_name_and_params[1]
            ],
            [
                (gate_name, [float(v) for v in gate_params])
                for gate_name, gate_params in self.gate_name_and_params[2]
            ],
        )

        return {
            "name": self.name,
            "gate_name_and_params": gate_name_and_params_export,
        }

    @classmethod
    def ingest(cls, raw_dict: ShadowRandomBasisData) -> "ShadowRandomBasis":
        """Load the ShadowRandomBasis data from a dictionary.

        Args:
            raw_dict (ShadowRandomBasisData): A dictionary containing the ShadowRandomBasis data.
        Returns:
            ShadowRandomBasis: The loaded ShadowRandomBasis instance.
        """
        if "gate_name_and_params" not in raw_dict:
            raise ValueError("Data must contain 'gate_name_and_params' keys.")
        if len(raw_dict["gate_name_and_params"]) != 3:
            raise ValueError("gate_name_and_params must contain exactly three basis lists.")

        basis_gates = []
        for basis in raw_dict["gate_name_and_params"]:
            if not isinstance(basis, Sequence):
                raise ValueError("Each basis in gate_name_and_params must be a list.")
            if len(basis) < 1:
                raise ValueError("Each basis must contain at least one gate definition.")

            gates = []
            for gate_name, params in basis:
                gate_instance = BASIS_ALLOW_GATES.get(gate_name)
                if gate_instance is None:
                    raise ValueError(f"Gate '{gate_name}' is not recognized.")
                if len(params) != len(gate_instance.params):
                    raise ValueError(
                        f"Gate '{gate_name}' expects {len(gate_instance.params)} "
                        + f"parameters, but got {len(params)}."
                    )
                gates.append(gate_instance.__class__(*params, label=None))  # type: ignore[arg-type]
            basis_gates.append(tuple(gates))

        return cls(
            basis_0_gates=basis_gates[0],
            basis_1_gates=basis_gates[1],
            basis_2_gates=basis_gates[2],
            name=raw_dict.get("name", None),
        )

    def __repr__(self) -> str:
        return f"ShadowRandomBasis(name='{self.name}')"


BUILTIN_BASIS = {
    basis_obj.name: basis_obj
    for basis_obj in [
        ShadowRandomBasis(
            basis_0_gates=(RYGate(-np.pi / 2),),
            basis_1_gates=(RXGate(np.pi / 2),),
            basis_2_gates=(RZGate(0),),
            name="RY_RX_RZ",
        ),
        ShadowRandomBasis(
            basis_0_gates=(HGate(),),
            basis_1_gates=(SdgGate(), HGate()),
            basis_2_gates=(IGate(),),
            name="H_H-Sdg_I",
        ),
    ]
}
r"""Predefined :class:`ShadowRandomBasis` instances.

Here are the built-in basis sets:
- `RY_RX_RZ`: 
    Uses :math:`R_Y(-\frac{\pi}{2})`, :math:`R_X(\frac{\pi}{2})`, and :math:`R_Z(0)` gates.
- `H_H-Sdg_I`: 
    Uses :math:`H`, :math:`H` followed by :math:`S^\dagger`, and Identity gates.
"""


class ShadowBasisMethod(BaseMethodEnum):
    """Enum for available unitary sets for classical shadow."""

    RY_RX_RZ = BUILTIN_BASIS["RY_RX_RZ"].name
    r"""Uses :math:`R_Y(-\frac{\pi}{2})`, :math:`R_X(\frac{\pi}{2})`, and :math:`R_Z(0)` gates.

    The basis of unitary operators is defined as:

    .. math::
        U = \{R_Y(-\frac{\pi}{2}), R_X(\frac{\pi}{2}), R_Z(0)\}

    The matrix representations are:

    .. math::
        R_Y(-\frac{\pi}{2}) = \begin{pmatrix} \cos(-\frac{\pi}{4}) & -\sin(-\frac{\pi}{4}) \\
        \sin(-\frac{\pi}{4}) & \cos(-\frac{\pi}{4}) \end{pmatrix} \\
        R_X(\frac{\pi}{2}) = \begin{pmatrix} \cos(\frac{\pi}{4}) & -i\sin(\frac{\pi}{4}) \\
        -i\sin(\frac{\pi}{4}) & \cos(\frac{\pi}{4}) \end{pmatrix} \\
        R_Z(0) = \begin{pmatrix} e^{0} & 0 \\ 0 & e^{0} \end{pmatrix}

    The console output of the matrices are:

    .. code-block:: console

        (array([[ 0.70710678+0.j,  0.70710678+0.j],
                [-0.70710678+0.j,  0.70710678+0.j]]),
         array([[0.70710678+0.j        , 0.        -0.70710678j],
                [0.        -0.70710678j, 0.70710678+0.j        ]]),
         array([[1.-0.j, 0.+0.j],
                [0.+0.j, 1.+0.j]]))

    """

    H_H_SDG_I = BUILTIN_BASIS["H_H-Sdg_I"].name
    r"""Uses :math:`H`, :math:`H` followed by :math:`S^\dagger`, and Identity gates.

    The basis of unitary operators is defined as:

    .. math::
        U = \{H, HS^\dagger, I\}

    The matrix representations are:

    .. math::
        H = \frac{1}{\sqrt{2}} \begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix} \\
        HS^\dagger = \frac{1}{\sqrt{2}} \begin{pmatrix} 1 & -i \\ 1 & i \end{pmatrix} \\
        I = \begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix}

    The console output of the matrices are:

    .. code-block:: console

        (array([[ 0.70710678+0.j,  0.70710678+0.j],
                [ 0.70710678+0.j, -0.70710678+0.j]]),
         array([[0.70710678+0.j        , 0.        -0.70710678j],
                [0.70710678+0.j        , 0.        +0.70710678j]]),
         array([[1.+0.j, 0.+0.j],
                [0.+0.j, 1.+0.j]]))

    """

    @classmethod
    def get_default(cls):
        """Get the default basis method.

        Returns:
            ShadowBasisMethod: The default basis method.
        """
        return cls.H_H_SDG_I

    @classmethod
    def get_shadow_basis(
        cls, shadow_basis: "ShadowBasisMethod | ShadowRandomBasis | str | None"
    ) -> ShadowRandomBasis:
        """Get the ShadowRandomBasis instance for the given method.

        Args:
            shadow_basis ("ShadowBasisMethod | ShadowRandomBasis | str | None"):
                The shadow basis method or instance.

        Returns:
            ShadowRandomBasis: The corresponding ShadowRandomBasis instance.
        """

        if isinstance(shadow_basis, ShadowRandomBasis):
            return shadow_basis
        if shadow_basis is None:
            return BUILTIN_BASIS[cls.get_default().value]
        if isinstance(shadow_basis, str):
            shadow_basis = cls.from_string(shadow_basis)

        if shadow_basis not in cls:
            raise cls.value_error()
        return BUILTIN_BASIS[shadow_basis.value]


ShadowBasisType = ShadowBasisMethod | ShadowRandomBasis | str
"""Type for shadow basis.
It can be either a :class:`ShadowBasisMethod` enum member, a string representing the enum member,
or a custom :class:`ShadowRandomBasis` instance.
"""


DEFAULT_SHADOW_BASIS: ShadowBasisMethod | ShadowRandomBasis = ShadowBasisMethod.get_default()
"""The default shadow basis method."""
