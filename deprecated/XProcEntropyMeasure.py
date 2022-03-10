from qiskit import IBMQ, Aer, BasicAer
from qiskit.visualization import *
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import json
import os
import numpy as np
from pathlib import Path
from math import pi
from typing import Union, Optional, List, Callable, Any, Iterable
from .XProcUniversal import *
from .entropyMeasure import EntropyMeasure

handleCollectAList: Callable[[List[Union[List[int], int]]], List[int]] = (
    lambda tgt: [(
        [int(a) for a in aItem] if type(aItem) == list else int(aItem)
    ) for aItem in tgt]
)


def handleCollectAList(
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


def spreadCollectA(
    collect: Iterable
) -> tuple[List[int], List[List[int]]]:
    return (
        [aItem[0] for aItem in collect],
        {aItem[0]: aItem[1:] for aItem in collect}
    )


def processDrawTwoSiteSOC(
    demoPurityPlotData: dict,
    demoEntropyPlotData: dict,
    demoFolderName: Path,
    demoConfig: dict
) -> tuple[Figure, str, Figure, str]:

    configKeyCheck(demoConfig)

    timeEvo = typeCheck(
        demoConfig['timeEvo'],
        [(int, range), (range, None)]
    )
    collectA = typeCheck(
        demoConfig['collectA'],
        [(int, range), (range, None), (list, handleCollectAList)]
    )
    collectANum, collectAOther = spreadCollectA(collectA)
    AllKeys = [ f"{a}" for a in collectA ]

    demoPurityPlotFig, demoPurityFigName = drawResultPlot(
        demoPlotData=demoPurityPlotData,
        demoPlotDataName='Purity',
        timeEvoRange=timeEvo,
        beta=demoConfig['beta'],
        collectANum=AllKeys,
        saveFolder=demoFolderName,
        # collectAOther=collectAOther,
        drawConfig={
            "fontSize": 12,
            "yLim": yLimDetector(demoPurityPlotData),
            "lineStyle": "--",
            "format": "png",
            "dpi": 300,
        }
    )

    demoEntropyPlotFig, demoEntropyFigName = drawResultPlot(
        demoPlotData=demoEntropyPlotData,
        demoPlotDataName='Entropy',
        timeEvoRange=timeEvo,
        beta=demoConfig['beta'],
        collectANum=AllKeys,
        saveFolder=demoFolderName,
        # collectAOther=collectAOther,
        drawConfig={
            "fontSize": 12,
            "yLim": None,
            "lineStyle": "--",
            "format": "png",
            "dpi": 300,
        }
    )

    return (
        demoPurityPlotFig, demoPurityFigName,
        demoEntropyPlotFig, demoEntropyFigName
    )


def processTwoSiteSOC(
    demoTestSet: EntropyMeasure,
    demoFolderName: Path,
    demoDataSet: dict,
    demoConfig: dict,
    backend=Aer.get_backend('qasm_simulator')
) -> tuple[dict[str], dict, Figure, dict, Figure]:

    demoConfigKeys = configKeyCheck(demoConfig)
    timeEvo = typeCheck(
        demoConfig['timeEvo'],
        [(int, range), (range, None)]
    )
    collectA = typeCheck(
        demoConfig['collectA'],
        [(int, range), (range, None), (list, handleCollectAList)]
    )
    collectANum, collectAOther = spreadCollectA(collectA)
    demoConfigStr = {k: str(demoConfig[k]) for k in demoConfigKeys}

    syncList = []
    syncControl: Callable[[bool, str], None] = (
        lambda isSync, fileName: syncList.append(
            Path(fileName).name) if isSync else None
    )

    None if os.path.exists(demoFolderName) else os.mkdir(demoFolderName)
    
    AllKeys = { f"{a}": {t: [] for t in timeEvo} for a in collectA }
    demoDataSet = { t:{} for t in timeEvo }
    for t in timeEvo:
        if demoConfig['waveFigType'] == 'text':
            with open(
                demoFolderName / f"t={t}_drawOfWave.txt", 'w', encoding='utf-8'
            ) as waveCircuit:
                print(demoTestSet[t].drawOfWave(
                    figType=demoConfig['waveFigType'],
                    composeMethod=demoConfig['waveComposeMethod']
                ), file=waveCircuit)
        else:
            plt.clf()
            plt.figure(demoTestSet[t].drawOfWave(
                figType=demoConfig['waveFigType'],
                composeMethod=demoConfig['waveComposeMethod']
            ), title=f"wave function t={t}")
            plt.savefig(demoFolderName / f"t={t}_drawOfWave.png", format="png")
            plt.close()

        for a in collectA:
            demoTestSet[t].go(
                params=a,
                runBy=demoConfig['goRunby'],
                figType=demoConfig['goFigType'],
                composeMethod=demoConfig['goComposeMethod'],
                shots=demoConfig['shots'],
                backend=backend
            )

            keyList = demoTestSet[t].base.keys()
            
            AllKeys[f"{a}"][t] = list(keyList)[collectA.index(a)]
            for expId in keyList:

                if demoConfig['goFigType'] == 'text':
                    with open(
                        demoFolderName / ("".join([
                            f"t={t}-dimA={expId}", *
                            [f"-{i}" for i in collectAOther[a[0]]]
                        ])+"_drawCircuit.txt"), 'w', encoding='utf-8'
                    ) as goCircuit:
                        print(demoTestSet[t].base[expId]['fig'], file=goCircuit)
                else:
                    plt.clf()
                    plt.figure(
                        demoTestSet[t].base[expId]['fig'], title=f"wave function t={t}"
                    )
                    plt.savefig(
                        demoFolderName / (f"t={t}-dimA={expId}_".join([
                            f"-{i}" for i in collectAOther[a[0]]
                        ])+"drawCircuit.png"), format="png"
                    )
                    plt.close()

                demoDataSet[t][expId] = {
                    "counts": demoTestSet[t].base[expId]['counts'],
                    "purity": demoTestSet[t].base[expId]['purity'],
                    "entropy": demoTestSet[t].base[expId]['entropy']
                }

                if demoConfig['singleResultKeep']:
                    with open(
                        demoFolderName / ("".join([
                            f"t={t}-dimA={expId}", *
                            [f"-{i}" for i in collectAOther[a[0]]]
                        ])+"_simpleResult.json"), 'w', encoding='utf-8'
                    ) as simpleResult:
                        json.dump(
                            demoDataSet[expId][t], simpleResult, indent=2, ensure_ascii=False
                        )

                plt.clf()
                plt.figure(plot_histogram(
                    demoTestSet[t].base[expId]['counts'], title=f"t={t}"))
                if demoConfig['countPlotKeep']:
                    plt.savefig(
                        demoFolderName / ("".join([
                            f"t={t}-dimA={expId}", *
                            [f"-{i}" for i in collectAOther[a[0]]]
                        ])+"_counts.png"), format="png"
                    )
                plt.close()

    print(AllKeys)
    [ print(demoDataSet[t].keys()) for t in timeEvo ]
    
    """
    {
        klist: [
            print([AllKeys[klist][t], t, klist, demoDataSet[t][str(AllKeys[klist][t])]])
        for t in timeEvo] 
    for klist in AllKeys.keys() }
    
    demoPurityPlotData = {
        klist: [
            demoDataSet[t][AllKeys[klist][t]]['purity']
        for t in timeEvo] 
    for klist in AllKeys.keys() }
    
    demoEntropyPlotData = {
        klist: [
            demoDataSet[t][AllKeys[klist][t]]['entropy']
        for t in timeEvo] 
    for klist in AllKeys.keys() }
    """
    
    for klist in AllKeys.keys():
        for t in timeEvo: 
            tmpK = AllKeys[klist][t]
            print(demoDataSet[t].keys(), tmpK, klist, t)
            print(tmpK in demoDataSet[t].keys())
    
    demoPurityPlotData = {}
    for klist in AllKeys.keys():
        demoPurityPlotData[klist] = []
        for t in timeEvo: 
            tmpK = AllKeys[klist][t]
            demoPurityPlotData[klist].append(demoDataSet[t][tmpK]['purity'])
                
    demoEntropyPlotData = {}
    for klist in AllKeys.keys():
        demoEntropyPlotData[klist] = []
        for t in timeEvo: 
            tmpK = AllKeys[klist][t]
            demoEntropyPlotData[klist].append(demoDataSet[t][tmpK]['entropy'])
    


    with open(
        demoFolderName / f"all_simpleResult.json", 'w', encoding='utf-8'
    ) as simpleResult:
        syncControl(True, simpleResult.name)
        json.dump(demoDataSet, simpleResult, indent=2, ensure_ascii=False)

    with open(
        demoFolderName / f"all_config.json", 'w', encoding='utf-8'
    ) as config:
        syncControl(True, config.name)
        json.dump(demoConfigStr, config, indent=2, ensure_ascii=False)

    with open(
        demoFolderName / f"all_Purity.json", 'w', encoding='utf-8'
    ) as demoPurity:
        syncControl(True, demoPurity.name)
        json.dump(demoPurityPlotData, demoPurity, indent=2, ensure_ascii=False)

    with open(
        demoFolderName / f"all_Entropy.json", 'w', encoding='utf-8'
    ) as demoEntropy:
        syncControl(True, demoEntropy.name)
        json.dump(demoEntropyPlotData, demoEntropy,
                  indent=2, ensure_ascii=False)

    (
        demoPurityPlotFig,
        demoPurityFigName,
        demoEntropyPlotFig,
        demoEntropyFigName
    ) = processDrawTwoSiteSOC(
        demoPurityPlotData,
        demoEntropyPlotData,
        demoFolderName,
        demoConfig
    )

    syncControl(True, demoPurityFigName)
    syncControl(True, demoEntropyFigName)

    with open(
        demoFolderName / f".gitignore", 'w', encoding='utf-8'
    ) as ignoreList:
        print("*.png", file=ignoreList)
        print("*.json", file=ignoreList)
        print("*.txt", file=ignoreList)
        [print(f"!{fileName}", file=ignoreList) for fileName in syncList]

    return (
        demoDataSet, demoPurityPlotData, demoPurityPlotFig,
        demoEntropyPlotData, demoEntropyPlotFig
    )


def readTwoSiteSOCJson(
    demoFolderName: Path
) -> tuple[dict[str], dict[str], dict, dict]:
    demoDataSet = {}
    demoConfig = {}
    demoPurityPlotData = {}
    demoEntropyPlotData = {}

    with open(
        demoFolderName / f"all_simpleResult.json", 'r', encoding='utf-8'
    ) as simpleResult:
        demoDataSet = (json.load(simpleResult))

    with open(
        demoFolderName / f"all_config.json", 'r', encoding='utf-8'
    ) as config:
        demoConfig = (json.load(config))

    with open(
        demoFolderName / f"all_Purity.json", 'r', encoding='utf-8'
    ) as demoPurity:
        demoPurityPlotData = (json.load(demoPurity))

    with open(
        demoFolderName / f"all_Entropy.json", 'r', encoding='utf-8'
    ) as demoEntropy:
        demoEntropyPlotData = (json.load(demoEntropy))

    return (
        demoDataSet, demoPurityPlotData, demoEntropyPlotData, demoConfig
    )
