"""Test the Qurrium Runtime :class:`EchoListenRandomized`.

It's from :class:`~qurry.qurry.qurries.echo_randomized.qurry.EchoListenRandomized`.
"""

from typing import TypedDict
import logging
import pytest

from qiskit import QuantumCircuit

from qurry.qurries.echo_randomized import EchoListenRandomized, ELRMeasureArgs
from qurry.qurries.echo_randomized.analysis import ELRAnalyzeArgs, ELRAnalysis
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
from .utilities.circuits import (
    cx_dyn_comparing,
    dummy_two_body_measurement,
    make_ghz_overlap_case,
    preparing_circuits_lib,
)


logger = logging.getLogger(__name__)

SIMULATOR = get_seeded_simulator()

RANDOM_UNITARY_SEEDS = prepare_random_unitary_seeds()

THRESHOLD = 0.125


class CaseDataDictABC(TypedDict):
    """Case data dictionary for testing."""

    circuits: tuple[QuantumCircuit, QuantumCircuit]
    """The quantum circuit to be tested."""


class CaseDataDict(CaseDataDictABC, total=False):
    """Case data dictionary for testing."""

    target_echo: float
    """The overlap value for the test case."""
    measure_range: tuple[list[int] | None, list[int] | None]
    """The measurement range for the test case."""
    selected_clregs: list[int] | None
    """The selected qubits for analysis."""
    times: int
    """The number of random unitaries."""


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
        # GHZ with other GHZ cases
        "4_ghz-00": make_ghz_overlap_case(4, "00"),
        "4_ghz-01": make_ghz_overlap_case(4, "01"),
        "4_ghz-10": make_ghz_overlap_case(4, "10"),
        "4_ghz-11": make_ghz_overlap_case(4, "11"),
        "4_ghz-x-init": make_ghz_overlap_case(4, "x-init-ghz"),
        "4_ghz-singlet": make_ghz_overlap_case(4, "singlet"),
        "4_ghz-intracell-plus": make_ghz_overlap_case(4, "intracell-plus"),
        # CXDynamic cases
        "4_cx-dyn": cx_dyn_comparing(4, name="4-cx-dyn"),
        "6_cx-dyn": cx_dyn_comparing(6, name="6-cx-dyn"),
        "4_cx-dyn-comparison": cx_dyn_comparing(4, name="4-cx-dyn-comparison", mode="comparison"),
        "6_cx-dyn-comparison": cx_dyn_comparing(6, name="6-cx-dyn-comparison", mode="comparison"),
    }
)


def making_pair(name1: str, name2: str | None = None) -> tuple[QuantumCircuit, QuantumCircuit]:
    """Make a pair of circuits from names.

    Args:
        name1 (str): The name of the first circuit.
        name2 (str | None): The name of the second circuit. If None, use name1.

    Returns:
        tuple[QuantumCircuit, QuantumCircuit]: The pair of circuits.
    """
    if name2 is None:
        name2 = name1
    return (circuits_lib[name1].copy(), circuits_lib[name2].copy())


case_datas: list[CaseDataDict] = [
    {"circuits": making_pair("4_trivial"), "target_echo": 1.0, "times": 50},
    {"circuits": making_pair("4_ghz"), "target_echo": 0.5, "times": 50},
    {"circuits": making_pair("4_topological-period"), "target_echo": 0.25, "times": 50},
    {"circuits": making_pair("6_trivial"), "target_echo": 1.0, "times": 50},
    {"circuits": making_pair("6_ghz"), "target_echo": 0.5, "times": 50},
    {"circuits": making_pair("6_topological-period"), "target_echo": 0.25, "times": 50},
    # Two-body with measurement cases
    {
        "circuits": making_pair("4_dummy-2-body-with-clbits"),
        "target_echo": 1.0,
        "measure_range": ([2, 3], [2, 3]),
    },
    {
        "circuits": making_pair("6_dummy-2-body-with-clbits"),
        "target_echo": 1.0,
        "measure_range": ([4, 5], [4, 5]),
    },
    # GHZ with other GHZ cases
    {"circuits": making_pair("4_ghz", "4_ghz-00"), "target_echo": 0.5},
    {"circuits": making_pair("4_ghz", "4_ghz-01"), "target_echo": 0},
    {"circuits": making_pair("4_ghz", "4_ghz-10"), "target_echo": 0},
    {"circuits": making_pair("4_ghz", "4_ghz-11"), "target_echo": 0.5},
    {"circuits": making_pair("4_ghz", "4_ghz-x-init"), "target_echo": 0.5},
    {
        "circuits": making_pair("4_ghz", "4_ghz-singlet"),
        "target_echo": 0,
        "measure_range": (list(range(4)), list(range(4))),
    },
    {
        "circuits": making_pair("4_ghz", "4_ghz-intracell-plus"),
        "target_echo": 0,
        "measure_range": (list(range(4)), list(range(4))),
    },
]
case_datas_extra: list[CaseDataDict] = [
    {
        "circuits": making_pair("4_cx-dyn", "4_cx-dyn"),
        "target_echo": 1.0,
        "measure_range": ([0, 3], [0, 3]),
        "selected_clregs": [0, 3],
    },
    {
        "circuits": making_pair("6_cx-dyn", "6_cx-dyn"),
        "target_echo": 1.0,
        "measure_range": ([0, 5], [0, 5]),
        "selected_clregs": [0, 5],
    },
    {
        "circuits": making_pair("4_cx-dyn", "4_cx-dyn"),
        "target_echo": 0.5,
        "measure_range": ([0], [0]),
        "selected_clregs": [0],
    },
    {
        "circuits": making_pair("6_cx-dyn", "6_cx-dyn"),
        "target_echo": 0.5,
        "measure_range": ([0], [0]),
        "selected_clregs": [0],
    },
    # not self overlap cases
    {
        "circuits": making_pair("4_cx-dyn", "4_cx-dyn-comparison"),
        "target_echo": 1.0,
        "measure_range": ([0, 3], [0, 3]),
        "selected_clregs": list(range(-2, 0)),
    },
    {
        "circuits": making_pair("6_cx-dyn", "6_cx-dyn-comparison"),
        "target_echo": 1.0,
        "measure_range": ([0, 5], [0, 5]),
        "selected_clregs": list(range(-2, 0)),
    },
]

if SIM_DEFAULT_SOURCE == "qiskit_aer":
    case_datas.extend(case_datas_extra)  # only add these cases when Qiskit Aer is used


DEFAULT_TIMES = 80
DEFAULT_SELECTED_CLREGS = list(range(-2, 0))


def make_case_entries(
    case_data: CaseDataDict, times: int = DEFAULT_TIMES
) -> CaseEntries[ELRMeasureArgs, ELRAnalyzeArgs]:
    """Make case entries from case data.

    Args:
        case_data (CaseDataDict): The case data.
        times (int): The number of random unitaries. Default is 20.
        shots (int): The number of shots. Default is 1024.

    Returns:
        CaseEntriesTuple[ELRMeasureArgs, ELRAnalyzeArgs]: The case entries.
    """

    num_qubits_1 = case_data["circuits"][0].num_qubits
    num_qubits_2 = case_data["circuits"][1].num_qubits
    measure_range_1, measure_range_2 = case_data.get("measure_range", (None, None))
    if num_qubits_1 != num_qubits_2:
        if measure_range_1 is None or measure_range_2 is None:
            raise ValueError(
                "When the two circuits have different number of qubits, "
                + "the measurement ranges must be provided."
            )
        if len(measure_range_1) != len(measure_range_2):
            raise ValueError(
                "When the two circuits have different number of qubits, "
                + "the measurement ranges must have the same length."
            )
        actual_qubits_num = len(measure_range_1)
    else:
        actual_qubits_num = num_qubits_1

    random_unitary_seeds = {i: RANDOM_UNITARY_SEEDS[actual_qubits_num][i] for i in range(times)}

    return CaseEntries(
        tags=(f"{case_data['circuits'][0].name}_{case_data['circuits'][1].name}",),
        measure_entries={
            "wave1": case_data["circuits"][0],
            "wave2": case_data["circuits"][1],
            "backend": SIMULATOR,
            "times": times,
            "random_unitary_seeds": random_unitary_seeds,
            "measure_1": measure_range_1,
            "measure_2": measure_range_2,
        },
        analyze_entries={
            "selected_classical_registers": case_data.get(
                "selected_clregs", DEFAULT_SELECTED_CLREGS
            )
        },
        expect_answer={"target_system": ("echo", case_data.get("target_echo", 1.0))},
    )


CASES = [make_case_entries(case_data) for case_data in case_datas]


@pytest.mark.parametrize("case_entries", CASES)
def test_measure_and_analyze(
    case_entries: CaseEntries[ELRMeasureArgs, ELRAnalyzeArgs],
) -> None:
    """Test orphan experiments.

    Args:
        case_entries (CaseEntriesTuple[ELRMeasureArgs, ELRAnalyzeArgs]): The test case item.
    """

    exp_method = EchoListenRandomized()
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

    exp_method = EchoListenRandomized()

    config_list, cases_with_tags = make_config_list_and_tagged_case(CASES)

    summoner_id = exp_method.multiOutput(
        config_list,
        backend=SIMULATOR,
        summoner_name="echo_randomized",
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
    test_report: dict[tuple[str, ...], list[ELRAnalysis]] = exp_method.multimanagers[
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
