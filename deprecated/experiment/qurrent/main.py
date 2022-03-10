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
from ...qurrent import EntropyMeasure, getMeasurement
from ...tool import yLimDetector, syncControl, Configuration, jsonablize
from ..quick import drawCircuit, exportSyncJson, readJson
from .params import paramsControl, configuration


qurrentConfig = Configuration(
    name="qurrentExpConfig",
    default={
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
)


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
    
    configJsonable = jsonablize(config)
    
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
