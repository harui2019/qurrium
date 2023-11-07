"""
================================================================
Default Configuration for Qurry MultiManager
(:mod:`qurry.declare.multimanager`)
================================================================
"""
from ..capsule.mori import DefaultConfig
from ..qurrium.utils.datetime import DatetimeDict

multicommonConfig = DefaultConfig(
    name='multicommon',
    default={
        'summonerID': None,
        'summonerName': None,
        'tags': [],
        'shots': 0,
        'backend': None,
        'saveLocation': None,
        'exportLocation': None,
        'files': {},
        'jobsType': None,
        'managerRunArgs': None,
        'filetype': 'json',
        'datetimes': DatetimeDict(),
    }
)
