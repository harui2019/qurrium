"""Test the Qurrium Runtime :class:`EntropyMeasureRandomized`.

It's from :class:`~qurry.qurry.qurries.entropy_randomized.qurry.EntropyMeasureRandomized`.
"""

from typing import TypedDict
import logging
import pytest

from qiskit import QuantumCircuit

from qurry.qurries.entropy_randomized import EntropyMeasureRandomized, EMRMeasureArgs
from qurry.qurries.entropy_randomized.analysis import EMRAnalyzeArgs, EMRAnalysis
from qurry.recipe import trivial_paramagnet, cluster, ghz

from .utilities.simulator import get_seeded_simulator, SIM_DEFAULT_SOURCE
from .utilities.other import (
    CaseEntries,
    check_analysis_result,
    EXPORT_DIR,
    make_config_list_and_tagged_case,
    make_specific_analysis_args,
    multi_read_tests_exported_files,
)
from .utilities.random_stuff import prepare_random_unitary_seeds
from .utilities.circuits import cx_dyn_comparing, dummy_two_body_measurement


logger = logging.getLogger(__name__)

SIMULATOR = get_seeded_simulator()

RANDOM_UNITARY_SEEDS = prepare_random_unitary_seeds()

THRESHOLD = 0.25


class CaseDataDictABC(TypedDict):
    """Case data dictionary for testing."""

    circuit: QuantumCircuit
    """The quantum circuit to be tested."""


class CaseDataDict(CaseDataDictABC, total=False):
    """Case data dictionary for testing."""

    target_purity: float
    """The expected target system purity for the test case."""
    allsys_purity: float | None
    """The expected all system purity for the test case."""
    mitigated_purity: float | None
    """The expected mitigated purity for the test case."""
    measure_range: list[int] | None
    """The measurement range for the test case."""
    selected_qubits: list[int] | None
    """The selected qubits for analysis."""


case_datas: list[CaseDataDict] = [
    {"circuit": trivial_paramagnet(4, name="4-trivial"), "target_purity": 1.0},
    {"circuit": ghz(4, name="4-GHZ"), "target_purity": 0.5},
    {"circuit": cluster(4, name="4-topological-period"), "target_purity": 0.25},
    {"circuit": trivial_paramagnet(6, name="6-trivial"), "target_purity": 1.0},
    {"circuit": ghz(6, name="6-GHZ"), "target_purity": 0.5},
    {"circuit": cluster(6, name="6-topological-period"), "target_purity": 0.25},
    {
        "circuit": dummy_two_body_measurement(4, name="4-dummy-2-body-with-clbits"),
        "target_purity": 1.0,
        "measure_range": [2, 3],
    },
    {
        "circuit": dummy_two_body_measurement(6, name="6-dummy-2-body-with-clbits"),
        "target_purity": 1.0,
        "measure_range": [4, 5],
    },
]
case_datas_extra: list[CaseDataDict] = [
    {
        "circuit": cx_dyn_comparing(4, name="4-cx-dyn"),
        "target_purity": 1.0,
        "measure_range": [0, 3],
        "selected_qubits": [0, 3],
    },
    {
        "circuit": cx_dyn_comparing(6, name="6-cx-dyn"),
        "target_purity": 1.0,
        "measure_range": [0, 5],
        "selected_qubits": [0, 5],
    },
    {
        "circuit": cx_dyn_comparing(4, name="4-cx-dyn"),
        "target_purity": 0.5,
        "allsys_purity": 0.5,
        "mitigated_purity": 1.0,
        "measure_range": [0],
        "selected_qubits": [0],
    },
    {
        "circuit": cx_dyn_comparing(6, name="6-cx-dyn"),
        "target_purity": 0.5,
        "allsys_purity": 0.5,
        "mitigated_purity": 1.0,
        "measure_range": [0],
        "selected_qubits": [0],
    },
]

if SIM_DEFAULT_SOURCE == "qiskit_aer":
    case_datas.extend(case_datas_extra)  # only add these cases when Qiskit Aer is used

DEFAULT_SELECTED_QUBITS = list(range(-2, 0))
DEFAULT_SHOTS = 1024
DEFAULT_TIMES = 50


def make_case_entries(
    case_data: CaseDataDict, times: int = DEFAULT_TIMES, shots: int = DEFAULT_SHOTS
) -> CaseEntries[EMRMeasureArgs, EMRAnalyzeArgs]:
    """Make case entries from case data.

    Args:
        case_data (CaseDataDict): The case data.
        times (int): The number of random unitaries. Default is 50.
        shots (int): The number of shots. Default is 1024.

    Returns:
        CaseEntriesTuple[EMRMeasureArgs, EMRAnalyzeArgs]: The case entries.
    """

    num_qubits = case_data["circuit"].num_qubits
    random_unitary_seeds = {i: RANDOM_UNITARY_SEEDS[num_qubits][i] for i in range(times)}

    expect_answer = {"target_system": ("purity", case_data.get("target_purity", 1.0))}
    all_sys_purity = case_data.get("allsys_purity", 1.0)
    if all_sys_purity is not None:
        expect_answer["all_system"] = ("purity", all_sys_purity)
    mitigated_purity = case_data.get("mitigated_purity", case_data.get("target_purity", 1.0))
    if mitigated_purity is not None:
        expect_answer["mitigated"] = ("mitigated_purity", mitigated_purity)

    return CaseEntries(
        tags=(case_data["circuit"].name,),
        measure_entries={
            "wave": case_data["circuit"],
            "backend": SIMULATOR,
            "times": times,
            "random_unitary_seeds": random_unitary_seeds,
            "shots": shots,
            "measure": case_data.get("measure_range", None),
        },
        analyze_entries={
            "selected_qubits": case_data.get("selected_qubits", DEFAULT_SELECTED_QUBITS)
        },
        expect_answer=expect_answer,
    )


CASES = [make_case_entries(case_data) for case_data in case_datas]


@pytest.mark.parametrize("case_entries", CASES)
def test_measure_and_analyze(
    case_entries: CaseEntries[EMRMeasureArgs, EMRAnalyzeArgs],
) -> None:
    """Test orphan experiments.

    Args:
        case_entries (CaseEntriesTuple[EMRMeasureArgs, EMRAnalyzeArgs]): The test case item.
    """

    exp_method = EntropyMeasureRandomized()
    exp_01 = exp_method.measure(**case_entries.measure_entries_with_tags())
    analysis_01 = exp_01.analyze(**case_entries.analyze_entries)

    checker_list = [
        check_analysis_result(
            analysis_01.results[key],
            result_name=key,
            target_field=target_field,
            expect_answer=expect_answer_value,
            name=case_entries.name,
            threshold=THRESHOLD,
        )
        for key, (target_field, expect_answer_value) in case_entries.expect_answer.items()
    ]

    analysis_02 = exp_01.analyze(**{**case_entries.analyze_entries, "counts_used": range(5)})
    analysis_03 = exp_01.analyze(**{**case_entries.analyze_entries, "counts_used": range(5)})

    checker_list.append(
        check_analysis_result(
            analysis_02.results["all_system"],
            result_name="all_system_source",
            target_field="purity",
            expect_answer=analysis_03["all_system", "purity"],
            name=case_entries.name,
        )
    )

    for checker in checker_list:
        checker.make_logger(logger)

    assert analysis_02["all_system", "entropy"] != analysis_01["all_system", "entropy"], (
        "The all system entropy should be different for counts_used is not same: "
        + f"counts_num: '{analysis_02['all_system', 'counts_num']}' "
        + f"and '{analysis_01['all_system', 'counts_num']}'."
        + f"'{analysis_02['all_system', 'purity']}' != '{analysis_01['all_system', 'purity']}', "
        + f"from '{analysis_02['all_system', 'all_system_source']}' "
        + f"and '{analysis_01['all_system', 'all_system_source']}'."
    )

    assert analysis_02["all_system", "all_system_source"] == "independent", (
        "The source of all system is not independent: "
        + f"from '{analysis_02['all_system', 'all_system_source']}' "
    )

    for checker in checker_list:
        checker.assert_correct()


def test_multi_output_all() -> None:
    """Test the multi-output experiment for all cases."""

    exp_method = EntropyMeasureRandomized()

    config_list, cases_with_tags = make_config_list_and_tagged_case(CASES)

    summoner_id = exp_method.multiOutput(
        config_list,
        backend=SIMULATOR,
        summoner_name="entropy_randomized",
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
    test_report: dict[tuple[str, ...], list[EMRAnalysis]] = exp_method.multimanagers[
        summoner_id
    ].all_reports(report_name)

    checker_list = []
    for tags, report_list in test_report.items():
        assert len(report_list) == 1, (
            f"The report list length is wrong for tags {tags}: {len(report_list)} != 1."
        )
        checker_list += [
            check_analysis_result(
                report_list[0].results[key],
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
