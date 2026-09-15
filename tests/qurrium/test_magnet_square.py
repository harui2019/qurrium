"""Test the Qurrium Runtime :class:`MagnetSquare`.

It's from :class:`~qurry.qurry.qurries.magnet_square.qurry.MagnetSquare`.
"""

from typing import TypedDict
import logging
import pytest

from qiskit import QuantumCircuit

from qurry.qurries.magnet_square import MagnetSquare, MSMeasureArgs
from qurry.qurries.magnet_square.analysis import MSAnalyzeArgs, MSAnalysis
from qurry.recipe import trivial_paramagnet, ghz

from .utilities.simulator import get_seeded_simulator
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

THRESHOLD = 0.05

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

CASES: list[CaseEntries[MSMeasureArgs, MSAnalyzeArgs]] = [
    CaseEntries(
        tags=(f"{case_data['circuit'].name}",),
        measure_entries={
            "wave": case_data["circuit"],
            "backend": SIMULATOR,
            "unitary_operator": "z",
        },
        analyze_entries={},
        expect_answer={"default": ("magnet_square", case_data["expect_answer"])},
    )
    for case_data in case_datas
]


@pytest.mark.parametrize("case_entries", CASES)
def test_measure_and_analyze(
    case_entries: CaseEntries[MSMeasureArgs, MSAnalyzeArgs],
) -> None:
    """Test orphan experiments.

    Args:
        case_entries (CaseEntriesTuple[MSMeasureArgs, MSAnalyzeArgs]): The test case item.
    """

    exp_method = MagnetSquare()
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
    for checker in checker_list:
        checker.make_logger(logger)
    for checker in checker_list:
        checker.assert_correct()


def test_multi_output_all() -> None:
    """Test the multi-output experiment for all cases."""

    exp_method = MagnetSquare()

    config_list, cases_with_tags = make_config_list_and_tagged_case(CASES)

    summoner_id = exp_method.multiOutput(
        config_list,
        backend=SIMULATOR,
        summoner_name="magnet_square",
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
    test_report: dict[tuple[str, ...], list[MSAnalysis]] = exp_method.multimanagers[
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
