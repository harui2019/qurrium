from matplotlib.figure import Figure
from matplotlib.axes import Axes, SubplotBase
import matplotlib.pyplot as plt
import matplotlib

import numpy as np
import warnings
import os
from pathlib import Path
from math import pi
from typing import Callable, Optional, Union, Annotated, NamedTuple

from ..tool import argdict
from .widget import *


class argdictQurryPlot(NamedTuple):
    yLim: Union[callable, tuple[float, int]]
    fontSize: int
    lineStyle: str
    foramt: str
    dpi: int

    quantity: str

    plotType: str
    plotName: str
    filename: Path
    saveFolder: Union[Path, str]


class QurryplotV1:
    """QurryplotV1 will be pointed to migrate old code and function in draw.py

    Returns:
        _type_: _description_
    """

    @staticmethod
    def drawConfigControls(
        yLim: Union[callable, tuple[float, int]] = yLimDecider,
        fontSize: int = 12,
        lineStyle: str = '--',
        format: str = 'png',
        dpi: int = 300,

        quantity: str = 'entropy',

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
        data: dict[list[Union[float, int]]],
        plotName: str = 'Qurryplot',
        saveFolder: Union[Path, str] = './',
        **otherArgs: any,
    ) -> None:
        """_summary_

        Args:
            data (dict[list[Union[float, int]]]): _description_

            - data input format

            >>> {
            >>>     'trivialPM_4': [...],
            >>>     'cat_4': [...],
            >>>     'topPMPeriod_4': [...],
            >>>     'topPMOpen_4': [...],
            >>>     ...
            >>> }


            plotName (str, optional): _description_. Defaults to 'Qurryplot'.
            saveFolder (Optional[Path], optional): _description_. Defaults to None.
        """
        self.fulldata = data
        self.data = {
            k: self.fulldata[k] for k in self.fulldata
            if k not in ['all', 'noTags']}

        self.plotName = plotName
        self.saveFolder = saveFolder

    def errorBar(
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
                quantityContainer[args.quantity]
                for quantityContainer in self.data[k]
                if args.quantity in quantityContainer]
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
