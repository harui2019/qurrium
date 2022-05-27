from qiskit import (
    QuantumRegister, ClassicalRegister, QuantumCircuit)
from qiskit.providers.ibmq.managed import ManagedResults, IBMQManagedResultDataNotAvailable
from qiskit.visualization import *

from qiskit.result import Result

import numpy as np
import warnings
from typing import Union, Optional, Callable, List, NamedTuple
from qiskit.visualization.counts_visualization import hamming_distance

from .qurrent import EntropyMeasureV3
from ..tool import Configuration
# EntropyMeasure V0.3.0 - Measuring Renyi Entropy - Qurrech


class hadamardTestV3(EntropyMeasureV3):
    """hadamardTest V0.3.0 of qurrech
    """

    """ Configuration """

    class argdictCore(NamedTuple):
        expsName: str = 'exps',
        wave: Union[QuantumCircuit, any, None] = None,
        degree: Optional[int] = None,

    # Initialize
    def initialize(self) -> dict[str: any]:
        """Configuration to Initialize haarMeasure.

        Returns:
            dict[str: any]: The basic configuration of `haarMeasure`.
        """

        self._expsConfig = self.expsConfig(
            name="qurrentConfig",
        )
        self._expsBase = self.expsBase(
            name="qurrentBase",
            defaultArg={
                # Reault of experiment.
                'entropy': -100,
                'purity': -100,
            },
        )
        self._expsHint = self.expsHint(
            name='qurrechBaseHint',
            hintContext={
                'entropy': 'The Renyi Entropy.',
                'purity': '',
            },
        )
        self._expsMultiConfig = self.expsConfigMulti(
            name="qurrentConfigMulti",
        )
        self.shortName = 'qurrent.hadamard'
        self.__name__ = 'qurrent.hadamardTest'

        return self._expsConfig, self._expsBase

    """Arguments and Parameters control"""

    def paramsControlMain(
        self,
        expsName: str = 'exps',
        wave: Union[QuantumCircuit, any, None] = None,
        degree: Optional[int] = None,
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

            degree (Optional[int], optional): 
                The degree of freedom.
                If input is `None`, 
                then use the number of half qubits for even number of qubits, 
                or (the number of qubits + 1)/2 for odd number of qubits.
                If input is illegal, then raise ValueError.
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

        # degree
        numQubits = self.waves[wave].num_qubits
        if degree > numQubits:
            raise ValueError(
                f"The subsystem A includes {degree} qubits beyond {numQubits} which the wave function has.")
        elif degree < 0:
            raise ValueError(
                f"The number of qubits of subsystem A has to be natural number.")

        return {
            'wave': wave,
            'degree': degree,
            'numQubit': numQubits,
            'expsName': f"{expsName}.{wave}-deg={degree}.{self.__name__}",
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
        argsNow: super().argdictNow = self.now
        numQubits = self.waves[argsNow.wave].num_qubits

        qAnc = QuantumRegister(1, 'ancilla')
        qFunc1 = QuantumRegister(numQubits, 'q1')
        qFunc2 = QuantumRegister(numQubits, 'q2')
        cMeas1 = ClassicalRegister(1, 'c1')
        qcExp1 = QuantumCircuit(qAnc, qFunc1, qFunc2, cMeas1)

        qcExp1.append(self.waveInstruction(
            wave=argsNow.wave,
            runBy=argsNow.runBy,
            backend=argsNow.backend,
        ), [qFunc1[i] for i in range(numQubits)])

        qcExp1.append(self.waveInstruction(
            wave=argsNow.wave,
            runBy=argsNow.runBy,
            backend=argsNow.backend,
        ), [qFunc2[i] for i in range(numQubits)])

        qcExp1.barrier()
        qcExp1.h(qAnc)
        for i in range(argsNow.degree):
            qcExp1.cswap(qAnc[0], qFunc1[i], qFunc2[i])
        qcExp1.h(qAnc)
        qcExp1.measure(qAnc, cMeas1)

        return [qcExp1]

    @classmethod
    def quantity(
        cls,
        shots: int,
        result: Union[Result, ManagedResults],
        resultIdxList: Optional[list[int]] = None,
        **otherArgs,
    ) -> tuple[dict, dict]:
        """Computing specific quantity.
        Where should be overwritten by each construction of new measurement.

        Returns:
            tuple[dict, dict]:
                Counts, purity, entropy of experiment.
        """
        if resultIdxList == None:
            resultIdxList = [0]
        elif isinstance(resultIdxList, list):
            if len(resultIdxList) == 1:
                ...
            else:
                raise ValueError(
                    "The element number of 'resultIdxList' needs to 1 for 'hadamardTest'.")
        else:
            raise ValueError("'resultIdxList' needs to be 'list'.")

        counts = []
        onlyCount = None
        purity = -100

        try:
            counts = [result.get_counts(i) for i in resultIdxList]
            onlyCount = counts[0]
        except IBMQManagedResultDataNotAvailable as err:
            print("| Failed Job result skip, index:", resultIdxList, err)
            return {}

        isZeroInclude = '0' in onlyCount
        isOneInclude = '1' in onlyCount
        if isZeroInclude and isOneInclude:
            purity = (onlyCount['0'] - onlyCount['1'])/shots
        elif isZeroInclude:
            purity = onlyCount['0']/shots
        elif isOneInclude:
            purity = onlyCount['1']/shots
        else:
            purity = None
            raise Warning("Expected '0' and '1', but there is no such keys")

        entropy = -np.log2(purity)
        quantity = {
            'purity': purity,
            'entropy': entropy,
        }
        return counts, quantity

    """ Main Process: Main Control"""

    def measure(
        self,
        wave: Union[QuantumCircuit, any, None] = None,
        degree: Optional[int] = None,
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
            degree=degree,
            expsName=expsName,
            **otherArgs,
        )
