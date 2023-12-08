"""
================================================================
Default Configuration for Qurry MultiManager
(:mod:`qurry.declare.multimanager`)
================================================================
"""
from ..capsule.mori import DefaultConfig
from ..tools.datetime import DatetimeDict

multicommonConfig = DefaultConfig(
    name="multicommon",
    default={
        "summoner_id": None,
        "summoner_name": None,
        "tags": [],
        "shots": 0,
        "backend": None,
        "save_location": None,
        "export_location": None,
        "files": {},
        "jobstype": None,
        "manager_run_args": {},
        "filetype": "json",
        "datetimes": DatetimeDict(),
    },
)
