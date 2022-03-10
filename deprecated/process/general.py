from qiskit.visualization import plot_histogram
import os
import numpy as np
from pathlib import Path
from typing import Union, Callable


def universal_cmd(
    cmd: str = ""
) -> None:
    """[summary]

    Args:
        cmd (str, optional): Which execute command in any python or
            jupyter environment. Defaults to "".
    """
    try:
        from IPython import get_ipython
        get_ipython().system(cmd)
    except:
        os.system(cmd)


def pytorchCUDACheck(
) -> None:
    """Via pytorch to check Nvidia CUDA available.
    """
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
) -> Union[Exception, any]:
    """Check whether the parameter is the type which required, then  
    transform into another type or handle it with specific function.

    Args:
        target (any): The parameter
        typeWantAndHandle (list[tuple[type, Union[type, Callable]]]): 
            The required type and the 

    Raises:
        TypeError: When there is no type which meet the requirement.

    Returns:
        Union[Exception, any]: The result of handle the parameter or 
            the error which the parameter does not meet the requirement.
    """
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


def configKeyCheckGeneral(
    target: dict,
    keyCheck: list[str] = [
        'qPairNum', 'boundaryCond', 'alpha', 'beta',
        'circuitRunBy', 'initSet', 'hamiltonianIndex', 'timeEvo',
        'collectA', 'waveFigType', 'waveComposeMethod',
        'goRunby', 'goFigType', 'goComposeMethod',
        'shots', 'singleResultKeep', 'countPlotKeep',
    ]
) -> list:
    """Check whether the configuration is completed.

    Args:
        target (dict): The configuration
        keyCheck (List[str], optional): The required items. Defaults to 
            [ 'qPairNum', 'boundaryCond', 'alpha', 'beta', 'circuitRunBy',
            'initSet', 'hamiltonianIndex', 'timeEvo', 'collectA',
            'waveFigType', 'waveComposeMethod', 'goRunby', 'goFigType',
            'goComposeMethod', 'shots', 'singleResultKeep', 'countPlotKeep' ].

    Raises:
        KeyError: When configuration is not completed.

    Returns:
        list: The keys of the configuration.
    """
    targetKeys = list(target.keys())
    for k in keyCheck:
        if not k in targetKeys:
            print(target)
            raise KeyError(
                f"'{k}' is lost in Configuration, make sure it has been configured.")
    return targetKeys


class syncControl(list):
    """A quick way to create .gitignore

    Args:
        list ([type]): A simple inherition from list.
    """

    def sync(
        self,
        fileName: str
    ) -> None:
        """Add file to sync.

        Args:
            fileName (str): FileName.
        """
        self.append(f"!{fileName}")

    def ignore(
        self,
        fileName: str
    ) -> None:
        """Add file to ignore from sync.

        Args:
            fileName (str): FileName.
        """
        self.append(f"{fileName}")

    def export(
        self,
        saveFolderName: Path,
    ) -> None:
        """Export .gitignore

        Args:
            saveFolderName (Path): The location of .gitignore.
        """
        with open(
            saveFolderName / f".gitignore", 'w', encoding='utf-8'
        ) as ignoreList:
            [print(item, file=ignoreList) for item in self]

    def add(
        self,
        saveFolderName: Path,
    ) -> None:
        """Export .gitignore

        Args:
            saveFolderName (Path): The location of .gitignore.
        """
        with open(
            saveFolderName / f".gitignore", 'a', encoding='utf-8'
        ) as ignoreList:
            [print(item, file=ignoreList) for item in self]


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
