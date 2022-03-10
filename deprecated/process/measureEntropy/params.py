from typing import Union
from ....qurrent import EntropyMeasure, EntropyMeasureV1
from ..general import *

"""Params.py is used to control the experiment parameters input.

Raises:
    KeyError: [description]

Returns:
    [type]: [description]
"""

class configuration(dict):
    def __init__(
        self,
        default: dict = {
            "measure": "None",
            "experiment": "None",

            "qPairNum": 1,
            "qNum": 2,
            "boundaryCond": 'period',
            "alpha": 0,
            "beta": 0,

            "circuitRunBy": "operator",
            "initSet": None,
            "hamiltonianIndex": None,

            "timeEvo": range(11),
            "collectA": [[1]],

            "waveFigType": 'text',
            "waveComposeMethod": "decompose",

            "goRunby": "gate",
            "goFigType": 'text',
            "goComposeMethod": None,
            "shots": 1024,

            'singleResultKeep': False,
            'countPlotKeep': False,
            'simpleResultKeep': False,

            "expNum": None,
            "demoNum": None,
        },
        configName: str = 'configuration'
    ) -> None:

        self.configName = configName
        self.default = default
        self.config = {
            **self.default,
        }
        super().__init__(self.config)

    def make(
        self,
        inputObject: dict = {},
    ) -> dict:

        self.config = {
            **self.default,
            **inputObject,
        }
        super().__init__(self.config)

        return self.copy()

    def configKeyCheck(
        self,
        target: dict,
    ) -> list:
        """Check whether the configuration is completed.

        Args:
            target (dict): The configuration.

        Raises:
            KeyError: When configuration is not completed.

        Returns:
            list: The keys of the configuration.
        """

        targetKeys = list(target.keys())
        for k in self.default:
            if not k in targetKeys:
                print(target)
                raise KeyError(
                    f"{k}' is lost in Configuration, make sure it has been configured.")
        return targetKeys

    def __repr__(self):
        return f"{self.configName}({self.config})"


def configKeyCheck(
    target: dict,
    keyCheck: list[str] = [
        'qPairNum', 'boundaryCond', 'alpha', 'beta',
        'circuitRunBy', 'initSet', 'hamiltonianIndex', 'timeEvo',
        'collectA', 'waveFigType', 'waveComposeMethod',
        'goRunby', 'goFigType', 'goComposeMethod',
        'shots', 'singleResultKeep', 'countPlotKeep',
    ]
) -> list:
    return configKeyCheckGeneral(target, keyCheck)


def paramsCollectInt(
    tgt: int
) -> list[list[int]]:
    return [[i] for i in range(tgt)]


def paramsCollectRange(
    tgt: range
) -> list[list[int]]:
    return [[i] for i in tgt]


def paramsCollectList(
    collect: list[Union[int, list[int], dict[str, int]]]
) -> list[list[int]]:
    collectA = []
    for aItem in collect:
        if type(aItem) == list:
            collectA.append(aItem)
        elif type(aItem) == dict:
            collectA.append(aItem)
        elif type(aItem) == int:
            collectA.append([aItem])
        else:
            print(
                f"Unrecognized type of input '{type(aItem)}'" +
                " of '{aItem}' has been dropped.'")
    return collectA


def paramsControl(
    config: dict,
    expSample: EntropyMeasure,
) -> tuple[list[str], range, list[tuple[int, list[int]]], list[str]]:
    """ From parameters list isolated the degree of freedom and
        other parameters.

    Args: 
        config (dict): The configuration of experiment.
        expSample (EntropyMeasure): Check which experiment runs

    Returns:
        tuple[list[str], range, list[tuple[int, list[int]]], list[str]]: 
            The parameters will use for the following execution.
    """

    configKeys = configKeyCheck(config)
    configJsonable = {k: str(config[k]) for k in configKeys}
    timeEvo = typeCheck(
        config['timeEvo'],
        [(int, range), (range, None)]
    )
    paramsCollect = typeCheck(
        config['collectA'], [
            (int, paramsCollectInt),
            (range, paramsCollectRange),
            (list, paramsCollectList)]
    )
    # typeKeep = type(expSample)()
    typeKeep = expSample
    print(typeKeep)
    
    if isinstance(typeKeep, EntropyMeasureV1):
        paramsControlMethod = typeKeep.paramsControl
        paramsHint = typeKeep.defaultParaKey
        paramsControlList = [
            paramsControlMethod(params, 'dummy')[:2] for params in paramsCollect
        ]
    else:
        paramsControlMethod = typeKeep.paramsControl
        paramsHint = typeKeep.measureConfig['defaultParamsHint']
        paramsControlList = [
            paramsControlMethod(params=params, expId='dummy')[2:3] for params in paramsCollect
        ]

    return configJsonable, timeEvo, paramsControlList, paramsHint
