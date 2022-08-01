from typing import Union, Iterable, NamedTuple, Optional
from matplotlib.figure import Figure
from matplotlib.axes import Axes, SubplotBase
from pathlib import Path
from math import pi
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

from .qurchart import paramsControl, valueGetter, stickLabelGiver
from ..mori.type import TagMapType
from ..qurrium import Quantity


def errorBar(
    data: Union[TagMapType[Quantity], dict[str, dict[str, float]]],

    name: str,
    quantity: str = 'entropy',
    **otherconfig: any,
) -> tuple[Figure, Optional[Path]]:

    config = paramsControl(
        **otherconfig,
        additionName=name,
        name=f'{quantity}.quench',
        quantity=quantity
    )

    fig = plt.figure()
    ax_main: Union[SubplotBase, Axes] = fig.add_subplot(1, 1, 1)

    # label
    ax_main.set_xlabel(
        f"ErrorBar of Experiments", size=config.fontSize)
    ax_main.set_ylabel(f"{config.quantity  }", size=config.fontSize)

    # xLim, data length
    plt.xlim((0, 2*(len(data)+1)))
    length = len(data)

    # xstick
    ax_main.set_xticks([2*i for i in range(length+2)])
    ax_main.set_xticklabels(
        [None]+[k for k in data]+[None],
        rotation=90,
    )
    ax_main.grid(linestyle=config.lineStyle)

    # draw
    dataKeys = list(data.keys())
    for i in range(length):
        k = dataKeys[i]
        dataAtK = [
            valueGetter(quantityContainer, config.quantity)
            for quantityContainer in data[k]
            if valueGetter(quantityContainer, config.quantity) != None]
        ax_main.errorbar(
            [2*(i+1)],
            [np.mean(dataAtK)],
            [np.std(dataAtK)],
            capsize=10,
            linewidth=2,
            elinewidth=2,
            marker='.',
            label="".join([f"{k}"])
        )
        ax_main.scatter(
            [2*(i+1) for v in dataAtK],
            dataAtK,
            marker='x',
            label="".join([f"{k}"])
        )

        # legend
    h, l = ax_main.get_legend_handles_labels()
    ax_main_legend = ax_main.legend(
        handles=zip(h[:length], h[length:]),
        handler_map={tuple: matplotlib.legend_handler.HandlerTuple(None)},
        labels=l[:length],
        bbox_to_anchor=(1.025, 1.0),
        loc='upper left',
        borderaxespad=0.,
    )

    if config.exportPltObjects:
        return fig, config.name

    else:
        saveLoc = config.saveFolder / config.fileName
        export_fig = plt.savefig(
            saveLoc,
            format=config.filetype,
            dpi=config.dpi,
            dpi=config.dpi,
            bbox_extra_artists=(ax_main_legend, ),
            bbox_inches='tight',
        )
        return export_fig, saveLoc
