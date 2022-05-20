from qiskit import (
    QuantumRegister, ClassicalRegister, QuantumCircuit)
from qiskit.result import Result
from qiskit.providers.ibmq.managed import ManagedResults

import numpy as np
import warnings
from math import pi
from itertools import permutations
import time
from typing import Union, Optional, NamedTuple

from ..qurrium import Qurry
from ..tool import Configuration

# MagnetSquare V0.3.0 - Measuring Loschmidt Echo - Qurrech


class MagnetSquare(Qurry):
    """MagnetSquare V0.3.0 of qurmagsq
    """

    class argdictCore(NamedTuple):
        expsName: str = 'exps',
        wave: Union[QuantumCircuit, any, None] = None,

    # Initialize
    def initialize(self) -> dict[str: any]:
        """Configuration to Initialize Qurrech.

        Returns:
            dict[str: any]: The basic configuration of `Qurrech`.
        """

        self._expsConfig = self.expsConfig(
            name="qurmagsqConfig",
        )
        self._expsBase = self.expsBase(
            name="qurmagsqBase",
            defaultArg={
                # Reault of experiment.
                'magnetsq': -100,
            },
        )
        self._expsHint = self.expsHint(
            name='qurmagsqBaseHint',
            hintContext={
                'magnetsq': 'The Magnet Square.',
            },
        )
        self._expsMultiConfig = self.expsConfigMulti(
            name="qurmagsqConfigMulti",
        )
        self.shortName = 'qurmagsq'
        self.__name__ = 'MagnetSquare'

        return self._expsConfig, self._expsBase

    """Arguments and Parameters control"""

    def paramsControlMain(
        self,
        expsName: str = 'exps',
        wave: Union[QuantumCircuit, any, None] = None,
        **otherArgs: any
    ) -> dict:
        """Handling all arguments and initializing a single experiment.

        Args:
            wave (Union[QuantumCircuit, int, None], optional): 
                The index of the wave function in `self.waves` or add new one to calaculation,
                then choose one of waves as the experiment material.
                If input is `QuantumCircuit`, then add and use it.
                If input is the key in `.waves`, then use it.
                If input is `None` or something illegal, then use `.lastWave'.
                Defaults to None.

            expsName (str, optional):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.

            otherArgs (any):
                Other arguments.

        Raises:
            KeyError: Given `expID` does not exist.
            TypeError: When parameters are not all to be `int`.
            KeyError: The given parameters lost degree of freedom.".

        Returns:
            tuple[str, dict[str: any]]: Current `expID` and arguments.
        """

        # wave
        if isinstance(wave, QuantumCircuit):
            wave = self.addWave(wave)
            print(f"| Add new wave with key: {wave}")
        elif wave == None:
            wave = self.lastWave
            print(f"| Autofill will use '.lastWave' as key")
        else:
            try:
                self.waves[wave]
            except KeyError as e:
                warnings.warn(f"'{e}', use '.lastWave' as key")
                wave = self.lastWave

        numQubits = self.waves[wave].num_qubits

        return {
            'wave': wave,
            'numQubit': numQubits,
            'expsName': f"{expsName}.{wave}.magsq",
            **otherArgs,
        }

    """ Main Process: Circuit"""

    def circuitMethod(
        self,
    ) -> Union[QuantumCircuit, list[QuantumCircuit]]:
        """The method to construct circuit.
        Where should be overwritten by each construction of new measurement.

        Returns:
            Union[QuantumCircuit, list[QuantumCircuit]]: 
                The quantum circuit of experiment.
        """
        argsNow = self.now
        numQubits = self.waves[argsNow.wave].num_qubits

        qcExpList = []
        permut = [b for b in permutations([a for a in range(numQubits)], 2)]
        numPermut = len(permut)
        idxPermut = 0
        ABegin = time.time()
        print(f"| Build circuit A: {argsNow.wave}", end="\r")
        for i, j in permut:
            qFunc = QuantumRegister(numQubits, 'q1')
            cMeas = ClassicalRegister(2, 'c1')
            qcExp = QuantumCircuit(qFunc, cMeas)

            qcExp.append(self.waveInstruction(
                wave=argsNow.wave,
                runBy=argsNow.runBy,
                backend=argsNow.backend,
            ), [qFunc[i] for i in range(numQubits)])

            qcExp.barrier()
            qcExp.measure(qFunc[i], cMeas[0])
            qcExp.measure(qFunc[j], cMeas[1])

            qcExpList.append(qcExp)
            print(
                f"| Build circuit: {i} x {j}" +
                f" - {idxPermut}/{numPermut} - {round(time.time() - ABegin, 3)}s.", end="\r")
            idxPermut += 1
        print(
            f"| Circuit completed: {argsNow.wave}" +
            f" - {idxPermut}/{numPermut} - {round(time.time() - ABegin, 3)}s." +
            " "*30)

        return qcExpList

    """ Main Process: Data Import and Export"""

    """ Main Process: Job Create"""

    """ Main Process: Calculation and Result"""

    """ Main Process: Purity and Entropy"""

    @classmethod
    def quantity(
        cls,
        shots: int,
        result: Union[Result, ManagedResults],
        resultIdxList: Optional[list[int]] = None,
        numQubit: int = None,
        **otherArgs,
    ) -> tuple[dict, dict]:
        """Computing specific quantity.
        Where should be overwritten by each construction of new measurement.

        Returns:
            tuple[dict, dict]:
                Counts, purity, entropy of experiment.
        """

        if resultIdxList == None:
            resultIdxList = [i for i in range(numQubit*(numQubit-1))]
        elif isinstance(resultIdxList, list):
            if len(resultIdxList) > 1:
                ...
            elif len(resultIdxList) != numQubit*(numQubit-1):
                raise ValueError(
                    f"The element number of 'resultIdxList': {len(resultIdxList)} is different with 'N(N-1)': {times*2}.")
            else:
                raise ValueError(
                    f"The element number of 'resultIdxList': {len(resultIdxList)} needs to be more than 1 for 'MagnetSquare'.")
        else:
            raise ValueError("'resultIdxList' needs to be 'list'.")

        counts = [result.get_counts(i) for i in resultIdxList]
        magnetsq = -100
        magnetsqCellList = []

        length = len(resultIdxList)
        idx = 0
        Begin = time.time()
        print(f"| Calculating magnetsq ...", end="\r")
        for i in resultIdxList:
            magnetsqCell = 0
            checkSum = 0
            print(
                f"| Calculating magnetsq on {i}" +
                f" - {idx}/{length} - {round(time.time() - Begin, 3)}s.", end="\r")
            allMeas = result.get_counts(i)

            for bits in allMeas:
                checkSum += allMeas[bits]
                if (bits == '00') or (bits == '11'):
                    magnetsqCell += allMeas[bits]/shots
                else:
                    magnetsqCell -= allMeas[bits]/shots

            if checkSum != shots:
                raise ValueError(
                    f"'{allMeas}' may not be contained by '00', '11', '01', '10'.")

            magnetsqCellList.append(magnetsqCell)
            print(
                f"| Calculating magnetsq end - {idx}/{length}" +
                f" - {round(time.time() - Begin, 3)}s." +
                " "*30, end="\r")
            idx += 1
        print(
            f"| Calculating magnetsq end - {idx}/{length}" +
            f" - {round(time.time() - Begin, 3)}s.")

        magnetsq = (sum(magnetsqCellList) + numQubit)/(numQubit**2)

        quantity = {
            'magnetsq': magnetsq,
        }
        return counts, quantity

    """ Main Process: Main Control"""

    def measure(
        self,
        wave: Union[QuantumCircuit, any, None] = None,
        expsName: str = 'exps',
        **otherArgs: any
    ) -> dict:
        """

        Args:
            wave (Union[QuantumCircuit, int, None], optional):
                The index of the wave function in `self.waves` or add new one to calaculation,
                then choose one of waves as the experiment material.
                If input is `QuantumCircuit`, then add and use it.
                If input is the key in `.waves`, then use it.
                If input is `None` or something illegal, then use `.lastWave'.
                Defaults to None.

            expsName (str, optional):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.

            otherArgs (any):
                Other arguments.

        Returns:
            dict: The output.
        """
        return self.output(
            wave=wave,
            expsName=expsName,
            **otherArgs,
        )
