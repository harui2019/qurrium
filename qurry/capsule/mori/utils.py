"""
================================================================
Utilities for :mod:`qurry.capsule.mori` --- *Mori* CapSule Utils
(:mod:`qurry.capsule.mori.utils`)
================================================================
"""

from typing import Literal, Union, Any

defaultOpenArgs: dict[Union[Literal["encoding"], str], Any] = {
    "mode": "w+",
    "encoding": "utf-8",
}
defaultPrintArgs = {}
defaultJsonDumpArgs = {
    "indent": 2,
    "ensure_ascii": False,
}
