"""
================================================================
Default Configuration for Qurry Experimrnt 
(:mod:`qurry.declare.experiment`)
================================================================

"""
from pathlib import Path

from ..tools.backend import AerSimulator
from ..capsule.mori import DefaultConfig
from ..qurrium.utils.datetime import DatetimeDict

commonparamsConfig = DefaultConfig(
    name='commonparams',
    default={
        'expID': None,
        'waveKey': None,
        'shots': 1024,
        'backend': AerSimulator(),
        'provider': None,
        'runArgs': {},
        'runBy': 'gate',
        'transpileArgs': {},
        'decompose': None,
        'tags': (),
        'defaultAnalysis': [],
        'saveLocation': Path('./'),
        'filetype': 'json',
        'datetimes': DatetimeDict(),
        'serial': None,
        'summonerID': None,
        'summonerName': None,
    })

beforeConfig = DefaultConfig(
    name='before',
    default={
        'circuit': [],
        'figOriginal': [],
        'jobID': '',
        'expName': '',
        'sideProduct': {},
    })

afterConfig = DefaultConfig(
    name='after',
    default={
        'result': [],
        'counts': [],
    })
