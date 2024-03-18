"""
================================================================
Default Configuration for Qurry Experimrnt 
(:mod:`qurry.declare.experiment`)
================================================================

"""
from pathlib import Path

from ..tools.backend import GeneralSimulator
from ..capsule.mori import DefaultConfig
from ..tools.datetime import DatetimeDict

commonparamsConfig = DefaultConfig(
    name="commonparams",
    default={
        "exp_id": None,
        "wave_key": None,
        "shots": 1024,
        "backend": GeneralSimulator(),
        "provider": None,
        "run_args": {},
        "runBy": "gate",
        "transpile_args": {},
        "decompose": None,
        "tags": (),
        "default_analysis": [],
        "save_location": Path("./"),
        "filetype": "json",
        "datetimes": DatetimeDict(),
        "serial": None,
        "summoner_id": None,
        "summoner_name": None,
    },
)

beforeConfig = DefaultConfig(
    name="before",
    default={
        "circuit": [],
        "fig_original": [],
        "job_id": "",
        "exp_name": "",
        "side_product": {},
    },
)

afterConfig = DefaultConfig(
    name="after",
    default={
        "result": [],
        "counts": [],
    },
)
