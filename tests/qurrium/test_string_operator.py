"""Test the Qurrium Runtime :class:`StringOperator`.

It's from :class:`~qurry.qurry.qurries.string_operator.qurry.StringOperator`.
"""

from typing import TypedDict, Literal
import logging
import pytest

from qiskit import QuantumCircuit

from qurry.qurries.string_operator import StringOperator, SOMeasureArgs
from qurry.qurries.string_operator.analysis import SOAnalyzeArgs, SOAnalysis
from qurry.recipe import trivial_paramagnet, cluster

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

THRESHOLD = 0.1

ANSWERS: dict[Literal["i", "zy"], dict[str, float]] = {
    "i": {
        "5_trivial": 1.0,
        "6_trivial": 1.0,
        "7_trivial": 1.0,
        "8_trivial": 1.0,
        "9_trivial": 1.0,
        "6_topological": 0.0,
        "8_topological": 0.0,
    },
    "zy": {
        "7_trivial": 0.0,
        "8_trivial": 0.0,
        "9_trivial": 0.0,
        "8_topological": 1.0,
    },
}


class CaseDataDict(TypedDict):
    """Case data dictionary for testing."""

    circuit: QuantumCircuit
    """The quantum circuit to be tested."""
    expect_answer: float
    """The expected answer for the test case."""
    str_op: Literal["i", "zy"]
    """The string operator to be used in the measurement."""


circuits_lib = preparing_circuits_lib(
    {
        "5_trivial": trivial_paramagnet(5),
        "6_trivial": trivial_paramagnet(6),
        "7_trivial": trivial_paramagnet(7),
        "8_trivial": trivial_paramagnet(8),
        "9_trivial": trivial_paramagnet(9),
        "6_topological": cluster(6),
        "8_topological": cluster(8),
    }
)


case_datas: list[CaseDataDict] = [
    {"circuit": circuits_lib[name].copy(), "expect_answer": answer, "str_op": str_op}
    for str_op, answer_of_string_op in ANSWERS.items()
    for name, answer in answer_of_string_op.items()
]

CASES: list[CaseEntries[SOMeasureArgs, SOAnalyzeArgs]] = [
    CaseEntries(
        tags=(f"{case_data['circuit'].name}",),
        measure_entries={
            "wave": case_data["circuit"],
            "backend": SIMULATOR,
            "str_op": case_data["str_op"],
        },
        analyze_entries={},
        expect_answer={"default": ("order", case_data["expect_answer"])},
    )
    for case_data in case_datas
]


@pytest.mark.parametrize("case_entries", CASES)
def test_measure_and_analyze(
    case_entries: CaseEntries[SOMeasureArgs, SOAnalyzeArgs],
) -> None:
    """Test orphan experiments.

    Args:
        case_entries (CaseEntriesTuple[SOMeasureArgs, SOAnalyzeArgs]): The test case item.
    """

    exp_method = StringOperator()
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

    exp_method = StringOperator()

    config_list, cases_with_tags = make_config_list_and_tagged_case(CASES)

    summoner_id = exp_method.multiOutput(
        config_list,
        backend=SIMULATOR,
        summoner_name="string_operator",
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
    test_report: dict[tuple[str, ...], list[SOAnalysis]] = exp_method.multimanagers[
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
