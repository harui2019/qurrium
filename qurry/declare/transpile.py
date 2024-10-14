"""
================================================================
Extra arguments for :func:`transpile` 
from :module:`qiskit.compiler.transpiler` 
(:mod:`qurry.declare.transpile`)
================================================================

"""

from typing import Optional, Union, Callable, TypedDict, Any

from qiskit.dagcircuit import DAGCircuit
from qiskit.providers.models.backendproperties import BackendProperties
from qiskit.pulse import InstructionScheduleMap
from qiskit.transpiler import Layout, CouplingMap, PropertySet
from qiskit.transpiler.basepasses import BasePass
from qiskit.transpiler.instruction_durations import InstructionDurationsType
from qiskit.transpiler.passes.synthesis.high_level_synthesis import HLSConfig
from qiskit.transpiler.target import Target


class TranspileArgs(TypedDict, total=False):
    """Transpile arguments for :func:`transpile` from :module:`qiskit.compiler.transpiler`.

    ```python
    _CircuitT = TypeVar("_CircuitT", bound=Union[QuantumCircuit, List[QuantumCircuit]])

    def transpile(
        circuits: _CircuitT,
        backend: Optional[Backend] = None,
        basis_gates: Optional[List[str]] = None,
        inst_map: Optional[List[InstructionScheduleMap]] = None,
        coupling_map: Optional[Union[CouplingMap, List[List[int]]]] = None,
        backend_properties: Optional[BackendProperties] = None,
        initial_layout: Optional[Union[Layout, Dict, List]] = None,
        layout_method: Optional[str] = None,
        routing_method: Optional[str] = None,
        translation_method: Optional[str] = None,
        scheduling_method: Optional[str] = None,
        instruction_durations: Optional[InstructionDurationsType] = None,
        dt: Optional[float] = None,
        approximation_degree: Optional[float] = 1.0,
        timing_constraints: Optional[Dict[str, int]] = None,
        seed_transpiler: Optional[int] = None,
        optimization_level: Optional[int] = None,
        callback: Optional[Callable[[BasePass, DAGCircuit, float, PropertySet, int], Any]] = None,
        output_name: Optional[Union[str, List[str]]] = None,
        unitary_synthesis_method: str = "default",
        unitary_synthesis_plugin_config: Optional[dict] = None,
        target: Optional[Target] = None,
        hls_config: Optional[HLSConfig] = None,
        init_method: Optional[str] = None,
        optimization_method: Optional[str] = None,
        ignore_backend_supplied_default_methods: bool = False,
        num_processes: Optional[int] = None,
    ) -> _CircuitT:
    ...
    ```

    """

    basis_gates: Optional[list[str]]
    inst_map: Optional[list[InstructionScheduleMap]]
    coupling_map: Optional[Union[CouplingMap, list[list[int]]]]
    backend_properties: Optional[BackendProperties]
    initial_layout: Optional[Union[Layout, dict, list]]
    layout_method: Optional[str]
    routing_method: Optional[str]
    translation_method: Optional[str]
    scheduling_method: Optional[str]
    instruction_durations: Optional[InstructionDurationsType]
    dt: Optional[float]
    approximation_degree: Optional[float]
    timing_constraints: Optional[dict[str, int]]
    seed_transpiler: Optional[int]
    optimization_level: Optional[int]
    callback: Optional[Callable[[BasePass, DAGCircuit, float, PropertySet, int], Any]]
    output_name: Optional[Union[str, list[str]]]
    unitary_synthesis_method: str
    unitary_synthesis_plugin_config: Optional[dict]
    target: Optional[Target]
    hls_config: Optional[HLSConfig]
    init_method: Optional[str]
    optimization_method: Optional[str]
    ignore_backend_supplied_default_methods: bool
    num_processes: Optional[int]
