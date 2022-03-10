from qiskit.visualization import plot_histogram
from qiskit import Aer, QuantumCircuit
from qiskit.providers import Backend
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import json
import os
import numpy as np
from pathlib import Path
from math import pi
import gc
import warnings
from typing import Optional, Callable
from ....qurrent import EntropyMeasure, getMeasurement
from ..general import yLimDetector, syncControl
from ..quick import drawCircuit, exportSyncJson, readJson
from .params import paramsControl, configuration


def drawResultPlot(
    plotObject: dict,
    plotObjectKey: str,
    timeEvoRange: range,
    beta: float,
    expListKeys: list,
    saveFolder: Path,
    configDraw: dict = {},
    configForEach: Optional[list[dict[str]]] = {},
) -> tuple[Figure, str]:
    """[summary]

    Args:
        plotObject (dict): [description]
        plotObjectKey (str): [description]
        timeEvoRange (range): [description]
        beta (float): [description]
        expListKeys (list): [description]
        saveFolder (Path): [description]
        configDraw (dict, optional): [description]. Defaults to {}.
        configForEach (Optional[list[dict[str]]], optional): [description]. Defaults to {}.

    Returns:
        tuple[Figure, str]: [description]
    """

    configDefault = {
        "fontSize": 12,
        "yLim": yLimDetector(plotObject),
        "lineStyle": "--",
        "format": "png",
        "dpi": 300,
        "alpha": 0.7,
        "marker": '.',
    }
    configForEachWork = {
        exp: {
            **configDefault,
            **configForEach[exp],
        } for exp in configForEach
    }

    configDrawWork = {
        **configDefault,
        **configDraw,
    }

    plotFigName = f"all_{plotObjectKey}.{configDrawWork['format']}"
    fileName = saveFolder / plotFigName

    indexOfReDraw = 0
    while os.path.exists(fileName):
        indexOfReDraw += 1
        fileName = saveFolder / (
            f"all_{plotObjectKey}_{indexOfReDraw}.{configDrawWork['format']}")
    gitignoreList = syncControl()
    gitignoreList.sync(fileName.name)
    gitignoreList.add(saveFolder)

    timeEvoNum = len(timeEvoRange)
    plotFig = plt.figure()
    ax = plotFig.add_subplot(1, 1, 1)

    ax.set_xlabel(
        f'evolution ($\Delta t = {beta/pi} \pi$)', size=configDrawWork["fontSize"])
    ax.set_ylabel(f'{plotObjectKey}', size=configDrawWork["fontSize"])

    (plt.ylim(configDrawWork['yLim']) if bool(
        configDrawWork['yLim']) else None)

    if beta != 0:
        betaPiNum = ((beta/pi) if beta != 0 else 1/4)
        piFourthIden = int(1/(4*betaPiNum))
        [plt.axvline(x=i, color='r', alpha=0.3) for i in np.linspace(
            0, timeEvoNum - 1, int((timeEvoNum - 1)/piFourthIden + 1)
        ) if (
            (i % piFourthIden == 0) and (i % (piFourthIden*2) != 0)
        )]

    ax.set_xticks(timeEvoRange)
    ax.set_xticklabels(
        [i if (i % 5 == 0) else None for i in timeEvoRange])
    ax.grid(linestyle=configDrawWork["lineStyle"])

    cutToJ: Callable[[float], float] = (
        lambda x: x * (beta if beta != 0 else 1/4))
    JToCut: Callable[[float], float] = (
        lambda x: x * 1/(beta if beta != 0 else 1/4))

    secax = ax.secondary_xaxis('top', functions=(cutToJ, JToCut))
    secax.set_xlabel(f'$Jt$', size=configDrawWork["fontSize"])

    print(
        "The following numbers are the result at specific number of subsystem A",
        expListKeys
    )

    for exp in expListKeys:
        if exp in configForEach:
            ax.plot(
                timeEvoRange,
                plotObject[exp],
                marker=configForEachWork[exp]['marker'],
                label=f"{exp}",
                alpha=configForEachWork[exp]['alpha'],
            ),
        else:
            ax.plot(
                timeEvoRange, plotObject[exp],
                marker=configDrawWork['marker'],
                label=f"{exp}",
                alpha=configDrawWork['alpha'],
            )

    legendPlt = ax.legend(
        bbox_to_anchor=(1.025, 1.0),
        loc='upper left',
        borderaxespad=0.)

    plotFig = plt.savefig(
        fileName,
        format=configDrawWork["format"],
        dpi=configDrawWork['dpi'],
        bbox_extra_artists=(legendPlt, secax,),
        bbox_inches='tight'
    )
    return plotFig, plotFigName


def drawTwoObject(
    purityObject: dict,
    entropyObject: dict,
    saveFolderName: Path,
    config: dict[str],
    timeEvo: range,
    expListKeys: list[str],
    configDraw: dict = {},
    configForEach: Optional[list[dict[str]]] = {},
) -> tuple[Figure, str, Figure, str]:
    """[summary]

    Args:
        purityObject (dict): [description]
        entropyObject (dict): [description]
        saveFolderName (Path): [description]
        config (dict[str]): [description]
        timeEvo (range): [description]
        expListKeys (list[str]): [description]
        configDraw (dict, optional): [description]. Defaults to {}.
        configForEach (Optional[list[dict[str]]], optional): [description]. Defaults to {}.

    Returns:
        tuple[Figure, str, Figure, str]: [description]
    """

    configDefault = {
        "fontSize": 12,
        "yLim": (-0.1, 1.1),
        "lineStyle": "--",
        "format": "png",
        "dpi": 300,
        "alpha": 0.7,
        "marker": '.',
    }
    configForEachWork = {
        exp: {
            **configDefault,
            **configForEach[exp],
        } for exp in configForEach
    }

    configDrawWork = {
        **configDefault,
        **configDraw,
    }

    purityPlotFig, purityFigName = drawResultPlot(
        plotObject=purityObject,
        plotObjectKey='Purity',
        timeEvoRange=timeEvo,
        beta=config['beta'],
        expListKeys=expListKeys,
        saveFolder=saveFolderName,
        configDraw=configDrawWork,
        configForEach=configForEachWork,
    )

    entropyPlotFig, entropyFigName = drawResultPlot(
        plotObject=entropyObject,
        plotObjectKey='Entropy',
        timeEvoRange=timeEvo,
        beta=config['beta'],
        expListKeys=expListKeys,
        saveFolder=saveFolderName,
        configDraw=configDrawWork,
        configForEach=configForEachWork,
    )

    return (
        purityPlotFig, purityFigName,
        entropyPlotFig, entropyFigName
    )


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


def readExport(
    saveFolderName: Path
) -> tuple[dict[str], dict[str], dict[str], dict[str]]:
    """Read result of previous export.

    Args:
        saveFolderName (Path): Location of previous export.

    Returns:
        tuple[dict[str], dict[str], dict[str], dict[str]]: Result.
    """

    dataObject = readJson(saveFolderName / "all_simpleResult.json")
    configJsonable = readJson(saveFolderName / "all_config.json")
    purityObject = readJson(saveFolderName / "all_Purity.json")
    entropyObject = readJson(saveFolderName / "all_Entropy.json")

    return (
        dataObject, configJsonable, purityObject, entropyObject
    )


def readToDrawTwoObject(
    saveFolderName: Path,
    config: dict[str],
) -> tuple:
    dataObject, configOringin, purityObject, entropyObject = readExport(
        saveFolderName)

    configJsonable, timeEvo, paramsCollect, paramsHint = paramsControl(
        config, getMeasurement(configOringin['measure'])(
            QuantumCircuit(configOringin['qPairNum']*2)
        )
    )

    (
        purityPlotFig, purityFigName,
        entropyPlotFig, entropyFigName
    ) = drawTwoObject(
        purityObject=purityObject,
        entropyObject=entropyObject,
        saveFolderName=saveFolderName,
        config=config,
        timeEvo=timeEvo,
        expListKeys=dataObject.keys(),
        configDraw={
            "yLim": yLimDetector(entropyObject),
        },
        # configForEach={},
    )

    return (
        purityPlotFig, purityFigName,
        entropyPlotFig, entropyFigName
    )


def dataIntegrated(
    purityObject1: dict,
    entropyObject1: dict,
    config1: dict[str],
    purityObject2: dict,
    entropyObject2: dict,
    config2: dict[str],
) -> tuple[dict, dict, list[zip]]:
    """Integrate two data.

    Args:
        purityObject1 (dict): Purity data of first experiment.
        entropyObject1 (dict): Entropy data of first experiment.
        config1 (dict[str]): Configuration data of first experiment.
        purityObject2 (dict): Purity data of second experiment.
        entropyObject2 (dict): Entropy data of second experiment.
        config2 (dict[str]): Configuration data of second experiment.

    Raises:
        ValueError: When two experiment has different beta (time step length).

    Returns:
        tuple[dict, dict, list[zip]]: The data which combined two experiment.
    """

    configJsonable1, timeEvo1, paramsCollect1, paramsHint1 = paramsControl(
        config1, getMeasurement(config1['measure'])(
            QuantumCircuit(config1['qPairNum']*2)
        )
    )
    configJsonable2, timeEvo2, paramsCollect2, paramsHint2 = paramsControl(
        config2, getMeasurement(config2['measure'])(
            QuantumCircuit(config2['qPairNum']*2)
        )
    )
    if configJsonable1['beta'] != configJsonable2['beta']:
        raise ValueError(
            f"Length of each time step are different," +
            f" respectly {configJsonable1['beta']} and {configJsonable2['beta']}.")

    timeEvoSum = timeEvo1
    if timeEvo1 != timeEvo2:
        warnings.warn(
            "Range of time evolution are different, " +
            "then keep the longer one as x-axis.")
        timeEvoSum = timeEvo1 if len(timeEvo1) > len(timeEvo2) else timeEvo2

    keyPair = list(zip(purityObject1.keys(), purityObject2.keys()))

    configSumPartial = {
        **{
            k: [config1[k], config2[k]]
            for k in config1.keys()
        },
        **{
            'beta': float(configJsonable1['beta']),
            'timeEvo': timeEvoSum
        }
    }

    purityObjectSum = {
        **purityObject1, **purityObject2,
    }
    entropyObjectSum = {
        **entropyObject1, **entropyObject2,
    }

    return purityObjectSum, entropyObjectSum, configSumPartial, keyPair


def main(
    expList: list[EntropyMeasure],
    saveFolderName: Path,
    config: dict[str],
    backend: Backend = Aer.get_backend('qasm_simulator')
) -> tuple[Optional[dict], dict[str], Figure, dict[str], Figure]:
    """The main process of measuring entropy.

    Args:
        expList (list[EntropyMeasure]): The list of experiment class 'EntropyMeasure'.
        saveFolderName (Path): The folder save the export.
        config (dict): Configuration of experiments.
        backend (Backend, optional): Qiskit backend. 
            Defaults to Aer.get_backend('qasm_simulator').

    Returns:
        tuple[Optional[dict], dict, Figure, dict, Figure]: 
            The export contains of data, purity, purityPlot, entropy, entropyPlot.
    """

    configJsonable, timeEvo, paramsCollect, paramsHint = paramsControl(
        config, expList[0]
    )
    gitignoreList = syncControl(["*.png", "*.json", "*.txt", "!*_drawOfWave"])
    None if os.path.exists(saveFolderName) else os.mkdir(saveFolderName)
    gitignoreList.export(saveFolderName)

    quickStr: callable[[tuple[int, str]], str] = (
        lambda aNum, other: f"{aNum}_{other}")
    # exp = quickStr(aNum, other)
    expListKeys = [quickStr(aNum, other) for aNum, other in paramsCollect]
    dataObject = {exp: {t: {} for t in timeEvo} for exp in expListKeys}

    for t in timeEvo:

        drawCircuit(
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
            expId = expList[t].current

            dataObject[quickStr(aNum, other)][t] = {
                "expId": expId,
                "counts": expList[t].base[expId]['counts'],
                "purity": expList[t].base[expId]['purity'],
                "entropy": expList[t].base[expId]['entropy']
            }

            drawCircuit(
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

            if config['countPlotKeep']:
                plt.clf()
                plt.figure(plot_histogram(
                    expList[t][t].base[expId]['counts'], title=f"t={t}"))
                plt.savefig(saveFolderName / (
                    f"t={t}-{expId}_dimA={quickStr(aNum, other)}_counts.png"
                ), format="png")
                plt.close()

            expList[t].reset(True)
            gc.collect()

    # exp = quickStr(aNum, other)
    purityObject = {
        exp: [dataObject[exp][t]['purity'] for t in timeEvo]
        for exp in expListKeys}
    entropyObject = {
        exp: [dataObject[exp][t]['entropy'] for t in timeEvo]
        for exp in expListKeys}

    for saveName, saveObject in [
        (saveFolderName / "all_simpleResult.json", dataObject),
        (saveFolderName / "all_config.json", configJsonable),
        (saveFolderName / "all_Purity.json", purityObject),
        (saveFolderName / "all_Entropy.json", entropyObject),
    ]:
        exportSyncJson(saveName, gitignoreList, saveObject)

    (
        purityPlotFig, purityPlotFigName,
        entropyPlotFig, entropyPlotFigName
    ) = drawTwoObject(
        purityObject=purityObject,
        entropyObject=entropyObject,
        saveFolderName=saveFolderName,
        config=config,
        timeEvo=timeEvo,
        expListKeys=expListKeys,
        # configDraw=config,
        # configForEach={},
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
