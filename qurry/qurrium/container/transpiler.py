"""Transpiler container (:mod:`qurry.qurrium.container.transpiler`)"""

from typing import Any, TypedDict
from collections.abc import Callable

from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler import Layout, CouplingMap, PropertySet
from qiskit.transpiler.basepasses import BasePass
from qiskit.transpiler.passes.synthesis.high_level_synthesis import HLSConfig
from qiskit.transpiler.target import Target
from qiskit.transpiler.passmanager import PassManager

from ...capsule import CustomDict

PassManagerType = str | PassManager | tuple[str, PassManager] | None
"""The type hint for passmanager argument in 
:meth:`~qurry.qurrium.qurrium.QurriumPrototype.output`."""


class PassManagerContainer(CustomDict[str, PassManager]):
    """A customized dictionary for storing
    :class:`~qiskit.transpiler.passmanager.PassManager` objects."""


def passmanager_processor(
    passmanager: PassManagerType, passmanager_container: dict[str, PassManager]
) -> tuple[str, PassManager] | None:
    """Process the passmanager for Qurrium.

    Args:
        passmanager (PassManagerType): The passmanager.
        passmanager_container (dict[str, PassManager]): The container of passmanager.

    Raises:
        KeyError: If the passmanager not found in the container.
        ValueError: If the passmanager is invalid.

    Returns:
        tuple[str, PassManager] | None: The passmanager pair.
    """
    if isinstance(passmanager, str):
        if passmanager not in passmanager_container:
            raise KeyError(f"Passmanager '{passmanager}' not found in {passmanager_container}")
        passmanager_pair = passmanager, passmanager_container[passmanager]
    elif isinstance(passmanager, PassManager):
        passmanager_pair = f"pass_{len(passmanager_container)}", passmanager
        passmanager_container[passmanager_pair[0]] = passmanager_pair[1]
    elif isinstance(passmanager, tuple):
        if not isinstance(passmanager[1], PassManager) or not isinstance(passmanager[0], str):
            raise ValueError(f"Invalid passmanager: {passmanager}")
        passmanager_pair = passmanager
        passmanager_container[passmanager_pair[0]] = passmanager_pair[1]
    elif passmanager is None:
        passmanager_pair = None
    else:
        raise ValueError(f"Invalid passmanager: {passmanager}")
    return passmanager_pair


class TranspileArgs(TypedDict, total=False):
    """Transpile arguments for :func:`~qiskit.compiler.transpiler.transpile`

    - :mod:`~qiskit` 2.0.0

    .. code-block:: python

        _CircuitT = TypeVar("_CircuitT", bound=Union[QuantumCircuit, list[QuantumCircuit]])

        def transpile(  # pylint: disable=too-many-return-statements
            circuits: _CircuitT,
            backend: Optional[Backend] = None,
            basis_gates: Optional[list[str]] = None,
            coupling_map: Optional[Union[CouplingMap, list[list[int]]]] = None,
            initial_layout: Optional[Union[Layout, dict, list]] = None,
            layout_method: Optional[str] = None,
            routing_method: Optional[str] = None,
            translation_method: Optional[str] = None,
            scheduling_method: Optional[str] = None,
            dt: Optional[float] = None,
            approximation_degree: Optional[float] = 1.0,
            seed_transpiler: Optional[int] = None,
            optimization_level: Optional[int] = None,
            callback: Optional[Callable[[
                BasePass, DAGCircuit, float, PropertySet, int
            ], Any]] = None,
            output_name: Optional[Union[str, list[str]]] = None,
            unitary_synthesis_method: str = "default",
            unitary_synthesis_plugin_config: Optional[dict] = None,
            target: Optional[Target] = None,
            hls_config: Optional[HLSConfig] = None,
            init_method: Optional[str] = None,
            optimization_method: Optional[str] = None,
            ignore_backend_supplied_default_methods: bool = False,
            num_processes: Optional[int] = None,
            qubits_initially_zero: bool = True,
        ) -> _CircuitT:
        ...

    """

    basis_gates: list[str] | None
    coupling_map: CouplingMap | list[list[int]] | None
    initial_layout: Layout | dict | list | None
    layout_method: str | None
    routing_method: str | None
    translation_method: str | None
    scheduling_method: str | None
    dt: float | None
    approximation_degree: float | None
    seed_transpiler: int | None
    optimization_level: int | None
    callback: Callable[[BasePass, DAGCircuit, float, PropertySet, int], Any] | None
    output_name: str | list[str] | None
    unitary_synthesis_method: str
    unitary_synthesis_plugin_config: dict | None
    target: Target | None
    hls_config: HLSConfig | None
    init_method: str | None
    optimization_method: str | None
    ignore_backend_supplied_default_methods: bool
    qubits_initially_zero: bool
