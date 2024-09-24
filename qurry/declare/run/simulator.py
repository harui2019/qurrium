"""
================================================================
Extra arguments for :meth:`backend.run` 
from :mod:`qiskit.providers.backend`
For each qiskit simulator.
(:mod:`qurry.declare.run.simulator`)
================================================================

"""

from typing import Optional, Union

from qiskit.circuit import Parameter, Qubit
from qiskit.pulse import LoConfig
from qiskit.pulse.channels import PulseChannel
from qiskit.qobj import QobjHeader
from qiskit.qobj.utils import MeasLevel, MeasReturnType

from .base_run import BaseRunArgs


class BasicSimulatorRunArgs(BaseRunArgs, total=False):
    """Arguments for :meth:`backend.run` from :module:`qiskit.providers.backend`.
    For :cls:`BasicSimulator` from :mod:`qiskit.providers.basic_provider`:

    ```python
    def _assemble(
        experiments: Union[
            QuantumCircuit,
            List[QuantumCircuit],
            Schedule,
            List[Schedule],
            ScheduleBlock,
            List[ScheduleBlock],
        ],
        backend: Optional[Backend] = None,
        qobj_id: Optional[str] = None,
        qobj_header: Optional[Union[QobjHeader, Dict]] = None,
        shots: Optional[int] = None,
        memory: Optional[bool] = False,
        seed_simulator: Optional[int] = None,
        qubit_lo_freq: Optional[List[float]] = None,
        meas_lo_freq: Optional[List[float]] = None,
        qubit_lo_range: Optional[List[float]] = None,
        meas_lo_range: Optional[List[float]] = None,
        schedule_los: Optional[
            Union[
                List[Union[Dict[PulseChannel, float], LoConfig]],
                Union[Dict[PulseChannel, float], LoConfig],
            ]
        ] = None,
        meas_level: Union[int, MeasLevel] = MeasLevel.CLASSIFIED,
        meas_return: Union[str, MeasReturnType] = MeasReturnType.AVERAGE,
        meas_map: Optional[List[List[Qubit]]] = None,
        memory_slot_size: int = 100,
        rep_time: Optional[int] = None,
        rep_delay: Optional[float] = None,
        parameter_binds: Optional[List[Dict[Parameter, float]]] = None,
        parametric_pulses: Optional[List[str]] = None,
        init_qubits: bool = True,
        **run_config: Dict,
    ) -> Union[QasmQobj, PulseQobj]:
    ...

    ```
    """

    qobj_id: Optional[str]
    qobj_header: Optional[Union[QobjHeader, dict]]
    shots: Optional[int]
    memory: Optional[bool]
    seed_simulator: Optional[int]
    qubit_lo_freq: Optional[list[float]]
    meas_lo_freq: Optional[list[float]]
    qubit_lo_range: Optional[list[float]]
    meas_lo_range: Optional[list[float]]
    schedule_los: Optional[
        Union[
            list[Union[dict[PulseChannel, float], LoConfig]],
            Union[dict[PulseChannel, float], LoConfig],
        ]
    ]

    meas_level: Union[int, MeasLevel]
    meas_return: Union[str, MeasReturnType]
    meas_map: Optional[list[list[Qubit]]]
    memory_slot_size: int
    rep_time: Optional[int]
    rep_delay: Optional[float]
    parameter_binds: Optional[list[dict[Parameter, float]]]
    parametric_pulses: Optional[list[str]]
    init_qubits: bool
    run_config: dict


class AerBackendRunArgs(BaseRunArgs, total=False):
    """Arguments for :meth:`backend.run` from :module:`qiskit.providers.backend`.
    For :cls:`AerBackend` from :mod:`qiskit_aer.backends.aerbackend`
    or :cls:`AerBackend` from :mod:`qiskit.providers.aer.backends.aerbackend`,
    the old import path.:

    ```python
    def run(self, circuits, parameter_binds=None, **run_options):
        if isinstance(circuits, (QuantumCircuit, Schedule, ScheduleBlock)):
        circuits = [circuits]

        return self._run_circuits(circuits, parameter_binds, **run_options)
    ```
    ->
    ```python
    def _run_circuits(self, circuits, parameter_binds, **run_options):
        # Submit job
        job_id = str(uuid.uuid4())
        aer_job = AerJob(
            self,
            job_id,
            self._execute_circuits_job, # This takes run_options
            parameter_binds=parameter_binds,
            circuits=circuits,
            run_options=run_options,
        )
        aer_job.submit()

        return aer_job

    ```
    ->
    ```python
    def set_option(self, key, value):
        if hasattr(self._configuration, key):
            self._set_configuration_option(key, value)
        elif hasattr(self._properties, key):
            self._set_properties_option(key, value)
        else:
            if not hasattr(self._options, key):
                raise AerError(f"Invalid option {key}")
            if value is not None:
                # Only add an option if its value is not None
                setattr(self._options, key, value)
            else:
                # If setting an existing option to None reset it to default
                # this is for backwards compatibility when setting it to None would
                # remove it from the options dict
                setattr(self._options, key, getattr(self._default_options(), key))
    ```

    So, `run_options` is a dictionary that can be set by `set_option` method?
    It actuanlly controls:
        - self._configuration
        - self._properties
        - self._options
    of the backend object.

    ???

    (Captured from qiskit-aer 0.15.0)
    """

    parameter_binds: Optional[list[dict[Parameter, float]]]
    run_options: dict


class BasicAerBackendRunArgs(BaseRunArgs, total=False):
    """Arguments for :meth:`backend.run` from :module:`qiskit.providers.backend`.
    For :cls:`QasmSimulatorPy` from :mod:`qiskit.providers.basicaer`:

    ```python

    def run(self, qobj, **backend_options):
        ...
        self._set_options(qobj_config=qobj_options, backend_options=backend_options)
        job_id = str(uuid.uuid4())
        job = BasicAerJob(self, job_id, self._run_job(job_id, qobj))
        return job
    ```
    ->
    ???

    I can't where the full content of `backend_options` is used in the source code.
    So, `backend_options: dict]`
    """

    backend_options: dict
