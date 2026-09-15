"""Counts Tools (:mod:`qurry.qurrium.utils.counts`)"""

from typing import TypeVar
import logging

from qiskit.result import Result
from qiskit.primitives import PrimitiveResult, PubResult
from qiskit.exceptions import QiskitError

from ..exceptions import CountsLost
from ...process.utils import counts_list_recount_pyrust

DEFAULT_LOGGER = logging.getLogger(__name__)

_PR = TypeVar("_PR", bound=PubResult)


def process_idx_list(num: int | None = None, result_idx_list: list[int] | None = None) -> list[int]:
    """Process the final index list of counts to be extracted.

    - No matter what, if `result_idx_list` is provided, \
return the unique indices in `result_idx_list`.
    - If both `num` and `result_idx_list` are None, return an empty list.
    - If `num` is given and `result_idx_list` is None, \
return a list of indices from 0 to `num - 1`.

    Args:
        num (int | None, optional):
            The number of counts wanted to be extracted. Defaults to None.
        result_idx_list (list[int] | None, optional):
            The index of counts wanted to be extracted. Defaults to None.

    Returns:
        list[int]: The final index list of counts to be extracted.
    """
    if result_idx_list is not None:
        if not isinstance(result_idx_list, list):
            raise TypeError("result_idx_list must be a list of integers.")
        if not all(isinstance(idx, int) for idx in result_idx_list):
            raise TypeError("All elements in result_idx_list must be integers.")
        return list(set(result_idx_list))

    if num is None:
        return []
    return list(range(num))


def get_counts_and_exceptions(
    result: Result | None,
    num: int | None = None,
    result_idx_list: list[int] | None = None,
    logger: logging.Logger = DEFAULT_LOGGER,
) -> tuple[list[dict[str, int]], dict[str, Exception]]:
    """Get counts and exceptions from traditional :class:`~qiskit.result.result.Result`.

    Args:
        result (Result | None):
            The result of job.
        num (int | None, optional):
            The number of counts wanted to be extracted. Defaults to None.
        result_idx_list (list[int] | None, optional):
            The index of counts wanted to be extracted. Defaults to None.
        logger (logging.Logger, optional):
            The logger to use. Defaults to DEFAULT_LOGGER.

    Returns:
        Counts and exceptions.
    """
    if not isinstance(result, Result) and result is not None:
        raise TypeError(f"The result should be a Result or None, but got {type(result)}.")

    idx_list = process_idx_list(num, result_idx_list)
    if result is None:
        logger.warning("| No Result is given.")
        return [{} for _ in idx_list], {"none": CountsLost("No Result is given.")}

    counts: list[dict[str, int]] = []
    exceptions: dict[str, Exception] = {}

    if len(idx_list) == 0:
        try:
            tmp_single_counts = result.get_counts()
            if isinstance(tmp_single_counts, list):
                counts.extend(tmp_single_counts)
            else:
                counts.append(tmp_single_counts)
        except QiskitError as err_1:
            exceptions[f"{result.job_id}"] = err_1
            logger.warning(
                "| Failed Job result, replace with null counts, Job ID: %s %s", result.job_id, err_1
            )
            counts.append({})
        return counts, exceptions

    for i in idx_list:
        try:
            tmp_single_counts = result.get_counts(i)
            if not isinstance(tmp_single_counts, dict):
                raise CountsLost(
                    f"The counts at index {i} is not a dict, got {type(tmp_single_counts)}."
                )
        except QiskitError as err_2:
            exceptions[f"{result.job_id}.{i}"] = err_2
            logger.warning(
                "| Failed Job result skip, Job ID/which counts: %s/%s, %s", result.job_id, i, err_2
            )
            tmp_single_counts = {}
        counts.append(tmp_single_counts)

    return counts, exceptions


def bitstring_mapping_getter(
    counts: list[dict[str, int]], registers_mapping: dict[int, int]
) -> tuple[dict[int, int], dict[int, int]]:
    """Get the bitstring mapping and the final mapping.

    When you have multiple classical registers clusters,
    the bitstring will be separated by space.
    So we need to shift the index of the `registers_mapping` to get the correct mapping,
    it usually happens when you measure a circuit with its own classical registers.

    For example, we consider a circuit with 4 qubits and
    its own classical registers cluster of 4 bits.
    We want to measure the last 2 qubits,
    then this will add a new classical register with 2 bits.
    Here is the example of the counts:

    .. code-block:: python

        {
            "00 0001": 75,
            "01 0001": 171,
            "11 0001": 584,
            "10 0001": 194
        }

    Qurrium will keep another mapping information on the classical register we added.

    .. code-block:: python

        {
            "registers_mapping": {
                2: 0,
                3: 1
            }
        }

    Everything looks good, right?

    The post-processing of Qurrium will read the bitstring from right to left,
    to handle the little-endian format of Qiskit.
    If we use the `registers_mapping` directly,
    it will map to the wrong cluster of classical registers,
    which is the first 2 bits of first cluster of 4 bits in this example,
    where the results is "01" in "0001".

    So we need to shift the index of the `registers_mapping` by the total of
    the length of the other clusters of classical registers and the space.
    In this example, the shift is `4 (the length of the first cluster) + 1 (the space) = 5`.
    So the final mapping should be

    .. code-block:: python

        {
            "registers_mapping": {
                2: 0,
                3: 1
            },  # qubit index to original classical index
            "bitstring_mapping": {
                0: 5,
                1: 6,
            },  # original classical index to shifted index, which the index on full bitstring
            "final_mapping": {
                2: 5,
                3: 6
            },  # qubit index to shifted index, which the index on full bitstring
        }

    The `bitstring_mapping` is the mapping of the original index to the shifted index.
    It is useful when you want to know the mapping of all classical registers.

    .. code-block:: python

        bitstring_all = "01 2345"  # length = 7
        num_classical_register = 7

        select_clregs_sort_rev = sorted([5, 6], reverse=True)
        bitstring = "".join(
            bitstring_all[num_classical_register - q_i - 1] for q_i in select_clregs_sort_rev
        )

        print(bitstring)  # output "01"

    Args:
        counts (list[dict[str, int]]):
            The counts of the experiment.
        registers_mapping (dict[int, int]):
            The mapping of the index of selected qubits to the index of the classical register.

    Returns:
        tuple[dict[int, int], dict[int, int]]: The bitstring mapping and the final mapping.
    """

    bitstring_sampling = next(iter(counts[0].keys()))
    bitstring_sampling_divided = bitstring_sampling.split(" ")

    if len(bitstring_sampling_divided) > 1:
        bitstring_shift = len(bitstring_sampling_divided) - 1
        for clbit_cluster in bitstring_sampling_divided[1:]:
            bitstring_shift += len(clbit_cluster)
        bitstring_mapping = {v: v + bitstring_shift for v in registers_mapping.values()}
        final_mapping = {k: bitstring_mapping[v] for k, v in registers_mapping.items()}
        return bitstring_mapping, final_mapping

    return {v: v for v in registers_mapping.values()}, registers_mapping


def extract_measured_counts(
    counts: list[dict[str, int]], registers_mapping: dict[int, int]
) -> tuple[list[dict[str, int]], dict[int, int], dict[int, int]]:
    """Extract the measured counts from the counts mixed with other classical registers,
    given the classical registers selected mapping, and other information.

    This function focuses on extracting the measured counts
    from `traditional` counts data structure,
    coming from Qiskit Result object :class:`~qiskit.result.result.Result`.
    which a bitstring mixed with multiple classical registers clusters like:

    .. code-block:: python

        {'010000 0100 0001': 1024}
        # The bitstring is '010000 0100 0001'.
        # The last four bits are the first classical register.
        # The middle four bits are the second classical register.
        # The first six bits are the last classical register for the randomized measurement.

    With the `registers_mapping` as follow:

    .. code-block:: python

        {
            0: 0, # The quantum register 0 is mapped to the classical register 0.
            1: 1, # The quantum register 1 is mapped to the classical register 1.
            5: 2, # The quantum register 5 is mapped to the classical register 2.
            7: 3, # The quantum register 7 is mapped to the classical register 3.
        }

    We can extract the measured counts.

    For :class:`~qiskit.primitives.containers.primitive_result.PrimitiveResult`,
    there is another function :func:`~qurry.qurrium.utils.counts.extract_measured_counts_primitive`
    handling it.

    Args:
        counts (list[dict[str, int]]):
            The counts of the experiment.
        registers_mapping (dict[int, int]):
            The mapping of the index of selected qubits to the index of the classical register.

    Returns:
        The measured counts, the bitstring mapping, and the final mapping.
    """

    bitstring_mapping, final_mapping = bitstring_mapping_getter(counts, registers_mapping)
    counts_of_last_clreg = counts_list_recount_pyrust(
        counts, len(next(iter(counts[0]))), list(final_mapping.values())
    )

    return counts_of_last_clreg, bitstring_mapping, final_mapping


def get_selected_qubits(
    selected_qubits: list[int] | None, registers_mapping: dict[int, int], actual_num_qubits: int
) -> list[int]:
    """Get the selected qubits from the registers mapping and actual number of qubits.

    Args:
        selected_qubits (list[int] | None):
            The selected qubits.
        registers_mapping (dict[int, int]):
            The mapping of the index of selected qubits to the index of the classical register.
        actual_num_qubits (int):
            The actual number of qubits.

    Returns:
        list[int]: The selected qubits.
    """
    actual_selected_qubits = (
        [qi % actual_num_qubits for qi in selected_qubits]
        if selected_qubits
        else list(registers_mapping.keys())
    )
    if len(set(actual_selected_qubits)) != len(actual_selected_qubits):
        raise ValueError(
            "selected_qubits should not have duplicated elements,"
            + f" but got {actual_selected_qubits}."
        )

    return actual_selected_qubits


def get_selected_qubits_and_clregs(
    selected_qubits: list[int] | None, registers_mapping: dict[int, int], actual_num_qubits: int
) -> tuple[list[int], list[int]]:
    """Get the selected qubits from the registers mapping and actual number of qubits.

    Args:
        selected_qubits (list[int] | None):
            The selected qubits.
        registers_mapping (dict[int, int]):
            The mapping of the index of selected qubits to the index of the classical register.
        actual_num_qubits (int):
            The actual number of qubits.

    Returns:
        tuple[list[int], list[int]]: The selected qubits and classical registers.
    """
    actual_selected_qubits = get_selected_qubits(
        selected_qubits, registers_mapping, actual_num_qubits
    )

    return actual_selected_qubits, [registers_mapping[qi] for qi in actual_selected_qubits]


def get_counts_and_exceptions_primitive(
    primitive_result: PrimitiveResult[_PR] | None,
    num: int | None = None,
    result_idx_list: list[int] | None = None,
    required_clregs: list[str] | None = None,
    logger: logging.Logger = DEFAULT_LOGGER,
) -> tuple[list[dict[str, dict[str, int]]], dict[str, Exception]]:
    """Get counts and exceptions from
    :class:`~qiskit.primitives.containers.primitive_result.PrimitiveResult`.

    Args:
        result (PrimitiveResult | None):
            The result of job.
        num (int | None, optional):
            The number of counts wanted to be extracted. Defaults to None.
        result_idx_list (list[int] | None, optional):
            The index of counts wanted to be extracted. Defaults to None.
        required_clregs (list[str] | None, optional):
            The required classical registers names.
            Confirm the classical registers exist in the result, otherwise raise Exception.
            If None, do not check. Defaults to None.
        logger (logging.Logger, optional):
            The logger to use. Defaults to DEFAULT_LOGGER.

    Returns:
        Counts of repecting classical registers and exceptions.
    """
    if not isinstance(primitive_result, PrimitiveResult) and primitive_result is not None:
        raise TypeError(
            f"The result should be a PrimitiveResult or None, but got {type(primitive_result)}."
        )

    idx_list = process_idx_list(num, result_idx_list)
    if primitive_result is None:
        logger.warning("| No Result is given.")
        return [{} for _ in idx_list], {"none": CountsLost("No Result is given.")}
    idx_list = list(range(len(primitive_result))) if len(idx_list) == 0 else idx_list

    primitive_counts: list[dict[str, dict[str, int]]] = []
    exceptions: dict[str, Exception] = {}

    for i in idx_list:
        tmp_all_single_counts = {
            cregs_name: data_bin.get_counts()
            for cregs_name, data_bin in primitive_result[i].data.items()
        }
        if required_clregs is not None:
            missing_clregs = set(required_clregs) - set(tmp_all_single_counts.keys())
            if missing_clregs:
                exceptions[f"{i}"] = CountsLost(
                    f"The required classical registers {missing_clregs} "
                    + f"are missing in the result at index {i}."
                )
                logger.warning(
                    "| Missing required classical registers, index: %s, missing: %s",
                    i,
                    missing_clregs,
                )
        primitive_counts.append(tmp_all_single_counts)

    return primitive_counts, exceptions


def extract_measured_counts_primitive(
    primitive_counts: list[dict[str, dict[str, int]]],
    required_clreg: str,
    registers_mapping: dict[int, int],
) -> tuple[list[dict[str, int]], dict[int, int], dict[int, int]]:
    """Extract the measured counts from the primitive counts mixed with other classical registers,

    Args:
        counts (list[dict[str, int]]):
            The counts of the experiment.
        required_clreg (str):
            The required classical register name.
        registers_mapping (dict[int, int]):
            The mapping of the index of selected qubits to the index of the classical register.

    Returns:
        The measured counts, the bitstring mapping, and the final mapping.
    """
    required_clregs_counts = [pc[required_clreg] for pc in primitive_counts]

    bitstring_mapping, final_mapping = bitstring_mapping_getter(
        required_clregs_counts, registers_mapping
    )
    counts_of_last_clreg = counts_list_recount_pyrust(
        required_clregs_counts,
        len(next(iter(required_clregs_counts[0]))),
        list(final_mapping.values()),
    )

    return counts_of_last_clreg, bitstring_mapping, final_mapping
