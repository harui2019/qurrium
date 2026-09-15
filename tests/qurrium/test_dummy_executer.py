"""Test the Qurrium Dummy Runtime :class:`SamplingExecuter` and :class:`WavesExecuter`.

They are from :class:`~qurry.qurry.qurries.dummy_executer.qurry.SamplingExecuter`
"""

import logging
import pytest

from qurry.qurries.samplingqurry import SamplingExecuter, SEMeasureArgs
from qurry.qurries.wavesqurry import WavesExecuter, WEMeasureArgs
from qurry.qurries.samplingqurry.analysis import DummyAnalysis, DummyAnalyzeArgs
from qurry.recipe import trivial_paramagnet, cluster, ghz

from .utilities.simulator import get_seeded_simulator
from .utilities.other import (
    CaseEntries,
    AnalysisResultChecker,
    check_analysis_result,
    EXPORT_DIR,
    make_config_list_and_tagged_case,
    make_specific_analysis_args,
    multi_read_tests_exported_files,
)
from .utilities.circuits import preparing_circuits_lib


logger = logging.getLogger(__name__)

SIMULATOR = get_seeded_simulator()


circuits_lib = preparing_circuits_lib(
    {
        "4_trivial": trivial_paramagnet(4),
        "4_topological": cluster(4),
        "4_ghz": ghz(4),
    }
)

DEFAULT_SAMPLING = 5


def make_case_for_2_qurries() -> list[
    tuple[
        CaseEntries[SEMeasureArgs, DummyAnalyzeArgs],
        CaseEntries[WEMeasureArgs, DummyAnalyzeArgs],
    ]
]:
    """Make a case data dictionary for two qurries.

    Args:
        circuit_name (str): The name of the circuit.
        expect_answer (float): The expected answer.

    Returns:
        The list of case entries tuples for two qurries.
    """
    se_and_we_cases: list[
        tuple[
            CaseEntries[SEMeasureArgs, DummyAnalyzeArgs],
            CaseEntries[WEMeasureArgs, DummyAnalyzeArgs],
        ]
    ] = []

    for circuit_name in circuits_lib.keys():
        circ = circuits_lib[circuit_name].copy()
        circ.measure_all()
        se_and_we_cases.append(
            (
                CaseEntries(
                    tags=(f"{circuit_name}", f"sampling_{DEFAULT_SAMPLING}"),
                    measure_entries={"wave": circ, "sampling": DEFAULT_SAMPLING},
                    analyze_entries={},
                    expect_answer={"default": ("ultimate_answer", 42)},
                ),
                CaseEntries(
                    tags=(f"{circuit_name}", f"repeating_{DEFAULT_SAMPLING}"),
                    measure_entries={"waves": [circ for i in range(DEFAULT_SAMPLING)]},
                    analyze_entries={},
                    expect_answer={"default": ("ultimate_answer", 42)},
                ),
            )
        )

    return se_and_we_cases


SE_AND_WE_CASES = make_case_for_2_qurries()


@pytest.mark.parametrize(["se_case", "we_case"], SE_AND_WE_CASES)
def test_measure_and_analyze_2_dummy(
    se_case: CaseEntries[SEMeasureArgs, DummyAnalyzeArgs],
    we_case: CaseEntries[WEMeasureArgs, DummyAnalyzeArgs],
) -> None:
    """Test orphan experiments of two dummy qurries.

    Args:
        se_case (CaseEntriesTuple[SEMeasureArgs, DummyAnalyzeArgs]):
            The test case item for SamplingExecuter.
        we_case (CaseEntriesTuple[WEMeasureArgs, DummyAnalyzeArgs]):
            The test case item for WavesExecuter.
    """

    exp_method_01 = SamplingExecuter()
    exp_method_02 = WavesExecuter()

    exp_01 = exp_method_01.measure(**se_case.measure_entries_with_tags())
    analysis_01 = exp_01.analyze(**se_case.analyze_entries)

    exp_02 = exp_method_02.measure(**we_case.measure_entries_with_tags())
    analysis_02 = exp_02.analyze(**we_case.analyze_entries)

    checker_list: list[AnalysisResultChecker] = []

    checker_list += [
        check_analysis_result(
            analysis_01.results[key],
            result_name=key,
            target_field=target_field,
            expect_answer=expect_answer_value,
            name=se_case.name,
        )
        for key, (target_field, expect_answer_value) in se_case.expect_answer.items()
    ]
    checker_list += [
        check_analysis_result(
            analysis_02.results[key],
            result_name=key,
            target_field=target_field,
            expect_answer=expect_answer_value,
            name=we_case.name,
        )
        for key, (target_field, expect_answer_value) in we_case.expect_answer.items()
    ]

    for checker in checker_list:
        checker.make_logger(logger)
    for checker in checker_list:
        checker.assert_correct()


def test_multi_output_all() -> None:
    """Test the multi-output experiment for all cases."""

    exp_method_01 = SamplingExecuter()
    exp_method_02 = WavesExecuter()

    se_cases, we_cases = zip(*SE_AND_WE_CASES)
    se_config_list, se_cases_with_tags = make_config_list_and_tagged_case(list(se_cases))
    we_config_list, we_cases_with_tags = make_config_list_and_tagged_case(list(we_cases))

    summoner_id_se = exp_method_01.multiOutput(
        se_config_list,
        backend=SIMULATOR,
        summoner_name="sampling_executer",
        save_location=EXPORT_DIR,
        multiprocess_build=True,
        multiprocess_write=False,
    )
    summoner_id_se, report_name_se = exp_method_01.multiAnalysis(
        summoner_id_se,
        analysis_name="test_report",
        no_serialize=True,
        specific_analysis_args=make_specific_analysis_args(
            exp_method_01, summoner_id_se, se_cases_with_tags
        ),
    )
    test_report_se: dict[tuple[str, ...], list[DummyAnalysis]] = exp_method_01.multimanagers[
        summoner_id_se
    ].all_reports(report_name_se)

    summoner_id_we = exp_method_02.multiOutput(
        we_config_list,
        backend=SIMULATOR,
        summoner_name="waves_executer",
        save_location=EXPORT_DIR,
        multiprocess_build=True,
        multiprocess_write=False,
    )
    summoner_id_we, report_name_we = exp_method_02.multiAnalysis(
        summoner_id_we,
        analysis_name="test_report",
        no_serialize=True,
        specific_analysis_args=make_specific_analysis_args(
            exp_method_02, summoner_id_we, we_cases_with_tags
        ),
    )
    test_report_we: dict[tuple[str, ...], list[DummyAnalysis]] = exp_method_02.multimanagers[
        summoner_id_we
    ].all_reports(report_name_we)

    checker_list = []
    for tags, report_list in test_report_se.items():
        assert len(report_list) == 1, (
            f"The report list length is wrong for tags {tags}: {len(report_list)} != 1."
        )
        checker_list += [
            check_analysis_result(
                report_list[0].results[key],
                result_name=key,
                target_field=target_field,
                expect_answer=expect_answer_value,
                name=se_cases_with_tags[tags].name,
            )
            for key, (target_field, expect_answer_value) in se_cases_with_tags[
                tags
            ].expect_answer.items()
        ]
    for tags, report_list in test_report_we.items():
        assert len(report_list) == 1, (
            f"The report list length is wrong for tags {tags}: {len(report_list)} != 1."
        )
        checker_list += [
            check_analysis_result(
                report_list[0].results[key],
                result_name=key,
                target_field=target_field,
                expect_answer=expect_answer_value,
                name=we_cases_with_tags[tags].name,
            )
            for key, (target_field, expect_answer_value) in we_cases_with_tags[
                tags
            ].expect_answer.items()
        ]

    for checker in checker_list:
        checker.make_logger(logger, extra_msg="multi-output all")
    for checker in checker_list:
        checker.assert_correct()

    multi_read_tests_exported_files(exp_method_01, summoner_id_se, EXPORT_DIR)
    multi_read_tests_exported_files(exp_method_02, summoner_id_we, EXPORT_DIR)
