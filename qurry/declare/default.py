"""
================================================================
Default Configuration for Qurry (:mod:`qurry.declare.default`)
================================================================

"""
from typing import Optional
import warnings

from ..exceptions import QurryUnrecongnizedArguments
from ..capsule.mori import DefaultConfig

transpileConfig = DefaultConfig(
    name="transpile_args",
    default={
        "basis_gates": None,
        "inst_map": None,
        "coupling_map": None,
        "backend_properties": None,
        "initial_layout": None,
        "layout_method": None,
        "routing_method": None,
        "translation_method": None,
        "scheduling_method": None,
        "instruction_durations": None,
        "dt": None,
        "approximation_degree": None,
        "timing_constraints": None,
        "seed_transpiler": None,
        "optimization_level": None,
        "callback": None,
        "output_name": None,
        "unitary_synthesis_method": "default",
        "unitary_synthesis_plugin_config": None,
        "target": None,
    },
)

managerRunConfig = DefaultConfig(
    name="manager_run_args",
    default={
        "max_experiments_per_job": None,
        "job_share_level": None,
        "job_tags": None,
        "qobj_id": None,
        "qobj_header": None,
        "memory": False,
        "max_credits": None,
        "seed_simulator": None,
        "qubit_lo_freq": None,
        "meas_lo_freq": None,
        "qubit_lo_range": None,
        "meas_lo_range": None,
        "schedule_los": None,
        "meas_map": None,
        "memory_slot_size": 100,
        "rep_time": None,
        "rep_delay": None,
        "parameter_binds": None,
        "parametric_pulses": None,
        "init_qubits": True,
    },
)

runConfig = DefaultConfig(
    name="run_args",
    default={
        "basis_gates": None,
        "coupling_map": None,  # circuit transpile options
        "backend_properties": None,
        "initial_layout": None,
        "seed_transpiler": None,
        "optimization_level": None,
        "pass_manager": None,
        "qobj_id": None,
        "qobj_header": None,
        "memory": None,
        "max_credits": None,
        "seed_simulator": None,
        "default_qubit_los": None,
        "default_meas_los": None,  # schedule run options
        "qubit_lo_range": None,
        "meas_lo_range": None,
        "schedule_los": None,
        "meas_level": None,
        "meas_return": None,
        "memory_slots": None,
        "memory_slot_size": None,
        "rep_time": None,
        "rep_delay": None,
        "parameter_binds": None,
        "schedule_circuit": False,
        "inst_map": None,
        "meas_map": None,
        "scheduling_method": None,
        "init_qubits": None,
    },
)


def contain_checker(
    config: dict[str, any],
    checker: DefaultConfig,
    restrict: bool = False,
    null_allowed: bool = True,
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

    if len(config) > 0:
        use_key = checker.include_keys(config)
        if len(use_key) == 0:
            text = (
                "The following configuration has no any available arguments,"
                + f"'{config}' for '{checker.__name__}'\n"
                + f"Available keys: {checker.default_names}"
            )
            if restrict:
                raise QurryUnrecongnizedArguments(text)
            warnings.warn(text, QurryUnrecongnizedArguments)

        useless_key = checker.useless_keys(config)
        text = (
            f"'{use_key}' will be applied. "
            + "The following configuration has no any affect: "
            + f"'{useless_key}' for '{checker.__name__}'"
        )
        if len(useless_key) > 0:
            if restrict:
                raise QurryUnrecongnizedArguments(text)
            warnings.warn(text, QurryUnrecongnizedArguments)

    elif not null_allowed:
        text = (
            "The following configuration is null,"
            + f"'{config}' for '{checker.__name__}'\n"
            + f"Available keys: {checker.default_names}"
        )
        if restrict:
            raise QurryUnrecongnizedArguments(text)
        warnings.warn(text, QurryUnrecongnizedArguments)
