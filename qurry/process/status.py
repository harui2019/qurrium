"""Check the availability of the post-processing modules. (:mod:`qurry.process.status`)"""

from typing import Literal

from .randomized_measure import (
    entangled_availability,
    entangled_v1_availability,
    overlap_availability,
    overlap_v1_availability,
)
from .hadamard_test import purity_echo_core_availability
from .magnet_square import magnet_square_availability
from .classical_shadow import (
    classical_shadow_matrix_availability,
)
from .string_operator import string_operator_availability

from .utils import (
    counts_process_availability,
    bit_slice_availability,
    randomized_availability,
    dummy_availability,
)
from .availability import BACKEND_TYPES
from ..version import __version__
from ..capsule.hoshi import Hoshi


def availability_status_print() -> tuple[
    Hoshi,
    dict[str, dict[str, dict[str, Literal["Yes", "Error", "Depr.", "No"]]]],
    dict[str, dict[str, dict[str, ImportError | None]]],
]:
    """Print the availability status of the post-processing modules.

    Returns:
        The Hoshi object for the availability status of the post-processing modules,
        the availability status of the post-processing modules,
        and the dictionary of errors occurred during the availability check.
    """
    availability_dict = [
        # randomized_measure
        entangled_availability,
        entangled_v1_availability,
        overlap_availability,
        overlap_v1_availability,
        # hadamard_test
        purity_echo_core_availability,
        # magnet_square
        magnet_square_availability,
        # string_operator
        string_operator_availability,
        # classical_shadow
        classical_shadow_matrix_availability,
        # utils
        randomized_availability,
        counts_process_availability,
        bit_slice_availability,
        dummy_availability,
    ]
    pre_hoshi = [
        ("txt", f"| Qurrium version: {__version__}"),
        ("divider", 75),
        ("h3", "Qurrium Post-Processing"),
        {
            "type": "itemize",
            "description": "Backend Availability",
            "value": " ".join([f"{bt}".ljust(6) for bt in BACKEND_TYPES]),
            "listing_level": 2,
            "ljust_description_filler": ".",
        },
    ]
    availability_status = {}
    errors_status = {}
    # pylint: disable=no-member
    for mod_location, available_dict, errors in availability_dict:
        mod1, *files_tmp = mod_location.split(".")
        files = ".".join(files_tmp)
        if mod1 not in availability_status:
            availability_status[mod1] = {}
            errors_status[mod1] = {}
            pre_hoshi.append(
                {
                    "type": "itemize",
                    "description": mod1,
                },
            )
        availability_status[mod1][files] = {}
        errors_status[mod1][files] = errors
        for bt in BACKEND_TYPES:
            availability_status[mod1][files][bt] = available_dict.get(bt, "No")
            errors_status[mod1][files][bt] = errors.get(bt, None)
        pre_hoshi.append(
            {
                "type": "itemize",
                "description": f"{files}",
                "value": " ".join(
                    [f"{availability_status[mod1][files][bt]}".ljust(6) for bt in BACKEND_TYPES]
                ),
                "listing_level": 2,
                "ljust_description_filler": ".",
            }
        )
    pre_hoshi.append(("divider", 75))
    for d, v in [
        ("Yes", "Working normally."),
        ("Error", "Exception occurred."),
        ("No", "Not supported."),
        ("Depr.", "Deprecated."),
    ]:
        pre_hoshi.append(
            {
                "type": "itemize",
                "description": d,
                "value": v,
                "listing_level": 2,
                "ljust_description_filler": ".",
                "listing_itemize": "+",
                "ljust_description_len": 10,
            }
        )
    pre_hoshi.append(("divider", 75))
    return Hoshi(pre_hoshi), availability_status, errors_status


AVAIBILITY_STATESHEET, AVAIBILITY_STATUS, ERROR_STATUS = availability_status_print()
