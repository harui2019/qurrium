from typing import Union
from ...qurrent import EntropyMeasure, EntropyMeasureV1
from ..general import *


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


def typeCheck(
    target: any,
    typeWantAndHandle: list[tuple[type, Union[type, Callable]]]
) -> Union[Exception, any]:
    """Check whether the parameter is the type which required, then  
    transform into another type or handle it with specific function.

    Args:
        target (any): The parameter
        typeWantAndHandle (list[tuple[type, Union[type, Callable]]]): 
            The required type and the 

    Raises:
        TypeError: When there is no type which meet the requirement.

    Returns:
        Union[Exception, any]: The result of handle the parameter or 
            the error which the parameter does not meet the requirement.
    """
    checkedList = []
    for typeWant, handle in typeWantAndHandle:
        checkedList.append(f'{typeWant}')
        if type(target) == typeWant:
            handle = (lambda x: x) if handle == None else handle
            return handle(target)

    raise TypeError(
        'Expected'.join([f"'{typeWant}', " for typeWant, _ in checkedList[:-1]]) +
        f"or '{checkedList[-1]}', but got '{type(target)}'. "
    )
    

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
