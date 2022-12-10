from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit.result import Result
from qiskit.providers.ibmq.managed import ManagedResults, IBMQManagedResultDataNotAvailable

import numpy as np
import warnings
from typing import Hashable, Union, Optional, NamedTuple

from ..qurrium import QurryV4, qubit_selector, wave_selector, Counts
from ..mori import defaultConfig

# EchoListen V0.4.0 - Measuring Loschmidt Echo - Qurrech


class EchoHadamardTestV4(QurryV4):
    """HadamardTest V0.4.0 of qurrech

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

    """ Configuration """

    class argsCore(NamedTuple):
        expsName: str = None
        wave1: Union[QuantumCircuit, any, None] = None
        wave2: Union[QuantumCircuit, any, None] = None
        degree: tuple[int, int] = None

    class expsCore(NamedTuple):
        echo: float

    # Initialize
    def initialize(self) -> dict[str, any]:
        """Configuration to Initialize haarMeasure.

        Returns:
            dict[str, any]: The basic configuration of `haarMeasure`.
        """
        self._expsBase = defaultConfig(
            name='QurrechHadamardBase',
            default={
                **self.argsMain()._asdict(),
                **self.argsCore()._asdict(),
                **self.expsMain()._asdict(),
            },
        )
        self._expsHint = {
            **{k: f"sample: {v}" for k, v in self._expsBase},
            "_basicHint": "This is a hint of QurryV4.",
        }
        self._expsMultiBase = defaultConfig(
            name='QurrechHadamardMultiBase',
            default={
                **self.argsMultiMain()._asdict(),
                **self.expsMultiMain()._asdict(),
            },
        )

        self.shortName = 'qurrech_hadamard'
        self.__name__ = 'qurrech_hadamardTest'
        
    def paramsControlCore(
        self,
        expsName: Optional[str] = None,
        wave1: Union[QuantumCircuit, any, None] = None,
        wave2: Union[QuantumCircuit, any, None] = None,
        degree: Union[int, tuple[int, int], None] = None,
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
            tuple[str, dict[str, any]]: Current `expID` and arguments.
        """

        # wave
        wave1 = wave_selector(self, wave1)
        wave2 = wave_selector(self, wave2)

        # degree
        numQubits1 = self.waves[wave1].num_qubits
        numQubits2 = self.waves[wave2].num_qubits
        if numQubits1 != numQubits2:
            raise ValueError(
                f"Wave1 with {numQubits1} qubits and Wave2 with {numQubits2} qubits are different system size.")
        numQubits = numQubits1
        
        if degree is None:
            degree = numQubits
        degree = qubit_selector(numQubits, degree=degree)

        # expsName
        if expsName is None:
            expsName = f"w1={wave1}-w2={wave2}-deg={degree[1]-degree[0]}.{self.shortName}"

        return (
            self.argsCore(**{
                'wave1': wave1,
                'wave2': wave2,
                'degree': degree,
                'expsName': expsName,
            }),
            {
                k: v for k, v in otherArgs.items()
                if k not in self.argsCore._fields
            }
        )
        

    def method(
        self,
    ) -> Union[QuantumCircuit, list[QuantumCircuit]]:
        """The method to construct circuit.
        Where should be overwritten by each construction of new measurement.

        Returns:
            Union[QuantumCircuit, list[QuantumCircuit]]: 
                The quantum circuit of experiment.
        """
        argsNow: Union[QurryV4.argsMain,
                       EchoHadamardTestV4.argsCore] = self.now
        numQubits = self.waves[argsNow.wave1].num_qubits

        qAnc = QuantumRegister(1, 'ancilla')
        qFunc1 = QuantumRegister(numQubits, 'q1')
        qFunc2 = QuantumRegister(numQubits, 'q2')
        cMeas1 = ClassicalRegister(1, 'c1')
        qcExp1 = QuantumCircuit(qAnc, qFunc1, qFunc2, cMeas1)

        qcExp1.append(self.waveCall(
            wave=argsNow.wave1,
            runBy=argsNow.runBy,
            backend=argsNow.backend,
        ), [qFunc1[i] for i in range(numQubits)])

        qcExp1.append(self.waveCall(
            wave=argsNow.wave2,
            runBy=argsNow.runBy,
            backend=argsNow.backend,
        ), [qFunc2[i] for i in range(numQubits)])

        qcExp1.barrier()
        qcExp1.h(qAnc)
        for i in range(*argsNow.degree):
            qcExp1.cswap(qAnc[0], qFunc1[i], qFunc2[i])
        qcExp1.h(qAnc)
        qcExp1.measure(qAnc, cMeas1)

        return [qcExp1]
    
    @classmethod
    def counts(
        cls,
        result: Union[Result, ManagedResults],
        resultIdxList: Optional[list[int]] = None,
        **otherArgs,
    ):
        """Computing specific squantity.
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
        for i in resultIdxList:
            try:
                allMeas = result.get_counts(i)
                counts.append(allMeas)
            except IBMQManagedResultDataNotAvailable as err:
                counts.append({})
                print("| Failed Job result skip, index:", i, err)
                continue

        return counts
    
    @classmethod
    def quantities(
        cls,
        shots: int,
        counts: list[Counts],
        degree: tuple[int, int] = None,

        run_log: dict[str] = {},
        **otherArgs,
    ) -> expsCore:

        purity = -100
        entropy = -100
        onlyCount = counts[0]

        if (1 == len(counts)):
            ...
        else:
            warnings.warn(f"Hadamard test should only have one count, but there is '{len(counts)}'")

        isZeroInclude = '0' in onlyCount
        isOneInclude = '1' in onlyCount
        if isZeroInclude and isOneInclude:
            purity = (onlyCount['0'] - onlyCount['1'])/shots
        elif isZeroInclude:
            purity = onlyCount['0']/shots
        elif isOneInclude:
            purity = onlyCount['1']/shots
        else:
            purity = np.Nan
            raise Warning("Expected '0' and '1', but there is no such keys")

        entropy = -np.log2(purity)
        quantity = {
            'purity': purity,
            'entropy': entropy,
        }
        return quantity

    def measure(
        self,
        wave1: Union[QuantumCircuit, any, None] = None,
        wave2: Union[QuantumCircuit, any, None] = None,
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
            wave1=wave1,
            wave2=wave2,
            degree=degree,
            expsName=expsName,
            **otherArgs,
        )