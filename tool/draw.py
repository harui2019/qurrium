from matplotlib.figure import Figure
from matplotlib.axes import Axes, SubplotBase
import matplotlib.pyplot as plt
import matplotlib

import numpy as np
import warnings
from pathlib import Path
from math import pi
from typing import Callable, Optional, Union

from .configuration import Configuration


def yLimDetector(
    demoPlotData: dict
) -> tuple[int, int]:
    """(Deprecated)

    Args:
        demoPlotData (dict): _description_

    Returns:
        tuple[int, int]: _description_
    """

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


def yLimDecider(
    data: dict[str: list[Union[float, int]]],
) -> tuple[float, float]:
    """Give the `ylim` of the plot. (The remake of `yLimDetector`)

    Args:
        data (dict[str: list[Union[float, int]]]): Plot data.

    Returns:
        tuple[float, float]: The upper and the lower bounds of plot should be.
    """

    maxSet, minSet = [], []
    upperBound, lowerBound = 1.0, 0.0
    for listSingle in data.values():
        maxSet.append(max(listSingle))
        minSet.append(min(listSingle))
    maxMax, minMin = max(maxSet), min(minSet)
    upperBound, lowerBound = np.ceil(maxMax), np.floor(minMin)
    delta = upperBound - lowerBound
    if delta < 0:
        warnings.warn("Maximum is not larger than minimum.")
        delta = -delta

    boundAdd = np.floor(np.sqrt(delta))/2
    boundAdd = boundAdd if boundAdd > 0.1 else 0.1
    upperBound += boundAdd
    lowerBound -= boundAdd

    return lowerBound, upperBound


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
    """(Deprecated)

    Args:
        demoPlotData (dict): _description_
        demoPlotDataName (Path): _description_
        timeEvoRange (range): _description_
        beta (float): _description_
        collectANum (list): _description_
        saveFolder (Path): _description_
        drawConfig (_type_, optional): _description_. Defaults to { "fontSize": 12, "yLim": (-0.1, 1.1), "lineStyle": "--", "format": "png", "dpi": 300, }.

    Returns:
        tuple[Figure, str]: _description_
    """

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


dataConfigDefault = Configuration(
    name="dataConfig",
    default={
        "beta": 0,
        "timeEvo": None,
    },
)

drawConfigDefault = Configuration(
    name="drawConfig",
    default={
        "fontSize": 12,
        "yLim": yLimDecider,
        "lineStyle": "--",
        "format": "png",
        "dpi": 300,
    },
)


# def drawParamsControl(f: callable) -> any:
#     """Control arguments format for each drawing function.

#     Args:
#         f (callable): Drawing function.

#     Returns:
#         any: The result of drawing function.
#     """
    
#     def wrapper(
#         data: dict[str: list[Union[float, int]]],
#         plotName: str,
#         saveFolder: Optional[Path] = None,
#         dataConfig: Union[Configuration, dict] = dataConfigDefault,
#         drawConfig: Union[Configuration, dict] = drawConfigDefault,
#         **kwargs: any
#     ):
#         paramsControlArgsDoc = f"""
    
#         data (_type_): _description_
#         plotName (str): _description_
#         beta (float, optional): _description_. Defaults to 0.
#         saveFolder (Optional[Path], optional): _description_. Defaults to None.
#         dataConfig (Union[Configuration, dict], optional): _description_. Defaults to dataConfigDefault.
#         drawConfig (Union[Configuration, dict], optional): _description_. Defaults to drawConfigDefault.
        
#         """
#         docs = f.__doc__
#         if isinstance(docs, type(None)):
#             docs = """
#             Args:
#                 {paramsControlArgsDoc}
#             """.format(paramsControlArgsDoc=paramsControlArgsDoc)
#         else:
#             docs.format(paramsControlArgsDoc=paramsControlArgsDoc)
#         docs.format(paramsControlArgsDoc=paramsControlArgsDoc)
#         f.__doc__ = docs

#         return f(
#             data=data,
#             plotName=plotName,
#             saveFolder=saveFolder,
#             dataConfig=dataConfig,
#             drawConfig=drawConfig,
#             **kwargs,
#         )
#     return wrapper


def drawEntropyPlot(
    data: dict[str: list[Union[float, int]]],
    plotName: str,
    beta: float = 0,
    saveFolder: Optional[Path] = None,
    dataConfig: Union[Configuration, dict] = dataConfigDefault,
    drawConfig: Union[Configuration, dict] = drawConfigDefault,
) -> tuple[Figure, Optional[Path]]:
    """Draw the figure for entropy measuring result. (The remake of `drawResultPlot`)

    Args:
        data (_type_): _description_
        plotName (str): _description_
        beta (float, optional): _description_. Defaults to 0.
        saveFolder (Optional[Path], optional): _description_. Defaults to None.
        dataConfig (Union[Configuration, dict], optional): _description_. Defaults to dataConfigDefault.
        drawConfig (Union[Configuration, dict], optional): _description_. Defaults to drawConfigDefault.

    Returns:
        tuple[Figure, Optional[Path]]: _description_
    """

    dataConfig = dataConfigDefault.make({**dataConfig})
    dataConfig = {
        **dataConfig,
        "timeEvo": (
            range(max([len(line) for line in data.values()]))
            if dataConfig["timeEvo"] == None else dataConfig["timeEvo"]
        ),
    }
    timeEvoNum = dataConfig["timeEvo"]
    PiNumBeta = beta/pi if (beta != 0) else 1/4
    oneForthPoint = int(1/(4*PiNumBeta))

    drawConfig = drawConfigDefault.make({
        **drawConfig,
        "format": ("png" if drawConfig["format"] not in [
            "png", "jpg", "jpeg",
        ] else drawConfig["format"]),
    })
    figName = f"{plotName}.{drawConfig['format']}"

    PlotFig = plt.figure()
    ax: Union[SubplotBase, Axes] = PlotFig.add_subplot(1, 1, 1)

    ax.set_xlabel(
        f"evolution ($\Delta t = {PiNumBeta} \pi$)", size=drawConfig["fontSize"])
    ax.set_ylabel(f"{plotName}", size=drawConfig["fontSize"])

    if isinstance(drawConfig['yLim'], Callable):
        plt.ylim(drawConfig['yLim'](data))
    elif isinstance(drawConfig['yLim'], tuple):
        plt.ylim(drawConfig['yLim'])
    else:
        plt.ylim(yLimDecider(data))

    """ Vertical Line """
    if beta != 0:
        for i in np.linspace(0, timeEvoNum-1, int((timeEvoNum-1)/oneForthPoint+1)):
            if (i % oneForthPoint == 0) & (i % (oneForthPoint*2) != 0):
                plt.axvline(x=i, color='r', alpha=0.3)

    ax.set_xticks(dataConfig["timeEvo"])
    ax.set_xticklabels(
        [i if (i % 5 == 0) else None for i in dataConfig["timeEvo"]])
    ax.grid(linestyle=drawConfig["lineStyle"])

    def cutToJ(x: float) -> float: return x * (beta if beta != 0 else 1/4)
    def JToCut(x: float) -> float: return x * 1/(beta if beta != 0 else 1/4)
    secax = ax.secondary_xaxis('top', functions=(cutToJ, JToCut))
    secax.set_xlabel(f'$Jt$', size=drawConfig["fontSize"])

    for k in data:
        ax.plot(
            dataConfig["timeEvo"],
            data[k],
            marker='.',
            label="".join([f"{k}"])
        )
    legendPlt = ax.legend(
        bbox_to_anchor=(1.025, 1.0),
        loc='upper left',
        borderaxespad=0.
    )

    if isinstance(saveFolder, Path):
        saveLoc = saveFolder / figName
        PlotFig = plt.savefig(
            saveLoc,
            format=drawConfig["format"],
            dpi=drawConfig['dpi'],
            bbox_extra_artists=(legendPlt, secax,),
            bbox_inches='tight'
        )
        return PlotFig, saveLoc
    else:
        print("To export figure, use type 'Path' in 'saveFolder'.")
        return PlotFig, None


def drawEntropyErrorBar(
    data: dict[str: list[Union[float, int]]],
    plotName: str,
    saveFolder: Optional[Path] = None,
    dataConfig: Union[Configuration, dict] = dataConfigDefault,
    drawConfig: Union[Configuration, dict] = drawConfigDefault,
) -> tuple[Figure, Optional[Path]]:
    """Draw the figure for entropy measuring result. (The remake of `drawResultPlot`)

    Args:
        data (_type_): _description_
        plotName (str): _description_
        beta (float, optional): _description_. Defaults to 0.
        saveFolder (Optional[Path], optional): _description_. Defaults to None.
        dataConfig (Union[Configuration, dict], optional): _description_. Defaults to dataConfigDefault.
        drawConfig (Union[Configuration, dict], optional): _description_. Defaults to drawConfigDefault.

    Returns:
        tuple[Figure, Optional[Path]]: _description_
    """

    dataConfig = dataConfigDefault.make({**dataConfig})
    dataConfig = {
        **dataConfig,
    }

    drawConfig = drawConfigDefault.make({
        **drawConfig,
        "format": ("png" if drawConfig["format"] not in [
            "png", "jpg", "jpeg",
        ] else drawConfig["format"]),
    })
    figName = f"{plotName}.{drawConfig['format']}"

    PlotFig: Figure = plt.figure()
    ax: Axes = PlotFig.add_subplot(1, 1, 1)

    ax.set_xlabel(
        f"ErrorBar of Experiments", size=drawConfig["fontSize"])
    ax.set_ylabel(f"{plotName}", size=drawConfig["fontSize"])

    if isinstance(drawConfig['yLim'], Callable):
        plt.ylim(drawConfig['yLim'](data))
    elif isinstance(drawConfig['yLim'], tuple):
        plt.ylim(drawConfig['yLim'])
    else:
        plt.ylim(yLimDecider(data))

    plt.xlim((0, 2*(len(data)+1)))
    ax.set_xticks([2*i for i in range(len(data)+2)])
    ax.set_xticklabels(
        [None]+[k for k in data]+[None],
        rotation=30,
    )
    ax.grid(linestyle=drawConfig["lineStyle"])

    dataKeys = list(data.keys())
    for i in range(len(data)):
        k = dataKeys[i]
        ax.errorbar(
            [2*(i+1)],
            [np.mean(data[k])],
            [np.std(data[k])],
            capsize=10,
            linewidth=2,
            elinewidth=2,
            marker='.',
            label="".join([f"{k}"])
        )
        ax.scatter(
            [2*(i+1) for v in data[k]],
            data[k],
            marker='x',
            label="".join([f"{k}"])
        )

    h, l = ax.get_legend_handles_labels()
    legendPlt = ax.legend(
        handles=zip(h[:len(data)], h[len(data):]),
        handler_map={tuple: matplotlib.legend_handler.HandlerTuple(None)},
        labels=l[:len(data)],
        bbox_to_anchor=(1.025, 1.0),
        loc='upper left',
        borderaxespad=0.,
    )

    if isinstance(saveFolder, Path):
        saveLoc = saveFolder / figName
        PlotFig = plt.savefig(
            saveLoc,
            format=drawConfig["format"],
            dpi=drawConfig['dpi'],
            bbox_extra_artists=(legendPlt, ),
            bbox_inches='tight'
        )
        return PlotFig, saveLoc
    else:
        print("To export figure, use type 'Path' in 'saveFolder'.")
        return PlotFig, None


def drawEntropyErrorPlot(
    data: dict[str: list[Union[float, int]]],
    plotName: str,
    saveFolder: Optional[Path] = None,
    dataConfig: Union[Configuration, dict] = dataConfigDefault,
    drawConfig: Union[Configuration, dict] = drawConfigDefault,
) -> tuple[Figure, Optional[Path]]:
    """Draw the figure for entropy measuring result. (The remake of `drawResultPlot`)

    - Example:

    ```
    dummyData =  {str(i).rjust(2, '0'): {
        10:[3,4], # the output of the entropy of experiment when random unitary is 10.
        20:[4,7],
        40:[5,10],
        80:[6,13]
    } for i in range(6)}
    ```

    Args:
        data (_type_): _description_
        plotName (str): _description_
        beta (float, optional): _description_. Defaults to 0.
        saveFolder (Optional[Path], optional): _description_. Defaults to None.
        dataConfig (Union[Configuration, dict], optional): _description_. Defaults to dataConfigDefault.
        drawConfig (Union[Configuration, dict], optional): _description_. Defaults to drawConfigDefault.

    Returns:
        tuple[Figure, Optional[Path]]: _description_
    """

    dataConfig = dataConfigDefault.make({**dataConfig})
    dataConfig = {
        **dataConfig,
    }

    drawConfig = drawConfigDefault.make({
        **drawConfig,
        "format": ("png" if drawConfig["format"] not in [
            "png", "jpg", "jpeg",
        ] else drawConfig["format"]),
    })
    figName = f"{plotName}.{drawConfig['format']}"

    PlotFig: Figure = plt.figure()
    ax: Axes = PlotFig.add_subplot(1, 1, 1)

    ax.set_xlabel(
        f"ErrorBar of Experiments", size=drawConfig["fontSize"])
    ax.set_ylabel(f"{plotName}", size=drawConfig["fontSize"])

    numUnitarySet = [sorted([k for k in data[kData]]) for kData in data]
    numUnitaryKey = {}
    for nums in numUnitarySet:
        numUnitaryKey = {
            **numUnitaryKey,
            **dict.fromkeys(nums, None),
        }
    numUnitaryKey = sorted([k for k in numUnitaryKey])
    print(numUnitaryKey)

    plt.xlim(-0.5, len(numUnitaryKey)-0.5)
    ax.set_xticks(range(len(numUnitaryKey)))
    ax.set_xticklabels(numUnitaryKey)
    ax.grid(linestyle=drawConfig["lineStyle"])

    for kData in data:
        d = data[kData]
        ax.plot(
            [i for i in range(len(d))],
            [np.std(vset) for vset in d.values()],
            marker='.',
            label="".join([f"{kData}"])
        )
        ax.scatter(
            [i for i in range(len(d))],
            [np.std(vset) for vset in d.values()],
            marker='x',
            alpha=0.5,
            label="".join([f"{kData}"])
        )

    h, l = ax.get_legend_handles_labels()
    legendPlt = ax.legend(
        handles=zip(h[:len(data)], h[len(data):]),
        handler_map={tuple: matplotlib.legend_handler.HandlerTuple(None)},
        labels=l[:len(data)],
        bbox_to_anchor=(1.025, 1.0),
        loc='upper left',
        borderaxespad=0.,
    )

    if isinstance(saveFolder, Path):
        saveLoc = saveFolder / figName
        PlotFig = plt.savefig(
            saveLoc,
            format=drawConfig["format"],
            dpi=drawConfig['dpi'],
            bbox_extra_artists=(legendPlt, ),
            bbox_inches='tight'
        )
        return PlotFig, saveLoc
    else:
        print("To export figure, use type 'Path' in 'saveFolder'.")
        return PlotFig, None


def drawPurityErrorAnalysis(
    data: dict[str: list[Union[float, int]]],
    plotName: str,
    saveFolder: Optional[Path] = None,
    dataConfig: Union[Configuration, dict] = dataConfigDefault,
    drawConfig: Union[Configuration, dict] = drawConfigDefault,
) -> tuple[Figure, Optional[Path]]:
    """Draw the figure for entropy measuring result. (The remake of `drawResultPlot`)

    - Example:

    ```
    dummyData =  {str(i).rjust(2, '0'): {
        10:[3,4], # the output of the entropy of experiment when random unitary is 10.
        20:[4,7],
        40:5,
        80:[6,13],
        'expected': 0,
    } for i in range(6)}
    ```

    Args:
        data (_type_): _description_
        plotName (str): _description_
        beta (float, optional): _description_. Defaults to 0.
        saveFolder (Optional[Path], optional): _description_. Defaults to None.
        dataConfig (Union[Configuration, dict], optional): _description_. Defaults to dataConfigDefault.
        drawConfig (Union[Configuration, dict], optional): _description_. Defaults to drawConfigDefault.

    Returns:
        tuple[Figure, Optional[Path]]: _description_
    """

    dataConfig = dataConfigDefault.make({**dataConfig})
    dataConfig = {
        **dataConfig,
    }

    drawConfig = drawConfigDefault.make({
        **drawConfig,
        "format": ("png" if drawConfig["format"] not in [
            "png", "jpg", "jpeg",
        ] else drawConfig["format"]),
    })
    figName = f"{plotName}.{drawConfig['format']}"

    fig, axes = plt.subplots()
    fig: Figure
    axes01: Union[SubplotBase, Axes] = axes

    figTitle = fig.suptitle(f"{plotName}", y=1, size=drawConfig["fontSize"]+2)
    axes01.set_xlabel("$\log_{2}{N_U}$", size=drawConfig["fontSize"])
    axes01.set_ylabel(
        "$\log_{2}{|| {Tr}({\\rho_A}^2)_e - {Tr}({\\rho_A}^2)_t ||}$",
        size=drawConfig["fontSize"]
    )
    axes01.set_title(f"Purity error analysis", size=drawConfig["fontSize"])

    dataClone = {**data}
    for wave in data:
        if 'expected' not in data[wave]:
            raise ValueError("Each wave must have a expected purity number.")
        else:
            if not isinstance(data[wave]['expected'], (int, float)):
                raise TypeError("'expected' should be int or float.")

        for numU in data[wave]:
            if numU == 'expected':
                pass
            elif isinstance(numU, int):
                pass
            elif isinstance(numU, str):
                if not numU.isdigit():
                    raise ValueError(f"In '{wave}', '{numU}' is not a number.")
            else:
                raise ValueError(f"In '{wave}', '{numU}' is not a number.")

    numUnitarySet = [sorted([
        int(numU) for numU in dataClone[wave] if numU != 'expected'
    ]) for wave in dataClone]
    numUnitaryKey = {}
    for nums in numUnitarySet:
        numUnitaryKey = {
            **numUnitaryKey,
            **dict.fromkeys(nums, None),
        }
    numUnitaryKeyNu = sorted([k for k in numUnitaryKey])
    numUnitaryKey = sorted([np.log2(int(k)) for k in numUnitaryKey])

    def TOlog2(x): return np.log2(x)
    def ReverseTOlog2(x): return 2**x

    secax_x = axes01.secondary_xaxis(
        -0.2, functions=(ReverseTOlog2, TOlog2))
    secax_x.set_xlabel(r'$N_U$', size=drawConfig["fontSize"])
    secax_x.set_xticks(numUnitaryKeyNu)
    secax_x.set_xticklabels(numUnitaryKeyNu)

    axes01.grid(linestyle=drawConfig["lineStyle"])

    for wave in dataClone:
        d = dataClone[wave]
        expected = d['expected']
        del d['expected']
        errorSet = [
            np.log2(np.linalg.norm(np.mean(vset) - expected))
            for vset in d.values()]
        axes01.plot(
            numUnitaryKey,
            errorSet,
            marker='.',
            label="".join([f"{wave}"])
        )

    legendPlt = axes.legend(
        bbox_to_anchor=(1.025, 1.0),
        loc='upper left',
        borderaxespad=0.
    )

    if isinstance(saveFolder, Path):
        saveLoc = saveFolder / figName
        fig = plt.savefig(
            saveLoc,
            format=drawConfig["format"],
            dpi=drawConfig['dpi'],
            bbox_extra_artists=(legendPlt, secax_x, figTitle, ),
            bbox_inches='tight'
        )
        return fig, saveLoc
    else:
        return fig, None
