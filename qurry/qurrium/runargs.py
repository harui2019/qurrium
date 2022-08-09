from ..mori import defaultConfig
from ..util.watch import ResoureWatch

transpileConfig = defaultConfig(
    name='transpileArgs',
    default={
        'basis_gates': None,
        'inst_map': None,
        'coupling_map': None,
        'backend_properties': None,
        'initial_layout': None,
        'layout_method': None,
        'routing_method':  None,
        'translation_method': None,
        'scheduling_method': None,
        'instruction_durations': None,
        'dt': None,
        'approximation_degree': None,
        'timing_constraints': None,
        'seed_transpiler': None,
        'optimization_level': None,
        'callback': None,
        'output_name': None,
        'unitary_synthesis_method': "default",
        'unitary_synthesis_plugin_config': None,
        'target': None,
    }
)

managerRunConfig = defaultConfig(
    name='managerRunArgs',
    default={
        'max_experiments_per_job': None,
        'job_share_level': None,
        'job_tags': None,
        'qobj_id': None,
        'qobj_header':  None,
        'memory': False,
        'max_credits': None,
        'seed_simulator': None,
        'qubit_lo_freq': None,
        'meas_lo_freq': None,
        'qubit_lo_range': None,
        'meas_lo_range': None,
        'schedule_los': None,
        'meas_map': None,
        'memory_slot_size': 100,
        'rep_time': None,
        'rep_delay': None,
        'parameter_binds': None,
        'parametric_pulses': None,
        'init_qubits': True,
    }
)

runConfig = defaultConfig(
    name='runArgs',
    default={
        'basis_gates': None,
        'coupling_map': None,  # circuit transpile options
        'backend_properties': None,
        'initial_layout': None,
        'seed_transpiler': None,
        'optimization_level': None,
        'pass_manager': None,
        'qobj_id': None,
        'qobj_header': None,
        'memory': None,
        'max_credits': None,
        'seed_simulator': None,
        'default_qubit_los': None,
        'default_meas_los': None,  # schedule run options
        'qubit_lo_range': None,
        'meas_lo_range': None,
        'schedule_los': None,
        'meas_level': None,
        'meas_return': None,
        'memory_slots': None,
        'memory_slot_size': None,
        'rep_time': None,
        'rep_delay': None,
        'parameter_binds': None,
        'schedule_circuit': False,
        'inst_map': None,
        'meas_map': None,
        'scheduling_method': None,
        'init_qubits': None,
    }
)

ResoureWatchConfig = defaultConfig(
    name='ResoureWatchArgs',
    default=ResoureWatch.RESOURCE_LIMIT._asdict(),
)
