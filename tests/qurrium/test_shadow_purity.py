"""Test the Qurrium Runtime :class:`ShadowUnveil` for purity.

It's from :class:`~qurry.qurry.qurries.classical_shadow.qurry.ShadowUnveil`.
"""

from typing import TypedDict
import logging
from itertools import combinations
import pytest
import numpy as np

from qiskit import QuantumCircuit

from qurry.qurries.classical_shadow import ShadowUnveil, SUMeasureArgs
from qurry.qurries.classical_shadow.analysis import SUAnalyzeArgs, SUAnalysis
from qurry.process.classical_shadow import (
    RhoMethod,
    TraceMethod,
    verify_purity_value_kind,
    PurityValueKind,
)
from qurry.process.utils import NUMERICAL_ERROR_TOLERANCE
from qurry.recipe import trivial_paramagnet, ghz, cluster

from .utilities.simulator import get_seeded_simulator, SIM_DEFAULT_SOURCE
from .utilities.other import (
    CaseEntries,
    check_analysis_result,
    AnalysisResultChecker,
    EXPORT_DIR,
    make_config_list_and_tagged_case,
    make_specific_analysis_args,
    multi_read_tests_exported_files,
    FloatType,
)
from .utilities.random_stuff import prepare_random_basis
from .utilities.circuits import preparing_circuits_lib, cx_dyn_comparing, dummy_two_body_measurement


logger = logging.getLogger(__name__)

SIMULATOR = get_seeded_simulator()

RANDOM_BASIS = prepare_random_basis()

THRESHOLD = 0.25


class CaseDataDictABC(TypedDict):
    """Case data dictionary for testing."""

    circuit: QuantumCircuit
    """The quantum circuit to be tested."""
    target_purity: float
    """The expected target system purity for the test case."""


class CaseDataDict(CaseDataDictABC, total=False):
    """Case data dictionary for testing."""

    selected_qubits: list[int] | None
    """The selected qubits for analysis."""
    measure_range: list[int] | None
    """The measurement range for the test case."""


circuits_lib = preparing_circuits_lib(
    {
        "4_trivial": trivial_paramagnet(4),
        "4_ghz": ghz(4),
        "4_topological-period": cluster(4),
        "6_trivial": trivial_paramagnet(6),
        "6_ghz": ghz(6),
        "6_topological-period": cluster(6),
        # Two-body with measurement cases
        "4_dummy-2-body-with-clbits": dummy_two_body_measurement(4),
        "6_dummy-2-body-with-clbits": dummy_two_body_measurement(6),
        # CXDynamic cases
        "4_cx-dyn": cx_dyn_comparing(4, name="4-cx-dyn"),
        "6_cx-dyn": cx_dyn_comparing(6, name="6-cx-dyn"),
    }
)

case_datas: list[CaseDataDict] = [
    {"circuit": circuits_lib["4_trivial"].copy(), "target_purity": 1.0},
    {"circuit": circuits_lib["4_ghz"].copy(), "target_purity": 0.5},
    {"circuit": circuits_lib["4_topological-period"].copy(), "target_purity": 0.25},
    {"circuit": circuits_lib["6_trivial"].copy(), "target_purity": 1.0},
    {"circuit": circuits_lib["6_ghz"].copy(), "target_purity": 0.5},
    {"circuit": circuits_lib["6_topological-period"].copy(), "target_purity": 0.25},
    {
        "circuit": circuits_lib["4_dummy-2-body-with-clbits"].copy(),
        "target_purity": 1.0,
        "measure_range": [2, 3],
    },
    {
        "circuit": circuits_lib["6_dummy-2-body-with-clbits"].copy(),
        "target_purity": 1.0,
        "measure_range": [4, 5],
    },
]
case_datas_extra: list[CaseDataDict] = [
    {
        "circuit": circuits_lib["4_cx-dyn"].copy(),
        "target_purity": 1.0,
        "measure_range": [0, 3],
        "selected_qubits": [0, 3],
    },
    {
        "circuit": circuits_lib["6_cx-dyn"].copy(),
        "target_purity": 1.0,
        "selected_qubits": [0, 5],
        "measure_range": [0, 5],
    },
    {
        "circuit": circuits_lib["4_cx-dyn"].copy(),
        "target_purity": 0.5,
        "measure_range": [0],
        "selected_qubits": [0],
    },
    {
        "circuit": circuits_lib["6_cx-dyn"].copy(),
        "target_purity": 0.5,
        "measure_range": [0],
        "selected_qubits": [0],
    },
]

if SIM_DEFAULT_SOURCE == "qiskit_aer":
    case_datas.extend(case_datas_extra)  # only add these cases when Qiskit Aer is used

DEFAULT_SELECTED_QUBITS = list(range(-2, 0))
DEFAULT_SHOTS = 4
DEFAULT_SNAPSHOTS = 400

methods_by_kind: dict[PurityValueKind, list[tuple[str, str]]] = {}

for rho_method_tmp in RhoMethod.get_all_methods():
    for trace_method_tmp in TraceMethod.get_all_methods():
        if trace_method_tmp == TraceMethod.SKIP_TRACE.value:
            continue
        methods_by_kind.setdefault(
            verify_purity_value_kind(rho_method_tmp, trace_method_tmp), []
        ).append((rho_method_tmp, trace_method_tmp))


def all_methods_comparison(
    comparison_target: list[tuple[str, FloatType]], tolerance: FloatType = NUMERICAL_ERROR_TOLERANCE
) -> list[tuple[str, FloatType, str, FloatType, FloatType, FloatType]]:
    """Compare all methods' results for purity calculation.

    Args:
        comparison_target (list[tuple[str, FloatType]]):
            The list of method names and their results.
        tolerance (FloatType):
            The numerical tolerance for comparison. Defaults to NUMERICAL_ERROR_TOLERANCE.

    Returns:
        The list of invalid result comparisons, each containing:
        `(name_1, result_1, name_2, result_2, difference, tolerance)`.
    """

    invalid_results = []
    for (name_1, result_1), (name_2, result_2) in combinations(comparison_target, 2):
        diff = np.abs(result_1 - result_2)
        if diff > tolerance:
            invalid_results.append((name_1, result_1, name_2, result_2, diff, tolerance))

    return invalid_results


CASES: list[CaseEntries[SUMeasureArgs, SUAnalyzeArgs]] = [
    CaseEntries(
        tags=(f"{case_data['circuit'].name}",),
        measure_entries={
            "wave": case_data["circuit"],
            "snapshots": DEFAULT_SNAPSHOTS,
            "shots": DEFAULT_SHOTS,
            "measure": case_data.get("measure_range", None),
            "backend": SIMULATOR,
            "random_basis": {
                i: RANDOM_BASIS[case_data["circuit"].num_qubits][i]
                for i in range(DEFAULT_SNAPSHOTS)
            },
            "exp_name": f"measure_{case_data['circuit'].name}",
        },
        analyze_entries={
            "selected_qubits": case_data.get("selected_qubits", DEFAULT_SELECTED_QUBITS)
        },
        expect_answer={"purity": ("purity", case_data["target_purity"])},
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
    checker_list: list[AnalysisResultChecker] = []
    invalid_results_of_each_kind: dict[
        str, list[tuple[str, FloatType, str, FloatType, FloatType, FloatType]]
    ] = {}

    for kind, all_methods in methods_by_kind.items():
        invalid_results_of_each_kind[kind] = []
        checker_list_tmp: list[AnalysisResultChecker] = []

        for rho_method, trace_method in all_methods:
            analyze_entries_with_methods = case_entries.analyze_entries.copy()
            analyze_entries_with_methods["rho_method"] = rho_method
            analyze_entries_with_methods["trace_method"] = trace_method
            analysis_tmp = exp_01.analyze(**analyze_entries_with_methods)

            checker_list_tmp += [
                check_analysis_result(
                    analysis_tmp.results[key],
                    result_name=f"{kind}.{rho_method}.{trace_method} - {key}",
                    target_field=target_field,
                    expect_answer=expect_answer_value,
                    name=case_entries.name,
                    threshold=THRESHOLD,
                )
                for key, (target_field, expect_answer_value) in case_entries.expect_answer.items()
            ]

        invalid_results_of_each_kind[kind] = all_methods_comparison(
            [(arc.result_name, arc.got_answer) for arc in checker_list_tmp]
        )
        checker_list += checker_list_tmp

    for kind, invalid_results in invalid_results_of_each_kind.items():
        if len(invalid_results) > 0:
            msg = (
                f"FAIL - {case_entries.name} - "
                + f"Invalid results found in all methods comparison of {kind}:"
            )
            logger.error(msg)
            for name_1, result_1, name_2, result_2, difference, threshold in invalid_results:
                logger.error(
                    f" - {name_1} ({result_1}) vs {name_2} ({result_2}): "
                    + f"difference = {difference}, threshold = {threshold}"
                )
            assert False, msg
        else:
            msg = f"PASS - {case_entries.name} - All methods produced consistent results of {kind}."
            logger.info(msg)
            assert True, msg

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
        summoner_name="shadow_purity",
        save_location=EXPORT_DIR,
        multiprocess_build=True,
        multiprocess_write=False,
    )

    test_report_of_each_kind: dict[tuple[str, ...], dict[tuple[str, ...], list[SUAnalysis]]] = {}
    for kind, all_methods in methods_by_kind.items():
        for rho_method, trace_method in all_methods:
            summoner_id, report_name = exp_method.multiAnalysis(
                summoner_id,
                analysis_name=f"{kind}.{rho_method}.{trace_method}.test_report",
                no_serialize=True,
                trace_method=trace_method,
                rho_method=rho_method,
                specific_analysis_args=make_specific_analysis_args(
                    exp_method, summoner_id, cases_with_tags
                ),
            )
            test_report_of_each_kind[(kind, rho_method, trace_method)] = exp_method.multimanagers[
                summoner_id
            ].all_reports(report_name)

    checker_list = []
    for (kind, rho_method, trace_method), test_report in test_report_of_each_kind.items():
        for tags, report_list in test_report.items():
            assert len(report_list) == 1, (
                f"The report list length is wrong for tags {tags}: {len(report_list)} != 1."
            )
            checker_list += [
                check_analysis_result(
                    report_list[0].results[key],
                    result_name=f"{kind}.{rho_method}.{trace_method} - {key}",
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
