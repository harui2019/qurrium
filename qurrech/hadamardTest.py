from qiskit import (
    QuantumRegister, ClassicalRegister, QuantumCircuit)
from qiskit.providers.ibmq.managed import ManagedResults, IBMQManagedResultDataNotAvailable
from qiskit.visualization import *

from qiskit.result import Result

import numpy as np
import warnings
from typing import Union, Optional, Callable, List, NamedTuple
from qiskit.visualization.counts_visualization import hamming_distance

from .qurrech import EchoListen
# EchoListen V0.3.0 - Measuring Loschmidt Echo - Qurrech


class hadamardTest(EchoListen):
    """hadamardTest V0.3.0 of qurrech

    - Reference:
        - Used in:
            Entanglement spectroscopy on a quantum computer - Sonika Johri, Damian S. Steiger, and Matthias Troyer, [PhysRevB.96.195136](https://doi.org/10.1103/PhysRevB.96.195136)

        - `bibtex`:

```bibtex
@article{PhysRevB.96.195136,
    title = {Entanglement spectroscopy on a quantum computer},
    author = {Johri, Sonika and Steiger, Damian S. and Troyer, Matthias},
    journal = {Phys. Rev. B},
    volume = {96},
    issue = {19},
    pages = {195136},
    numpages = {7},
    year = {2017},
    month = {Nov},
    publisher = {American Physical Society},
    doi = {10.1103/PhysRevB.96.195136},
    url = {https://link.aps.org/doi/10.1103/PhysRevB.96.195136}
}

```
    """

    class argdictCore(NamedTuple):
        expsName: str = 'exps',
        wave1: Union[QuantumCircuit, any, None] = None,
        wave2: Union[QuantumCircuit, any, None] = None,

    # Initialize
    def initialize(self) -> dict[str: any]:
        """Configuration to Initialize Qurrech.

        Returns:
            dict[str: any]: The basic configuration of `Qurrech`.
        """

        self._expsConfig = self.expsConfig(
            name="qurrechConfig",
        )
        self._expsBase = self.expsBase(
            name="qurrechBase",
            defaultArg={
                # Reault of experiment.
                'echo': -100,
            },
        )
        self._expsHint = self.expsHint(
            name='qurrechBaseHint',
            hintContext={
                'echo': 'The Loschmidt Echo.',
            },
        )
        self._expsMultiConfig = self.expsConfigMulti(
            name="qurrentConfigMulti",
        )
        self.shortName = 'qurrech.hadamard'
        self.__name__ = 'qurrech.hadamardTest'

        return self._expsConfig, self._expsBase

    """Arguments and Parameters control"""

    def paramsControlMain(
        self,
        expsName: str = 'exps',
        wave1: Union[QuantumCircuit, any, None] = None,
        wave2: Union[QuantumCircuit, any, None] = None,
        **otherArgs: any
    ) -> dict:
        """Handling all arguments and initializing a single experiment.

        Args:
            wave1, wave2 (Union[QuantumCircuit, int, None], optional): 
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

        # wave1
        if isinstance(wave1, QuantumCircuit):
            wave1 = self.addWave(wave1)
            print(f"| Add new wave with key: {wave1}")
        elif wave1 == None:
            wave1 = self.lastWave
            print(f"| Autofill will use '.lastWave' as key")
        else:
            try:
                self.waves[wave1]
            except KeyError as e:
                warnings.warn(f"'{e}', use '.lastWave' as key")
                wave1 = self.lastWave

        # wave2
        if isinstance(wave2, QuantumCircuit):
            wave2 = self.addWave(wave2)
            print(f"| Add new wave with key: {wave2}")
        elif wave2 == None:
            wave2 = self.lastWave
            print(f"| Autofill will use '.lastWave' as key")
        else:
            try:
                self.waves[wave2]
            except KeyError as e:
                warnings.warn(f"'{e}', use '.lastWave' as key")
                wave2 = self.lastWave

        return {
            'wave1': wave1,
            'wave2': wave2,
            'expsName': f"w1={wave1}-w2={wave2}.{self.shortName}",
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
        if (self.waves[argsNow.wave1].num_qubits != self.waves[argsNow.wave2].num_qubits):
            raise ValueError(
                "Wave1 and Wave2 must be the same number of qubits.")
        numQubits = self.waves[argsNow.wave1].num_qubits

        qAnc = QuantumRegister(1, 'ancilla')
        qFunc1 = QuantumRegister(numQubits, 'q1')
        qFunc2 = QuantumRegister(numQubits, 'q2')
        cMeas1 = ClassicalRegister(1, 'c1')
        qcExp1 = QuantumCircuit(qAnc, qFunc1, qFunc2, cMeas1)

        qcExp1.append(self.waveInstruction(
            wave=argsNow.wave1,
            runBy=argsNow.runBy,
            backend=argsNow.backend,
        ), [qFunc1[i] for i in range(numQubits)])

        qcExp1.append(self.waveInstruction(
            wave=argsNow.wave2,
            runBy=argsNow.runBy,
            backend=argsNow.backend,
        ), [qFunc2[i] for i in range(numQubits)])

        qcExp1.barrier()
        qcExp1.h(qAnc)
        for i in range(numQubits):
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
            echo = (onlyCount['0'] - onlyCount['1'])/shots
        elif isZeroInclude:
            echo = onlyCount['0']/shots
        elif isOneInclude:
            echo = onlyCount['1']/shots
        else:
            echo = None
            raise Warning("Expected '0' and '1', but there is no such keys")

        quantity = {
            'echo': echo,
        }
        return counts, quantity

    """ Main Process: Main Control"""

    def measure(
        self,
        wave1: Union[QuantumCircuit, any, None] = None,
        wave2: Union[QuantumCircuit, any, None] = None,
        expsName: str = 'exps',
        **otherArgs: any
    ) -> dict:
        """The measure function which is the customized version of `.output`.

        Args:
            wave1, wave2 (Union[QuantumCircuit, int, None], optional): 
                The index of the wave function in `self.waves` or add new one to calaculation,
                then choose one of waves as the experiment material.
                If input is `QuantumCircuit`, then add and use it.
                If input is the key in `.waves`, then use it.
                If input is `None` or something illegal, then use `.lastWave'.
                Defaults to None.

            times (int, optional): 
                The number of test to count ensemble average.
                Defaults to `100`.

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
            wave1=wave1,
            wave2=wave2,
            expsName=expsName,
            **otherArgs,
        )
