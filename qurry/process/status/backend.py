"""
================================================================
Post-processing Status Conclusions
(:mod:`qurry.process.status.backend`)
================================================================
"""

from typing import Literal, Optional

from ..randomized_measure import (
    entangled_availability,
    purity_cell_availability,
    overlap_availability,
    echo_cell_availability,
)
from ..hadamard_test import purity_echo_core_availability
from ..magnet_square import magnet_square_availability

from ..utils import construct_availability, randomized_availability, dummy_availability
from ..availability import BACKEND_TYPES
from ...version import __version__
from ...capsule.hoshi import Hoshi


def availability_status_print() -> tuple[
    Hoshi,
    dict[str, dict[str, dict[str, Literal["Yes", "Error", "Depr.", "No"]]]],
    dict[str, dict[str, dict[str, Optional[ImportError]]]],
]:
    """Print the availability status of the post-processing modules.

    Returns:
        tuple[
            Hoshi,
            dict[str, dict[str, dict[str, Literal["Yes", "Error", "Depr.", "No"]]]],
            dict[str, dict[str, dict[str, Optional[ImportError]]]],
        ]:
            The Hoshi object for the availability status of the post-processing modules,
            the availability status of the post-processing modules and the errors.
    """
    availability_dict = [
        entangled_availability,
        purity_cell_availability,
        overlap_availability,
        echo_cell_availability,
        randomized_availability,
        construct_availability,
        dummy_availability,
        purity_echo_core_availability,
        magnet_square_availability,
    ]
    pre_hoshi = [
        ("txt", f"| Qurry version: {__version__}"),
        ("divider", 56),
        ("h3", "Qurry Post-Processing"),
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
    pre_hoshi.append(("divider", 56))
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
    pre_hoshi.append(("divider", 56))
    return Hoshi(pre_hoshi), availability_status, errors_status


AVAIBILITY_STATESHEET, AVAIBILITY_STATUS, ERROR_STATUS = availability_status_print()
