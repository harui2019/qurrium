from qiskit import Aer, QuantumCircuit
from qiskit.visualization import *
from qiskit.providers import Backend
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import json
import os
import numpy as np
from pathlib import Path
from math import pi
import gc
from typing import Union, Optional, List, Callable, Any, Iterable
from ...qurrent import EntropyMeasure
from ..general import configKeyCheckGeneral as configKeyCheck, typeCheck, syncControl
from ..quick import exportSyncJson as quickExportSyncJson
from . import drawTwoObject as quickDrawCircuit, drawResultPlot


def isHermitian(tgtOperator):
    try:
        return (tgtOperator.transpose().conjugate() == tgtOperator)
    except NameError:
        raise ModuleNotFoundError(
            "You need to import 'Operator' from 'qiskit.quantum_info'.")
    except AttributeError as e:
        raise NameError(
            f"{str(e)} is triggered, " +
            "check whether is 'Operator' defined " +
            "by the import from 'qiskit.quantum_info'")


def handleParams(
    collect: List[Union[int, List[int], dict[str, int]]]
) -> List[List[int]]:
    collectA = []
    for aItem in collect:
        if type(aItem) == list:
            collectA.append(aItem)
        elif type(aItem) == dict:
            if not 'degree' in aItem:
                raise KeyError("the degree of freedom is neccessary.")
            otherKey = [k for k in aItem.keys() if k != 'degree']
            collectA.append(
                [aItem['degree'], *[aItem[k] for k in otherKey]])
        elif type(aItem) == int:
            collectA.append([aItem])
        else:
            print(
                f"Unrecognized type of input '{type(aItem)} has been dropped.'")
    return collectA


def yLimDetector(
    demoPlotData: dict
) -> tuple[int, int]:
    maxSet, minSet = [], []
    yLimMax, yLimMin = 1.0, 0.0
    for listSingle in demoPlotData.values():
        maxSet.append(max(listSingle))
        minSet.append(min(listSingle))
    maxMax, minMin = max(maxSet), min(minSet)

    availableBound = [0, 1, 2, 4, 5, 8, 10, 16, 20]

    def boundDecision(extremeNum, availableBoundList):
        for boundNum in availableBoundList:
            yBound = (
                0.1 if boundNum == 0
                else boundNum+10**(np.floor(np.log10(boundNum))-1)
            )
            if extremeNum < yBound:
                break
        return yBound

    yLimMin = -boundDecision(minMin, availableBound)
    yLimMax = boundDecision(maxMax, availableBound)

    return yLimMin, yLimMax


def drawTwoObject(
    purityObject: dict,
    entropyObject: dict,
    saveFolderName: Path,
    config: dict[str],
    timeEvo: range,
    expListKeys: list[str]
) -> tuple[Figure, str, Figure, str]:

    purityPlotFig, purityFigName = drawResultPlot(
        plotObject=purityObject,
        plotObjectKey='Purity',
        timeEvoRange=timeEvo,
        beta=config['beta'],
        expListKeys=expListKeys,
        saveFolder=saveFolderName,
        configDraw={
            "fontSize": 12,
            "yLim": None,
            "lineStyle": "--",
            "format": "png",
            "dpi": 300,
        }
    )

    entropyPlotFig, entropyFigName = drawResultPlot(
        plotObject=entropyObject,
        plotObjectKey='Entropy',
        timeEvoRange=timeEvo,
        beta=config['beta'],
        expListKeys=expListKeys,
        saveFolder=saveFolderName,
        configDraw={
            "fontSize": 12,
            "yLim": None,
            "lineStyle": "--",
            "format": "png",
            "dpi": 300,
        }
    )

    return (
        purityPlotFig, purityFigName,
        entropyPlotFig, entropyFigName
    )


def paramsCollectInt(
    tgt: int
) -> List[List[int]]:
    return [[i] for i in range(tgt)]


def paramsCollectRange(
    tgt: range
) -> List[List[int]]:
    return [[i] for i in tgt]


def paramsCollectList(
    collect: List[Union[int, List[int], dict[str, int]]]
) -> List[List[int]]:
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
                f"Unrecognized type of input '{type(aItem)} has been dropped.'")
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
    paramsControlMethod = type(expSample)().paramsControl
    paramsHint = type(expSample)().defaultParaKey
    paramsControlList = [
        paramsControlMethod(params, 'dummy')[:2] for params in paramsCollect
    ]

    return configJsonable, timeEvo, paramsControlList, paramsHint


def main(
    expList: list[EntropyMeasure],
    saveFolderName: Path,
    config: dict,
    backend: Backend = Aer.get_backend('qasm_simulator')
) -> tuple[dict[str], dict, Figure, dict, Figure]:

    configJsonable, timeEvo, paramsCollect, paramsHint = paramsControl(
        config, expList[0]
    )
    gitignoreList = syncControl(["*.png", "*.json", "*.txt"])
    None if os.path.exists(saveFolderName) else os.mkdir(saveFolderName)

    quickStr: callable[[tuple[int, str]], str] = (
        lambda aNum, other: f"{aNum}_{other}")
    expListKeys = [quickStr(aNum, other) for aNum, other in paramsCollect]
    expItemKeys = {exp: {t: [] for t in timeEvo} for exp in expListKeys}
    # exp = quickStr(aNum, other)
    dataObject = {exp: {t: {} for t in timeEvo} for exp in expListKeys}

    for t in timeEvo:

        quickDrawCircuit(
            saveName=(saveFolderName, f"t={t}_drawOfWave"),
            syncList=gitignoreList,
            expDraw=expList[t].drawOfWave(
                figType=config['waveFigType'],
                composeMethod=config['waveComposeMethod']
            ),
            configDraw={
                'figType': config['waveFigType'],
                'composeMethod': config['waveComposeMethod'],
                'isSync': False,
            }
        )

        for aNum, other in paramsCollect:
            expList[t].go(
                params=[aNum, *other],
                runBy=config['goRunby'],
                figType=config['goFigType'],
                composeMethod=config['goComposeMethod'],
                shots=config['shots'],
                backend=backend
            )
            expItemKeys[quickStr(aNum, other)][t] = expList[t].current
            keyList = expList[t].base.keys()
            # keyList = 
            # expListKeys = 
            # [quickStr(aNum, other) for aNum, other in paramsCollect] = 
            # paramsCollect
            # 所以這裡因為結構錯誤直接多一層迴圈
            # 徒增O(len(paramsCollect))複雜度

            for expId in keyList:
                dataObject[t][expId] = {
                    "counts": expList[t].base[expId]['counts'],
                    "purity": expList[t].base[expId]['purity'],
                    "entropy": expList[t].base[expId]['entropy']
                }
                dataObject[quickStr(aNum, other)]
                expListKeys = [quickStr(aNum, other) for aNum, other in paramsCollect]
                expItemKeys = {exp: {t: [] for t in timeEvo} for exp in expListKeys}
                # exp = quickStr(aNum, other)
                dataObject = {exp: {t: {} for t in timeEvo} for exp in expListKeys}

                quickDrawCircuit(
                    saveName=(
                        saveFolderName,
                        f"t={t}-dimA={expId}_{quickStr(aNum, other)}_drawCircuit"),
                    syncList=gitignoreList,
                    expDraw=expList[t].base[expId]['fig'],
                    configDraw={
                        'figType': config['goFigType'],
                        'composeMethod': config['goComposeMethod'],
                        'isSync': False,
                    }
                )

                if config['singleResultKeep']:
                    with open(saveFolderName / (
                        f"t={t}-{expId}_dimA={quickStr(aNum, other)}_simpleResult.json"
                    ), 'w', encoding='utf-8'
                    ) as simpleResult:
                        json.dump(
                            expList[expId][t], simpleResult,
                            indent=2, ensure_ascii=False
                        )

                plt.clf()
                plt.figure(plot_histogram(
                    expList[t][t].base[expId]['counts'], title=f"t={t}"))
                if config['countPlotKeep']:
                    plt.savefig(saveFolderName / (
                        f"t={t}-{expId}_dimA={quickStr(aNum, other)}_counts.png"
                    ), format="png")
                plt.close()

            expList[t].reset(True)
            gc.collect()

    print(expItemKeys)

    for expId in keyList:
        dataObject[t][expId] = {
            "counts": expList[t].base[expId]['counts'],
            "purity": expList[t].base[expId]['purity'],
            "entropy": expList[t].base[expId]['entropy']
        }
    # exp = quickStr(aNum, other)
    purityObject = {
        exp: [
            expList[t][expItemKeys[exp][t]]['purity']
            for t in timeEvo]
        for exp in expListKeys}
    expListKeys = [quickStr(aNum, other) for aNum, other in paramsCollect]
    expItemKeys = {exp: {t: [] for t in timeEvo} for exp in expListKeys}

    entropyObject = {
        exp: [
            expList[t][expItemKeys[exp][t]]['entropy']
            for t in timeEvo]
        for exp in expListKeys}

    for saveName, saveObject in [
        ("all_simpleResult.json", dataObject),
        ("all_config.json", configJsonable),
        ("all_Purity.json", purityObject),
        ("all_Entropy.json", entropyObject),
    ]:
        quickExportSyncJson(
            (saveFolderName / saveName), gitignoreList, saveObject
        )

    (
        purityPlotFig, purityPlotFigName,
        entropyPlotFig, entropyPlotFigName
    ) = drawTwoObject(
        purityObject, entropyObject, saveFolderName,
        config, timeEvo, expListKeys
    )
    gitignoreList.sync(purityPlotFigName)
    gitignoreList.sync(entropyPlotFigName)

    gitignoreList.export(saveFolderName)

    if not config['simpleResultKeep']:
        print(
            "'dataObject' has been exported " +
            "and will be cleared to save memory allocation.")
        del dataObject
        gc.collect()
        dataObject = None
    else:
        print(
            "'dataObject' will be returned " +
            "but it may cause memory overallocated.")

    return (
        dataObject, purityObject, purityPlotFig, entropyObject, entropyPlotFig
    )
