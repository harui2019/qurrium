"""Test the Qurrium Runtime :class:`ShadowUnveil` for magnetization square.

It's from :class:`~qurry.qurry.qurries.classical_shadow.qurry.ShadowUnveil`.
"""

from typing import TypedDict, Literal
import logging
import pytest
import functools as ft
from itertools import permutations
import numpy as np
import numpy.typing as npt

from qiskit import QuantumCircuit
from qiskit.circuit.library import ZGate, IGate

from qurry.qurries.classical_shadow import ShadowUnveil, SUMeasureArgs
from qurry.qurries.classical_shadow.analysis import SUAnalyzeArgs, SUAnalysis
from qurry.qurries.magnet_square.analysis import MSDefaultResult
from qurry.recipe import trivial_paramagnet, ghz

from .utilities.simulator import get_seeded_simulator
from .utilities.random_stuff import prepare_random_basis
from .utilities.other import (
    CaseEntries,
    check_analysis_result,
    EXPORT_DIR,
    make_config_list_and_tagged_case,
    make_specific_analysis_args,
    multi_read_tests_exported_files,
)
from .utilities.circuits import preparing_circuits_lib

logger = logging.getLogger(__name__)

SIMULATOR = get_seeded_simulator()

RANDOM_BASIS = prepare_random_basis()

THRESHOLD = 0.09

ANSWERS = {
    "2_trivial": 1 / 2,
    "4_trivial": 1 / 4,
    "6_trivial": 1 / 6,
    "8_trivial": 1 / 8,
    "2_cat": 1,
    "4_cat": 1,
    "6_cat": 1,
    "8_cat": 1,
}


class CaseDataDict(TypedDict):
    """Case data dictionary for testing."""

    circuit: QuantumCircuit
    """The quantum circuit to be tested."""
    expect_answer: float
    """The expected answer for the test case."""


circuits_lib = preparing_circuits_lib(
    {
        "2_trivial": trivial_paramagnet(2),
        "4_trivial": trivial_paramagnet(4),
        "6_trivial": trivial_paramagnet(6),
        "8_trivial": trivial_paramagnet(8),
        "2_cat": ghz(2),
        "4_cat": ghz(4),
        "6_cat": ghz(6),
        "8_cat": ghz(8),
    }
)


case_datas: list[CaseDataDict] = [
    {"circuit": circuit.copy(), "expect_answer": ANSWERS[name]}
    for name, circuit in circuits_lib.items()
]


def z_dir_operator_preparing(num_qubits: int) -> list[npt.NDArray[np.complex128]]:
    """Prepare the operator for the circuit.

    Args:
        num_qubits (int): The number of qubits in the circuit.

    Returns:
        list[npt.NDArray[np.complex128]]:
            A list of numpy arrays representing the operator for each pair of qubits.
    """
    z_gate_matrix = ZGate().to_matrix()
    i_gate_matrix = IGate().to_matrix()

    return [
        ft.reduce(
            np.kron, (z_gate_matrix if i in tgt else i_gate_matrix for i in range(num_qubits))
        )
        for tgt in permutations(range(num_qubits), 2)
    ]


def unveil_magnetization_square(
    estimate_of_given_operators: list[np.complex128] | list[complex], num_qubits: int
) -> np.float64:
    """Processing Classical Shadows post-processing for MagnetSquare.

    Args:
        estimate_of_given_operators (list[np.complex128] | list[complex]):
            The estimates of the given operators.
        num_qubits (int): The number of qubits in the circuit.

    Returns:
        np.float64: The unveiled magnet square value.
    """
    return np.complex128(sum(estimate_of_given_operators) + num_qubits).real / (num_qubits**2)


def append_magnet_result(
    analysis_instance: SUAnalysis,
) -> SUAnalysis[Literal["magnet_square"], MSDefaultResult]:
    """Append the magnet square result to the results dictionary.

    Args:
        results (dict[str, float]): The existing results dictionary.
        magnet_square (float): The magnet square value to append.

    Returns:
        dict[str, float]: The updated results dictionary with the magnet square value.
    """

    esitimators = analysis_instance.results["estimation"].estimate_of_given_operators
    analysis_instance.results["magnet_square"] = MSDefaultResult(
        magnet_square=unveil_magnetization_square(
            esitimators,
            analysis_instance.middleware_entries.num_qubits,
        ),
        magnet_square_cells={i: np.float64(v.real) for i, v in enumerate(esitimators)},
        taking_time=(
            analysis_instance.results["estimation"].taking_time
            + analysis_instance.results["basic"].taking_time
        ),
    )

    return analysis_instance


DEFAULT_SHOTS = 10
DEFAULT_SNAPSHOTS = 500

CASES: list[CaseEntries[SUMeasureArgs, SUAnalyzeArgs]] = [
    CaseEntries(
        tags=(f"{case_data['circuit'].name}",),
        measure_entries={
            "wave": case_data["circuit"],
            "snapshots": DEFAULT_SNAPSHOTS,
            "shots": DEFAULT_SHOTS,
            "backend": SIMULATOR,
            "random_basis": {
                i: RANDOM_BASIS[case_data["circuit"].num_qubits][i]
                for i in range(DEFAULT_SNAPSHOTS)
            },
        },
        analyze_entries={
            "trace_method": "skip_trace",
            "selected_qubits": list(range(case_data["circuit"].num_qubits)),
            "given_operators": z_dir_operator_preparing(case_data["circuit"].num_qubits),
        },
        expect_answer={"magnet_square": ("magnet_square", case_data["expect_answer"])},
    )
    for case_data in case_datas
]


@pytest.mark.parametrize("case_entries", CASES)
def test_measure_and_analyze(
    case_entries: CaseEntries[SUMeasureArgs, SUAnalyzeArgs],
) -> None:
    """Test orphan experiments.

    Args:
        case_entries (CaseEntriesTuple[SUMeasureArgs, SUAnalyzeArgs]): The test case item.
    """

    exp_method = ShadowUnveil()
    exp_01 = exp_method.measure(**case_entries.measure_entries_with_tags())
    analysis_01 = exp_01.analyze(**case_entries.analyze_entries)

    processed_analysis = append_magnet_result(analysis_01)

    checker_list = [
        check_analysis_result(
            processed_analysis.results[key],
            result_name=key,
            target_field=target_field,
            expect_answer=expect_answer_value,
            name=case_entries.name,
            threshold=THRESHOLD,
        )
        for key, (target_field, expect_answer_value) in case_entries.expect_answer.items()
    ]
    for checker in checker_list:
        checker.make_logger(logger)
    for checker in checker_list:
        checker.assert_correct()


def test_multi_output_all() -> None:
    """Test the multi-output experiment for all cases."""

    exp_method = ShadowUnveil()

    config_list, cases_with_tags = make_config_list_and_tagged_case(CASES)

    summoner_id = exp_method.multiOutput(
        config_list,
        backend=SIMULATOR,
        summoner_name="shadow_magnet",
        save_location=EXPORT_DIR,
        multiprocess_build=True,
        multiprocess_write=False,
    )

    summoner_id, report_name = exp_method.multiAnalysis(
        summoner_id,
        analysis_name="test_report",
        no_serialize=True,
        specific_analysis_args=make_specific_analysis_args(
            exp_method, summoner_id, cases_with_tags
        ),
    )
    test_report: dict[tuple[str, ...], list[SUAnalysis]] = exp_method.multimanagers[
        summoner_id
    ].all_reports(report_name)

    checker_list = []
    for tags, report_list in test_report.items():
        assert len(report_list) == 1, (
            f"The report list length is wrong for tags {tags}: {len(report_list)} != 1."
        )

        processed_analysis = append_magnet_result(report_list[0])

        checker_list += [
            check_analysis_result(
                processed_analysis.results[key],
                result_name=key,
                target_field=target_field,
                expect_answer=expect_answer_value,
                name=cases_with_tags[tags].name,
                threshold=THRESHOLD,
            )
            for key, (target_field, expect_answer_value) in cases_with_tags[
                tags
            ].expect_answer.items()
        ]

    for checker in checker_list:
        checker.make_logger(logger, extra_msg="multi-output all")
    for checker in checker_list:
        checker.assert_correct()

    multi_read_tests_exported_files(exp_method, summoner_id, EXPORT_DIR)
