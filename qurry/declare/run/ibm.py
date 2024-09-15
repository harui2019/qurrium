"""
================================================================
Extra arguments for :meth:`backend.run` 
from :mod:`qiskit.providers.backend`
For each IBM Quantum provider.
(:mod:`qurry.declare.run.ibm`)
================================================================

"""

from typing import Optional, Union, Any, NotRequired

from qiskit.circuit import QuantumCircuit, Parameter
from qiskit.pulse import LoConfig
from qiskit.pulse.channels import PulseChannel
from qiskit.qobj.utils import MeasLevel, MeasReturnType

from .base_run import BaseRunArgs


class IBMRuntimeBackendRunArgs(BaseRunArgs):
    """Arguments for :meth:`backend.run` from :module:`qiskit.providers.backend`.
    For :cls:`IBMBackend` from :mod:`qiskit_ibm_runtime.ibm_backend`:

    ```python

    def run(
        self,
        circuits: Union[QuantumCircuit, str, List[Union[QuantumCircuit, str]]],
        dynamic: bool = None,
        job_tags: Optional[List[str]] = None,
        init_circuit: Optional[QuantumCircuit] = None,
        init_num_resets: Optional[int] = None,
        header: Optional[Dict] = None,
        shots: Optional[Union[int, float]] = None,
        memory: Optional[bool] = None,
        meas_level: Optional[Union[int, MeasLevel]] = None,
        meas_return: Optional[Union[str, MeasReturnType]] = None,
        rep_delay: Optional[float] = None,
        init_qubits: Optional[bool] = None,
        use_measure_esp: Optional[bool] = None,
        noise_model: Optional[Any] = None,
        seed_simulator: Optional[int] = None,
        **run_config: Dict,
    ) -> RuntimeJob:
    ...

    ```
    """

    dynamic: NotRequired[Optional[bool]]
    job_tags: NotRequired[Optional[list[str]]]
    init_circuit: NotRequired[Optional[QuantumCircuit]]
    init_num_resets: NotRequired[Optional[int]]
    header: NotRequired[Optional[dict]]
    shots: NotRequired[Optional[Union[int, float]]]
    memory: NotRequired[Optional[bool]]
    meas_level: NotRequired[Optional[Union[int, MeasLevel]]]
    meas_return: NotRequired[Optional[Union[str, MeasReturnType]]]
    rep_delay: NotRequired[Optional[float]]
    init_qubits: NotRequired[Optional[bool]]
    use_measure_esp: NotRequired[Optional[bool]]
    noise_model: NotRequired[Optional[Any]]
    seed_simulator: NotRequired[Optional[int]]
    run_config: NotRequired[dict]


class IBMProviderBackendRunArgs(BaseRunArgs):
    """Arguments for :meth:`backend.run` from :module:`qiskit.providers.backend`.
    For :cls:`IBMBackend` from :mod:`qiskit_ibm_provider.ibm_backend`:

    ```python
        def run(
        self,
        circuits: Union[QuantumCircuit, str, List[Union[QuantumCircuit, str]]],
        dynamic: bool = None,
        job_tags: Optional[List[str]] = None,
        init_circuit: Optional[QuantumCircuit] = None,
        init_num_resets: Optional[int] = None,
        header: Optional[Dict] = None,
        shots: Optional[Union[int, float]] = None,
        memory: Optional[bool] = None,
        meas_level: Optional[Union[int, MeasLevel]] = None,
        meas_return: Optional[Union[str, MeasReturnType]] = None,
        rep_delay: Optional[float] = None,
        init_qubits: Optional[bool] = None,
        use_measure_esp: Optional[bool] = None,
        noise_model: Optional[Any] = None,
        seed_simulator: Optional[int] = None,
        **run_config: Dict,
    ) -> IBMJob:
    ...

    ```
    """

    dynamic: NotRequired[Optional[bool]]
    job_tags: NotRequired[Optional[list[str]]]
    init_circuit: NotRequired[Optional[QuantumCircuit]]
    init_num_resets: NotRequired[Optional[int]]
    header: NotRequired[Optional[dict]]
    shots: NotRequired[Optional[Union[int, float]]]
    memory: NotRequired[Optional[bool]]
    meas_level: NotRequired[Optional[Union[int, MeasLevel]]]
    meas_return: NotRequired[Optional[Union[str, MeasReturnType]]]
    rep_delay: NotRequired[Optional[float]]
    init_qubits: NotRequired[Optional[bool]]
    use_measure_esp: NotRequired[Optional[bool]]
    noise_model: NotRequired[Optional[Any]]
    seed_simulator: NotRequired[Optional[int]]
    run_config: NotRequired[dict]


class IBMQBackendRunArgs(BaseRunArgs):
    """Arguments for :meth:`backend.run` from :module:`qiskit.providers.backend`.
    For :cls:`IBMQBackend` from :mod:`qiskit.providers.ibmq`:

    ```python
    def run(
        self,
        circuits: Union[QasmQobj, PulseQobj, QuantumCircuit, Schedule,
                        List[Union[QuantumCircuit, Schedule]]],
        job_name: Optional[str] = None,
        job_share_level: Optional[str] = None,
        job_tags: Optional[List[str]] = None,
        experiment_id: Optional[str] = None,
        header: Optional[Dict] = None,
        shots: Optional[int] = None,
        memory: Optional[bool] = None,
        qubit_lo_freq: Optional[List[int]] = None,
        meas_lo_freq: Optional[List[int]] = None,
        schedule_los: Optional[Union[List[Union[Dict[PulseChannel, float], LoConfig]],
                                        Union[Dict[PulseChannel, float], LoConfig]]] = None,
        meas_level: Optional[Union[int, MeasLevel]] = None,
        meas_return: Optional[Union[str, MeasReturnType]] = None,
        memory_slots: Optional[int] = None,
        memory_slot_size: Optional[int] = None,
        rep_time: Optional[int] = None,
        rep_delay: Optional[float] = None,
        init_qubits: Optional[bool] = None,
        parameter_binds: Optional[List[Dict[Parameter, float]]] = None,
        use_measure_esp: Optional[bool] = None,
        live_data_enabled: Optional[bool] = None,
        **run_config: Dict
    ) -> IBMQJob:
    ...

    ```
    """

    job_name: NotRequired[Optional[str]]
    job_share_level: NotRequired[Optional[str]]
    job_tags: NotRequired[Optional[list[str]]]
    experiment_id: NotRequired[Optional[str]]
    header: NotRequired[Optional[dict]]
    shots: NotRequired[Optional[int]]
    memory: NotRequired[Optional[bool]]
    qubit_lo_freq: NotRequired[Optional[list[int]]]
    meas_lo_freq: NotRequired[Optional[list[int]]]
    schedule_los: NotRequired[
        Optional[
            Union[
                list[Union[dict[PulseChannel, float], LoConfig]],
                Union[dict[PulseChannel, float], LoConfig],
            ]
        ]
    ]
    meas_level: NotRequired[Optional[Union[int, MeasLevel]]]
    meas_return: NotRequired[Optional[Union[str, MeasReturnType]]]
    memory_slots: NotRequired[Optional[int]]
    memory_slot_size: NotRequired[Optional[int]]
    rep_time: NotRequired[Optional[int]]
    rep_delay: NotRequired[Optional[float]]
    init_qubits: NotRequired[Optional[bool]]
    parameter_binds: NotRequired[Optional[list[dict[Parameter, float]]]]
    use_measure_esp: NotRequired[Optional[bool]]
    live_data_enabled: NotRequired[Optional[bool]]
    run_config: NotRequired[dict]
