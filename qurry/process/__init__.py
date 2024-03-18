"""
================================================================
Post-processing module for Qurry
(:mod:`qurry.qurry.process`)

- All post-processing modules are here.
- This module should be no dependency on qiskit.
================================================================
"""

from typing import Union
from .randomized_measure import (
    entangled_availability,
    purity_cell_availability,
    overlap_availability,
    echo_cell_availability,
)
from .utils import construct_availability, randomized_availability
from .availability import BACKEND_TYPES
from ..capsule.hoshi import Hoshi


def availability_status_print() -> (
    tuple[Hoshi, dict[str, dict[str, dict[str, Union[bool, None]]]]]
):
    """Print the availability status of the post-processing modules.

    Returns: tuple[Hoshi, dict[str, dict[str, dict[str, Union[bool, None]]]]]
    """
    availability_dict = [
        entangled_availability,
        purity_cell_availability,
        overlap_availability,
        echo_cell_availability,
        randomized_availability,
        construct_availability,
    ]
    pre_hoshi = [
        ("divider", 56),
        ("h3", "Qurry Post-Processing"),
        {
            "type": "itemize",
            "description": "Backend Availability",
            "value": " ".join([f"{bt}".ljust(6) for bt in BACKEND_TYPES]),
            "listing_level": 2,
            "ljust_description_filler": " ",
        },
    ]
    availability_status = {}
    for (mod_location, available) in availability_dict:
        mod1, file1 = mod_location.split(".")
        print(mod1, file1, available)
        if mod1 not in availability_status:
            availability_status[mod1] = {}
            pre_hoshi.append(
                {
                    "type": "itemize",
                    "description": mod1,
                },
            )
        availability_status[mod1][file1] = {}
        for bt in BACKEND_TYPES:
            availability_status[mod1][file1][bt] = available.get(bt, None)
        pre_hoshi.append(
            {
                "type": "itemize",
                "description": f"{file1}",
                "value": " ".join(
                    [
                        f"{availability_status[mod1][file1][bt]}".ljust(6)
                        for bt in BACKEND_TYPES
                    ]
                ),
                "listing_level": 2,
                "ljust_description_filler": ".",
            }
        )
    pre_hoshi.append(("divider", 56))
    for d, v in [
        ("True", "Working normally."),
        ("False", "Exception occurred."),
        ("None", "Not supported yet."),
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
    return Hoshi(pre_hoshi), availability_status


AVAIBILITY_STATESHEET, AVAIBILITY_STATUS = availability_status_print()
