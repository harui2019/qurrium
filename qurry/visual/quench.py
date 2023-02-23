from typing import Union, Iterable, NamedTuple, Optional
from matplotlib.figure import Figure
from matplotlib.axes import Axes, SubplotBase
from pathlib import Path
from math import pi

import matplotlib.pyplot as plt

from .qurchart import paramsControl
from ..mori import TagList
from ..qurrium import Quantity


def quench(
    data: Union[TagList[Quantity], dict[str, dict[str, float]]],
    beta: float,
    timeEvo: Iterable,
    name: str,
    saveFolder: Optional[Union[Path, str]] = None,
    quantity: str = 'entropy',
    **otherArgs,
) -> tuple[Figure, Union[str, Path]]:
    """_summary_

    Args:
        data (Union[TagList[Quantity], dict[str, dict[str, float]]]): _description_
        beta (float): _description_
        timeEvo (Iterable): _description_
        name (str): _description_
        saveFolder (Optional[Union[Path, str]], optional): _description_. Defaults to None.
        config (QurchartConfig, optional): _description_. Defaults to QurchartConfig().

    Raises:
        TypeError: _description_

    Returns:
        tuple[Figure, Union[str, Path]]: _description_
    """

    config = paramsControl(
        data=data,
        additionName=name,
        plotName=f'{quantity}.quench',
        quantity=quantity,
        saveFolder=saveFolder,
        **otherArgs,
    )

    fig = plt.figure()
    ax_main: Union[SubplotBase, Axes] = fig.add_subplot(1, 1, 1)

    # ax_main.set_title(config.name)
    ax_main.set_xlabel(
        f'evolution ($\Delta t = {beta} \pi$)', size=config.fontSize)
    ax_main.set_ylabel(f"{config.quantity}", size=config.fontSize)

    ax_main.set_xticks(timeEvo)
    ax_main.set_xticklabels([i if (i % 5 == 0) else None for i in timeEvo])

    ax_main.grid(linestyle=config.lineStyle)

    if not isinstance(data, dict):
        raise TypeError('entropies must be a dictionary.')

    for k, v in data.items():
        if isinstance(v, dict):
            v = v.values()
        ax_main.plot(
            timeEvo, v,
            marker='.',
            label="".join([f"{k}"])
        )
    ax_main_legend = ax_main.legend(
        bbox_to_anchor=(1.025, 1.0),
        loc='upper left',
        borderaxespad=0.
    )

    if config.exportPltObjects:
        return fig, config.name

    else:
        saveLoc = config.saveFolder / config.filename
        export_fig = plt.savefig(
            saveLoc,
            format=config.filetype,
            dpi=config.dpi,
            bbox_extra_artists=(ax_main_legend,),
            # bbox_extra_artists=(ax_main_legend, ax_main_secxa,),
            bbox_inches='tight'
        )

        return export_fig, config.saveFolder/config.filename
