from matplotlib.figure import Figure
from matplotlib.axes import Axes, SubplotBase
import matplotlib.pyplot as plt
import matplotlib

import numpy as np
import warnings
import os
from pathlib import Path
from math import pi
from typing import Callable, Optional, Union, NamedTuple, overload

from ..tool import argdict
from .widget import *


class QurryplotV1:
    """QurryplotV1 will be pointed to migrate old code and function in draw.py

    Returns:
        _type_: _description_
    """
    class argdictQurryPlot(NamedTuple):
        yLim: Union[callable, tuple[float, int], None] = None
        fontSize: int = 12
        lineStyle: str = '--'
        format: str = 'png'
        dpi: int = 300

        quantity: str = 'entropy'

        plotType: str = '_dummy'
        plotName: str = 'Qurryplot'
        filename: Path = Path('./')
        saveFolder: Union[Path, str] = './'

    QuantityType = Union[float, dict[float]]
    DataUnit = dict[list[QuantityType]]
    InputType = Union[DataUnit, list[DataUnit], dict[DataUnit]]

    def expsConfig(
        self,
        name: str = 'qurryConfig',
        defaultArg: dict[any] = {
            **argdictQurryPlot()._asdict()
        },
    ) -> Configuration:
        """The default format and value for executing a single experiment.
        - Example:

        ```
        {
            # Variants of experiment.
            **defaultArg,

            yLim: yLimDecider,
            fontSize: 12,
            lineStyle: '--',
            foramt: 'png',
            dpi: 300,

            quantity: 'entropy',

            plotType: '_dummy',
            plotName: 'Qurryplot',
            filename: Path('./'),
            saveFolder: './',
        }
        ```

        Args:
            name (str, optional):
                Name of basic configuration for `Qurry`.
                Defaults to 'qurryConfig'.
            defaultArg (dict[any], optional):
                Basic input for `.output`.
                Defaults to { 'wave': None }.

        Returns:
            Configuration: _description_
        """
        return Configuration(
            name=name,
            default={
                **self.argdictNow()._asdict(),
                # Variants of experiment.
                **defaultArg,
            },
        )

    def drawConfigControls(
        self,
        # matplotlib configuration
        yLim: Union[callable, tuple[float, int], None] = None,
        fontSize: int = 12,
        lineStyle: str = '--',
        format: str = 'png',
        dpi: int = 300,
        # quantity name
        quantity: str = 'entropy',
        # exportation configureation
        plotType: str = '_dummy',
        plotName: str = 'Qurryplot',
        saveFolder: Union[Path, str] = './',

        **otherArgs: any,
    ) -> argdictQurryPlot:
        """_summary_

        Args:
            yLim (Union[callable, tuple[float, int]], optional): _description_. Defaults to yLimDecider.
            fontSize (int, optional): _description_. Defaults to 12.
            lineStyle (str, optional): _description_. Defaults to '--'.
            foramt (str, optional): _description_. Defaults to 'png'.
            dpi (int, optional): _description_. Defaults to 300.
            plotType (str, optional): _description_. Defaults to '_dummy'.
            plotName (str, optional): _description_. Defaults to 'Qurryplot'.

        Returns:
            argdict: _description_
        """

        # format
        format = ("png" if format not in ["png", "jpg", "jpeg"] else format)

        # figName
        figName = f"{plotName}.{plotType}"
        fileName = f"{plotName}.{quantity}.{plotType}.{format}"

        # saveFolder
        if isinstance(saveFolder, (str, Path)):
            saveFolder = Path(saveFolder)
        else:
            warnings.warn(
                f"'{saveFolder}' is seems to be not a 'str' or 'Path'" +
                ", use default location './'.")
            saveFolder = Path('./')

        if not os.path.exists(saveFolder):
            os.makedirs(saveFolder)

        args = argdict(
            params={
                'yLim': yLim,
                'fontSize': fontSize,
                'lineStyle': lineStyle,
                'format': format,
                'dpi': dpi,

                'quantity': quantity,

                'plotType': plotType,
                'plotName': plotName,
                'figName': figName,
                'fileName': fileName,
                'saveFolder': saveFolder,

                **otherArgs
            },
        )
        return args

    def __init__(
        self,
        data: InputType,
        plotName: str = 'Qurryplot',
        saveFolder: Union[Path, str] = './',
        **otherArgs: any,
    ) -> None:
        """_summary_

        Args:
            data (dict[list[Union[float, int]]]): _description_

            - data input format

            ```

            {
                'trivialPM_4': [...],
                'cat_4': [...],
                'topPMPeriod_4': [...],
                'topPMOpen_4': [...],
                ...
            }
            ```

            plotName (str, optional): _description_. 
                Defaults to 'Qurryplot'.
            saveFolder (Optional[Path], optional): _description_. 
                Defaults to None.

        """
        self.fulldata = data
        self.data = {
            k: self.fulldata[k] for k in self.fulldata
            if k not in ['all', 'noTags']}

        self.plotName = plotName
        self.saveFolder = saveFolder

    def demoUnit(
        self,
        plt: plt,
        grid: tuple[int, int],
        position: tuple[int, int],

        **otherArgs: any,
    ) -> plt:
        ax: Axes = plt.subplot2grid(grid, position, colspan=1, rowspan=1)

        t = np.linspace(0.0, 1.0, 50)
        s = np.cos(4 * np.pi * t) + 2
        for i in range(10):
            ax.plot(t, s+i*1, marker='.', label=f"i={i}")

        ax.grid(linestyle='--')
        ax.set_xlabel(r'\textbf{time (s)}')
        ax.set_ylabel(
            "$\\log_{2}{\\frac{1}{n} \\ \\sum_{t=0}^{n} | [{Tr}({\\rho_A}^2)]_e - [{Tr}({\\rho_A}^2)]_t | }$", fontsize=16)
        ax.set_title(
            r'\TeX\ is Number $\sum_{n=1}^\infty\frac{-e^{i\pi}}{2^n}$!', fontsize=16)

        legendPlt = ax.legend(
            bbox_to_anchor=(1.025, 1.0),
            loc='upper left',
            borderaxespad=0.)

        return plt

    def errorBarUnit(
        self,
        plt: plt,
        grid: tuple[int, int],
        position: tuple[int, int],

        data: DataUnit,
        dataTag: str,
        quantity: str = 'entropy',

        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        xsticklabel: Optional[list[any]] = None,

        **otherArgs: any,
    ) -> plt:
        """_summary_

        Returns:
            tuple[Figure, Optional[Path]]: _description_
        """
        args = self.drawConfigControls(
            plotType='errorBar',
            plotName=self.plotName,
            saveFolder=self.saveFolder,
            quantity=quantity,
            **otherArgs
        )
        ax: Axes = plt.subplot2grid(grid, position, colspan=1, rowspan=1)

        ax.set_ylabel(
            f"ErrorBar of Experiments" if ylabel is None else ylabel,
            size=args.fontSize
        )
        ax.set_xlabel(
            f"ErrorBar of {dataTag}" if xlabel is None else xlabel,
            size=args.fontSize
        )

        ax.set_xlim(0, 2*(len(data)+1))
        if args.yLim:
            ax.set_ylim(args.yLim)
        length = len(data)

        # label
        # ax.set_xlabel(
        #     f"ErrorBar of Experiments", size=args.fontSize)
        # ax.set_ylabel(f"{args.plotName}", size=args.fontSize)
        ax.set_title(dataTag, size=args.fontSize)

        # xstick
        ax.set_xticks([2*i for i in range(length+2)])
        if xsticklabel is None:
            ax.set_xticklabels(
                [None]+[self.stickLabelGiver(k) for k in data]+[None])
        else:
            tmp = [self.stickLabelGiver(k) for k in data]
            for i in range(len(xsticklabel)):
                tmp[i] = xsticklabel[i]
            ax.set_xticklabels([None]+tmp+[None])
        ax.grid(linestyle=args.lineStyle)

        # draw
        dataKeys = list(data.keys())
        for i in range(length):
            k = dataKeys[i]
            dataAtK = [
                self.valueGetter(quantityContainer, args.quantity)
                for quantityContainer in data[k]
                if self.valueGetter(quantityContainer, args.quantity) != None]
            ax.errorbar(
                [2*(i+1)],
                [np.mean(dataAtK)],
                [np.std(dataAtK)],
                capsize=10,
                linewidth=2,
                elinewidth=2,
                marker='.',
                label="".join([f"{k}"])
            )
            ax.scatter(
                [2*(i+1) for v in dataAtK],
                dataAtK,
                marker='x',
                label="".join([f"{k}"])
            )
            
        if quantity == 'magnetsq' and all([isinstance(k, int) for k in dataKeys]):
            if dataTag == 'cat':
                ax.plot(
                    [2*(i+1) for i in range(length)],
                    [1 for v in dataKeys],
                    label="$1$",
                )
            else:
                ax.plot(
                    [2*(i+1) for i in range(length)],
                    [1/v for v in dataKeys],
                    label="$1/N$",
                    marker='.',
                )

        # legend
        h, l = ax.get_legend_handles_labels()
        if quantity == 'magnetsq' and all([isinstance(k, int) for k in dataKeys]):
            handlesZip = [h[0]]+list(zip(h[1:length+1], h[length+1:]))
            labels = l[:length+1]
        else:
            handlesZip = zip(h[:length], h[length:])
            labels = l[:length]
        legendPlt = ax.legend(
            handles=handlesZip,
            handler_map={tuple: matplotlib.legend_handler.HandlerTuple(None)},
            labels=labels,
            bbox_to_anchor=(1.025, 1.0),
            loc='upper left',
            borderaxespad=0.,
        )

        return plt

    def errorBar(
        self,
        quantity: str = 'entropy',
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        xsticklabel: Optional[list[any]] = None,
        **otherArgs: any,
    ) -> tuple[Figure, Optional[Path]]:
        """_summary_

        Returns:
            tuple[Figure, Optional[Path]]: _description_
        """
        args = self.drawConfigControls(
            plotType='multi.errorBar',
            plotName=self.plotName,
            saveFolder=self.saveFolder,
            quantity=quantity,
            **otherArgs
        )

        dataObj: dict[self.DataUnit] = {}
        if isinstance(self.data, list):
            dataObj = {k: self.data[k] for k in range(len(self.data))}
        elif isinstance(self.data, dict):
            dataObj = self.data
        else:
            warnings.warn("Unavailable input type.")

        length = len(dataObj)
        gridSize = int(np.sqrt(length))
        gridShape = (gridSize, gridSize)

        dataUnitSize = max([len(dataObj[k]) for k in dataObj])

        plt.figure(
            figsize=(gridShape[0]*(dataUnitSize*0.4 + 2.8), gridShape[1]*3))
        plt.suptitle(f'{self.plotName}.errorBar', fontsize=args.fontSize)

        dataKeysArray = list(dataObj.keys())
        positionArray = [
            (i, j)
            for i in range(gridSize)
            for j in range(gridSize)]

        for k in dataObj:
            self.errorBarUnit(
                plt=plt,
                grid=gridShape,
                position=positionArray[dataKeysArray.index(k)],
                dataTag=k,
                data=dataObj[k],
                quantity=quantity,

                xlabel=xlabel,
                ylabel=ylabel,
                xsticklabel=xsticklabel,
            )
        plt.tight_layout()

        if isinstance(args.saveFolder, Path):
            saveLoc = args.saveFolder / args.fileName
            PlotFig = plt.savefig(
                saveLoc,
                format=args.format,
                dpi=args.dpi,
                bbox_inches='tight',
            )
            return PlotFig, saveLoc
        else:
            print("To export figure, use type 'Path' in 'saveFolder'.")
            return PlotFig, None

    @overload
    def valueGetter(v: dict[float], quantity) -> float: ...
    @overload
    def valueGetter(v: float, quantity) -> float: ...

    @staticmethod
    def valueGetter(v: float, quantity) -> Optional[float]:
        if isinstance(v, dict):
            return v[quantity] if quantity in v else None
        elif isinstance(v, float):
            return v
        else:
            raise ValueError(f"Unavailable type '{type(v)}'")

    @overload
    def stickLabelGiver(l: int) -> int: ...
    @overload
    def stickLabelGiver(l: str) -> Optional[str]: ...

    @staticmethod
    def stickLabelGiver(l):
        if isinstance(l, int):
            return l
        elif isinstance(l, str):
            return l if len(l) < 4 else None
        else:
            raise ValueError(f"Unavailable type '{type(l)}'")

    def errorBar_old(
        self,
        quantity: str = 'entropy',
        **otherArgs: any,
    ) -> tuple[Figure, Optional[Path]]:
        """_summary_

        Returns:
            tuple[Figure, Optional[Path]]: _description_
        """
        args = self.drawConfigControls(
            plotType='errorBar',
            plotName=self.plotName,
            saveFolder=self.saveFolder,
            quantity=quantity,
            **otherArgs
        )

        mainPlot: Figure = plt.figure()
        errorBarAx: Axes = mainPlot.add_subplot(1, 1, 1)

        # label
        errorBarAx.set_xlabel(
            f"ErrorBar of Experiments", size=args.fontSize)
        errorBarAx.set_ylabel(f"{args.plotName}", size=args.fontSize)

        # yLim, xLim
        # if isinstance(args.yLim, Callable):
        #     plt.ylim(args.yLim(self.data))
        # elif isinstance(args.yLim, tuple):
        #     plt.ylim(args.yLim)
        # else:
        #     plt.ylim(yLimDecider(self.data))

        # xLim, data length
        plt.xlim((0, 2*(len(self.data)+1)))
        length = len(self.data)

        # xstick
        errorBarAx.set_xticks([2*i for i in range(length+2)])
        errorBarAx.set_xticklabels(
            [None]+[k for k in self.data]+[None],
            rotation=90,
        )
        errorBarAx.grid(linestyle=args.lineStyle)

        # draw
        dataKeys = list(self.data.keys())
        for i in range(length):
            k = dataKeys[i]
            dataAtK = [
                self.valueGetter(quantityContainer, args.quantity)
                for quantityContainer in self.data[k]
                if self.valueGetter(quantityContainer, args.quantity) != None]
            errorBarAx.errorbar(
                [2*(i+1)],
                [np.mean(dataAtK)],
                [np.std(dataAtK)],
                capsize=10,
                linewidth=2,
                elinewidth=2,
                marker='.',
                label="".join([f"{k}"])
            )
            errorBarAx.scatter(
                [2*(i+1) for v in dataAtK],
                dataAtK,
                marker='x',
                label="".join([f"{k}"])
            )

        # legend
        h, l = errorBarAx.get_legend_handles_labels()
        legendPlt = errorBarAx.legend(
            handles=zip(h[:length], h[length:]),
            handler_map={tuple: matplotlib.legend_handler.HandlerTuple(None)},
            labels=l[:length],
            bbox_to_anchor=(1.025, 1.0),
            loc='upper left',
            borderaxespad=0.,
        )

        if isinstance(args.saveFolder, Path):
            saveLoc = args.saveFolder / args.fileName
            PlotFig = plt.savefig(
                saveLoc,
                format=args.format,
                dpi=args.dpi,
                bbox_extra_artists=(legendPlt, ),
                bbox_inches='tight',
            )
            return PlotFig, saveLoc
        else:
            print("To export figure, use type 'Path' in 'saveFolder'.")
            return PlotFig, None
