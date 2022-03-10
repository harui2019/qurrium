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


def makeTwoBitStr(num: int, bits: List[str] = ['']) -> List[str]:
    return ((lambda bits: [
        *['0'+item for item in bits], *['1'+item for item in bits]
    ])(makeTwoBitStr(num-1, bits)) if num > 0 else bits)


makeTwoBitStrOneLiner: Callable[[int, List[str]], List[str]] = (
    lambda num, bits=['']: ((lambda bits: [
        *['0'+item for item in bits], *['1'+item for item in bits]]
    )(makeTwoBitStrOneLiner(num-1, bits)) if num > 0 else bits))


def universal_cmd(
    cmd: str = ""
) -> None:
    try:
        from IPython import get_ipython
        get_ipython().system(cmd)
    except:
        os.system(cmd)


def pytorchCUDACheck() -> None:
    try:
        import torch
        print(" - Torch CUDA available --------- %s" %
              (torch.cuda.is_available()))
        print(">>> Using torch %s %s" % (
            torch.__version__,
            torch.cuda.get_device_properties(
                0) if torch.cuda.is_available() else 'CPU'
        ))
    except ImportError as e:
        print(
            e, "This checking method requires pytorch" +
            " which has been installed in this enviornment."
        )


def typeCheck(
    target: any,
    typeWantAndHandle: list[tuple[type, Union[type, Callable]]]
) -> Exception:
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


def configKeyCheck(
    target: dict,
    keyCheck: List[str] = [
        'qPairNum', 'boundaryCond', 'alpha', 'beta',
        'circuitRunBy', 'initSet', 'hamiltonianIndex', 'timeEvo',
        'collectA', 'waveFigType', 'waveComposeMethod',
        'goRunby', 'goFigType', 'goComposeMethod',
        'shots', 'singleResultKeep', 'countPlotKeep'
    ]
) -> list:
    targetKeys = list(target.keys())
    for k in keyCheck:
        if not k in targetKeys:
            print(target)
            raise KeyError(
                f"{k}' is lost in Configuration, make sure it has been configured.")
    return targetKeys


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


def drawResultPlot(
    demoPlotData: dict,
    demoPlotDataName: Path,
    timeEvoRange: range,
    beta: float,
    collectANum: list,
    saveFolder: Path,
    # collectAOther: dict,
    drawConfig: dict = {
        "fontSize": 12,
        "yLim": (-0.1, 1.1),
        "lineStyle": "--",
        "format": "png",
        "dpi": 300,
    }
) -> tuple[Figure, str]:

    demoPlotFigName = f"all_{demoPlotDataName}.{drawConfig['format']}"
    timeEvoNum = len(timeEvoRange)
    betaPiNum = ((beta/pi) if beta != 0 else 1/4)
    piFourthIden = int(1/(4*betaPiNum))

    demoPlotFig = plt.figure()
    ax = demoPlotFig.add_subplot(1, 1, 1)

    ax.set_xlabel(
        f'evolution ($\Delta t = {beta/pi} \pi$)', size=drawConfig["fontSize"])
    ax.set_ylabel(f'{demoPlotDataName}', size=drawConfig["fontSize"])

    (plt.ylim(drawConfig['yLim']) if bool(drawConfig['yLim']) else None)
    if beta != 0:
        [plt.axvline(x=i, color='r', alpha=0.3) for i in np.linspace(
            0, timeEvoNum - 1, int((timeEvoNum - 1)/piFourthIden + 1)
        ) if (
            (i % piFourthIden == 0) and (i % (piFourthIden*2) != 0)
        )]

    ax.set_xticks(timeEvoRange)
    ax.set_xticklabels(
        [i if (i % 5 == 0) else None for i in timeEvoRange])
    ax.grid(linestyle=drawConfig["lineStyle"])

    cutToJ: Callable[[float], float] = (
        lambda x: x * (beta if beta != 0 else 1/4))
    JToCut: Callable[[float], float] = (
        lambda x: x * 1/(beta if beta != 0 else 1/4))

    secax = ax.secondary_xaxis('top', functions=(cutToJ, JToCut))
    secax.set_xlabel(f'$Jt$', size=drawConfig["fontSize"])

    print(
        "The following numbers are the result at specific number of subsystem A",
        collectANum
    )

    for aNum in collectANum:
        ax.plot(
            timeEvoRange, demoPlotData[aNum], marker='.',
            label="".join([
                f"a={aNum}"
                # , *[f"/{i}" for i in collectAOther[aNum]]
            ])
        )
    legendPlt = ax.legend(
        bbox_to_anchor=(1.025, 1.0),
        loc='upper left',
        borderaxespad=0.)
    demoPlotFig = plt.savefig(
        saveFolder / demoPlotFigName,
        format=drawConfig["format"],
        dpi=drawConfig['dpi'],
        bbox_extra_artists=(legendPlt, secax,),
        bbox_inches='tight'
    )
    return demoPlotFig, demoPlotFigName
