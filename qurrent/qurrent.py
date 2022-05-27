from qiskit import (
    QuantumRegister,
    ClassicalRegister,
    QuantumCircuit
)
from qiskit.result import Result
from qiskit.providers.ibmq.managed import ManagedResults

import numpy as np
import warnings
from math import pi
from typing import Union, Optional, NamedTuple, overload

from ..qurrium import Qurry
from ..tool import Configuration

# EntropyMeasure V0.3.0 - Measuring Renyi Entropy - Qurrent


class EntropyMeasureV3(Qurry):
    """EntropyMeasure V0.3.0 of qurrech
    """

    """ Configuration """

    class argdictCore(NamedTuple):
        expsName: str = 'exps',
        wave: Union[QuantumCircuit, any, None] = None,
        degree: Optional[int] = None,

    # class argdictNow(argdictCore, Qurry().argdictNow):
    #     ...    
        
    # class argdicMultiNow(argdictCore, Qurry().argdictMultiNow):
    #     ...  
        
    # def expsConfig(
    #     self,
    #     name: str = 'qurryConfig',
    #     defaultArg: dict[any] = {
    #         **argdictCore()._asdict()
    #     },
    # ) -> Configuration:
    #     return super().expsConfig(name, defaultArg)
    
    # def expsBase(
    #     self,
    #     name: str = 'qurryExpsBase',
    #     defaultArg: dict = {
    #         # Reault of experiment.
    #     },
    # ) -> Configuration:
    #     return super().expsBase(name, defaultArg)
    
    # def expsConfigMulti(
    #     self,
    #     name: str = 'qurryConfigMulti',
    #     defaultArg: dict[any] = {
    #         # Variants of experiment.
    #     },
    # ) -> Configuration:
    #     return super().expsConfigMulti(name, defaultArg)
    
    # def expsHint(
    #     self,
    #     name: str = 'qurryBaseHint',
    #     hintContext: dict = {
    #         "_basicHint": "This is a hint of qurry.",
    #     },
    # ) -> dict:
    #     return super().expsHint(name, hintContext)
        
    # Initialize
    def initialize(self) -> dict[str: any]:
        """Configuration to Initialize Hadamard.

        Returns:
            dict[str: any]: The basic configuration of `Qurrech`.
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
        self.shortName = 'qurrent'
        self.__name__ = 'EntropyMeasureV3'

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
            ValueError: The given degree of freedom larger than number of qubits or smaller than 0.

        Returns:
            dict: arguments.
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
        argsNow = self.now
        if (self.waves[argsNow.wave].num_qubits != self.waves[argsNow.wave2].num_qubits):
            raise ValueError(
                "Wave1 and Wave2 must be the same number of qubits.")
        numQubits = self.waves[argsNow.wave].num_qubits

        qFunc1 = QuantumRegister(numQubits, 'q1')
        qFunc2 = QuantumRegister(numQubits, 'q2')
        cMeas = ClassicalRegister(numQubits, 'c1')
        qcExp = QuantumCircuit(qFunc1, qFunc2, cMeas)

        qcExp.append(self.waveInstruction(
            wave=argsNow.wave,
            runBy=argsNow.runBy,
            backend=argsNow.backend,
        ), [qFunc1[i] for i in range(numQubits)])

        qcExp.append(self.waveInstruction(
            wave=argsNow.wave,
            runBy=argsNow.runBy,
            backend=argsNow.backend,
        ), [qFunc2[i] for i in range(numQubits)])

        for i in range(argsNow.degree):
            qcExp.measure(qFunc1[i], cMeas[i])
        print("It's default circuit, the quantum circuit is not yet configured.")

        return qcExp

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
        degree: int = None,
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
        else:
            ...

        warnings.warn(
            "It's default '.quantity' which exports meaningless value.")
        counts = result.get_counts(resultIdxList[0])

        purity = -100
        entropy = -100
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
