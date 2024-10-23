"""
================================================================
Construct (:mod:`qurry.qurrium.utils.construct`)
================================================================

"""

import warnings
from typing import Union, Optional

from qiskit import QuantumCircuit
from qiskit.result import Result
from qiskit.exceptions import QiskitError

from ...exceptions import QurryCountLost


def decomposer(
    qc: QuantumCircuit,
    reps: int = 2,
) -> QuantumCircuit:
    """Decompose the circuit with giving times.

    Args:
        qc (QuantumCircuit): The circuit wanted to be decomposed.
        reps (int, optional):  Decide the times of decomposing the circuit.
            Draw quantum circuit with composed circuit. Defaults to 2.

    Returns:
        QuantumCircuit: The decomposed circuit.
    """

    return qc.decompose(reps=reps)


def get_counts_and_exceptions(
    result: Optional[Result],
    num: Optional[int] = None,
    result_idx_list: Optional[list[int]] = None,
) -> tuple[list[dict[str, int]], dict[str, Exception]]:
    """Get counts and exceptions from result.

    Args:
        result (Optional[Result]): The result of job.
        num (Optional[int], optional): The number of counts wanted to be extracted.
            Defaults to None.
        result_idx_list (Optional[list[int]], optional): The index of counts wanted to be extracted.
            Defaults to None.

    Returns:
        tuple[list[dict[str, int]], dict[str, Exception]]:
            Counts and exceptions.
    """
    counts: list[dict[str, int]] = []
    exceptions: dict[str, Exception] = {}
    if num is None:
        idx_list = [] if result_idx_list is None else result_idx_list
    else:
        if result_idx_list is None:
            idx_list = list(range(num))
        else:
            warnings.warn(
                (
                    "The number of result is not equal to the length of "
                    + "'result_idx_list', use length of 'result_idx_list'."
                )
                if num != len(result_idx_list)
                else (
                    "The 'num' is not None, but 'result_idx_list' is not None, "
                    + "use 'result_idx_list'."
                )
            )
            idx_list = result_idx_list

    if result is None:
        exceptions["None"] = QurryCountLost("Result is None")
        print("| Failed Job result skip.")
        for _ in idx_list:
            counts.append({})
        return counts, exceptions

    if len(idx_list) == 0:
        try:
            get: Union[list[dict[str, int]], dict[str, int]] = result.get_counts()
            if isinstance(get, list):
                counts: list[dict[str, int]] = get
            else:
                counts.append(get)
        except QiskitError as err_1:
            exceptions[result.job_id] = err_1
            print("| Failed Job result skip, Job ID:", result.job_id, err_1)
        return counts, exceptions

    for i in idx_list:
        try:
            all_meas = result.get_counts(i)
            assert isinstance(all_meas, dict), "The counts is not a dict."
        except QiskitError as err_2:
            exceptions[f"{result.job_id}.{i}"] = err_2
            print(
                "| Failed Job result skip, Job ID/which counts:",
                result.job_id,
                i,
                err_2,
            )
            all_meas = {}
        counts.append(all_meas)

    return counts, exceptions
