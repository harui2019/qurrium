from typing import Optional
import warnings

from ..exceptions import QurryInheritionNoEffect
from ..mori import defaultConfig
from ..tools.watch import ResoureWatch

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
    default=ResoureWatch.RESOURCE_LIMIT()._asdict(),
)


def containChecker(
    config: dict[str, any],
    checker: defaultConfig,
    restrict: bool = False,
) -> Optional[Exception]:
    """Check whether configuration is available.

    Args:
        config (dict[str, any]): Configuration.
        checker (defaultConfig): defaultConfig for it.
        restrict (bool, optional):
            Raise error when `True`, otherwise only shows as a warning. 
            Defaults to False.

    Raises:
        QurryInheritionNoEffect: _description_
        QurryInheritionNoEffect: _description_

    Returns:
        Optional[Exception]: _description_
    """
    if (len(config) > 0):
        if not checker.contain(config):
            text = (
                f"The following configuration has no any effected arguments," +
                f"'{config}' for '{checker.__name__}'\n" +
                f'Available keys: {checker.default_names}'
            )

            if restrict:
                raise QurryInheritionNoEffect(text)
            else:
                warnings.warn(text, QurryInheritionNoEffect)
        else:
            useKey = checker.has(config)
            uselessKey = checker.useless(config)
            text = (
                f"'{useKey}' will be applied. " +
                f"The following configuration has no any affect: " +
                f"'{uselessKey}' for '{checker.__name__}'"
            )
            if len(uselessKey) > 0:
                if restrict:
                    raise QurryInheritionNoEffect(text)
                else:
                    warnings.warn(text, QurryInheritionNoEffect)
    else:
        ...
