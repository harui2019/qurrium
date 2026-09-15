"""Test qurry.process.classical_shadow module."""

from typing import TypedDict
from itertools import combinations
import logging
import pytest


from qurry.qurrium.utils import bitstring_mapping_getter
from qurry.process.utils import counts_list_recount_pyrust
from qurry.process.classical_shadow import (
    classical_shadow_complex,
    classical_shadow_matrix_availability,
    PurityValueKind,
    ShadowBasisType,
    RhoMethod,
    RhoMethodType,
    TraceMethod,
    TraceMethodType,
    verify_purity_value_kind,
)

from .utilities import (
    quick_json_read,
    get_dummy_file_path,
    assert_numerical_tolerance_check,
    FloatType,
    no_error_and_msg_of_availability,
)

logger = logging.getLogger(__name__)


class ClassicalShadowTarget(TypedDict):
    """The test target type for classical_shadow_complex function parameters."""

    shots: int
    """Number of shots."""
    counts: list[dict[str, int]]
    """The counts dictionary list."""
    random_basis: dict[str, dict[str, int]]
    """The random unitary identifiers."""
    selected_qubits: list[int]
    """The selected qubits."""

    snapshots: int
    """The number of snapshots."""
    registers_mapping: dict[str, int]
    """The register mapping."""
    actual_num_qubits: int
    """The number of qubits."""
    unitary_located: list[int]
    """The unitary located positions."""

    shadow_basis: ShadowBasisType
    """The shadow basis type."""
    # Only "RY_RX_RZ"


class ClassicalShadowAnswer(TypedDict):
    """The test answer type for classical_shadow_complex function parameters."""

    purity: FloatType
    """The purity value."""
    entropy: FloatType
    """The entropy value."""


class ClassicalShadowCase(TypedDict):
    """The test case type for classical_shadow_complex function."""

    target: ClassicalShadowTarget
    """The target parameters for the classical_shadow_complex function."""
    answer: dict[PurityValueKind, ClassicalShadowAnswer]
    """The expected answer from the classical_shadow_complex function."""


class ClassicalShadowEntries(TypedDict):
    """The test target type for classical_shadow_complex
    function parameters with processed counts."""

    shots: int
    """Number of shots."""
    counts: list[dict[str, int]]
    """The counts dictionary list."""
    random_basis_array: list[list[int]]
    """The random basis array."""
    selected_classical_registers: list[int]
    """The selected classical registers."""

    shadow_basis: ShadowBasisType
    """The shadow basis type."""
    # Only "RY_RX_RZ"


DUMMY_CASE_FILE = get_dummy_file_path("shadow_purity.json")
DUMMY_CASES_JSON: list[ClassicalShadowCase] = quick_json_read(DUMMY_CASE_FILE)
shadow_cases_entries = [
    (case["target"], respect_answer, kind_name)
    for case in DUMMY_CASES_JSON
    for kind_name, respect_answer in case["answer"].items()
    if kind_name != "bitwise"
]


def generate_entries(target: ClassicalShadowTarget) -> ClassicalShadowEntries:
    """Wrapper for the classical_shadow_complex function to include the trace of the expect_rho.

    Args:
        target (ClassicalShadowTarget): The raw target parameters.

    Return:
        ClassicalShadowEntries: The processed target parameters.
    """

    if len(target["random_basis"]) != target["snapshots"]:
        raise ValueError(
            f"The number of random basis should be {target['snapshots']}, "
            + f"but got {len(target['random_basis'])}."
        )
    actual_register_mapping = {int(k): v for k, v in target["registers_mapping"].items()}
    bitstring_mapping, final_mapping = bitstring_mapping_getter(
        target["counts"], actual_register_mapping
    )

    actual_selected_qubits = (
        [qi % target["actual_num_qubits"] for qi in target["selected_qubits"]]
        if target["selected_qubits"]
        else list(bitstring_mapping.keys())
    )
    if len(set(actual_selected_qubits)) != len(actual_selected_qubits):
        raise ValueError(
            "selected_qubits should not have duplicated elements, "
            + f"but got {target['selected_qubits']}."
        )

    all_clregs = sorted(target["registers_mapping"].values())
    acutual_random_basis = {
        int(k): {int(k2): int(v2) for k2, v2 in v.items()}
        for k, v in target["random_basis"].items()
    }
    random_basis_array: list[list[int]] = []
    for i in range(len(target["random_basis"])):
        tmp = {
            ci: acutual_random_basis[i][n_u_qi] for n_u_qi, ci in actual_register_mapping.items()
        }
        random_basis_array.append([tmp[j] for j in all_clregs])

    return {
        "shots": target["shots"],
        "counts": counts_list_recount_pyrust(
            target["counts"],
            len(next(iter(target["counts"][0].keys()))),
            list(final_mapping.values()),
        ),
        "random_basis_array": random_basis_array,
        "selected_classical_registers": sorted(
            [final_mapping[qi] for qi in actual_selected_qubits]
        ),
        "shadow_basis": target["shadow_basis"],
    }


def generate_trying_methods() -> dict[PurityValueKind, list[tuple[RhoMethodType, TraceMethodType]]]:
    """Generate the trying methods for each purity value kind.

    Returns:
        dict[PurityValueKind, list[tuple[RhoMethodType, TraceMethodType]]]:
            The trying methods for each purity value kind.
    """
    methods_by_kind = {}

    for rho_method_tmp in RhoMethod.get_all_methods():
        for trace_method_tmp in TraceMethod.get_all_methods():
            if trace_method_tmp == TraceMethod.SKIP_TRACE.value:
                continue
            methods_by_kind.setdefault(
                verify_purity_value_kind(rho_method_tmp, trace_method_tmp), []
            ).append((rho_method_tmp, trace_method_tmp))

    return methods_by_kind


METHODS_BY_KIND = generate_trying_methods()


def test_availability():
    """Test the availability of the Rust backend for the entangled_entropy_core function."""

    for module_location, avails_backends, errors in [
        classical_shadow_matrix_availability,
    ]:
        for backend_label in avails_backends.keys():
            is_no_error, msg = no_error_and_msg_of_availability(
                (module_location, avails_backends, errors), backend_label
            )
            if is_no_error:
                logger.info(msg)
            else:
                logger.error(msg)
            assert is_no_error, msg


@pytest.mark.parametrize(["target", "answer", "kind_name"], shadow_cases_entries)
def test_shadow(
    target: ClassicalShadowTarget, answer: ClassicalShadowAnswer, kind_name: PurityValueKind
):
    """Test the classical_shadow_complex function."""

    entries = generate_entries(target)

    results = {"answer": answer}
    for rho_method, trace_method in METHODS_BY_KIND[kind_name]:
        _basic_tmp, purity_result_tmp, estimation_tmp = classical_shadow_complex(
            **entries,
            rho_method=rho_method,
            trace_method=trace_method,
        )
        assert estimation_tmp is None, (
            "The estimation result should be None in classical_shadow_complex function."
            + "For it's not used with current entries."
        )
        assert purity_result_tmp is not None, (
            "The purity result should not be None in classical_shadow_complex function."
        )
        results[f"{rho_method}.{trace_method}"] = purity_result_tmp

    for (name_1, result_1), (name_2, result_2) in combinations(results.items(), 2):
        assert_numerical_tolerance_check(
            "classical_shadow_complex.purity",
            result_1["purity"],
            name_1,
            result_2["purity"],
            name_2,
            logger,
        )
        assert_numerical_tolerance_check(
            "classical_shadow_complex.entropy",
            result_1["entropy"],
            name_1,
            result_2["entropy"],
            name_2,
            logger,
        )
