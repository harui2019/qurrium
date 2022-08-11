from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit.providers.ibmq.managed import ManagedResults, IBMQManagedResultDataNotAvailable
from qiskit.quantum_info import random_unitary
from qiskit.result import Result

import numpy as np
import warnings
from typing import Union, Optional, NamedTuple
import time

from .qurrent import EntropyMeasureV3
from ..qurrium import haarBase
# EntropyMeasure V0.3.0 - Measuring Renyi Entropy - Qurrent


class haarMeasureV3(EntropyMeasureV3, haarBase):
    """haarMeasure V0.3.0 of qurrent

    - Reference:
        - Used in:
            Statistical correlations between locally randomized measurements: A toolbox for probing entanglement in many-body quantum states - A. Elben, B. Vermersch, C. F. Roos, and P. Zoller, [PhysRevA.99.052323](https://doi.org/10.1103/PhysRevA.99.052323)

        - `bibtex`:

```bibtex
@article{PhysRevA.99.052323,
    title = {Statistical correlations between locally randomized measurements: A toolbox for probing entanglement in many-body quantum states},
    author = {Elben, A. and Vermersch, B. and Roos, C. F. and Zoller, P.},
    journal = {Phys. Rev. A},
    volume = {99},
    issue = {5},
    pages = {052323},
    numpages = {12},
    year = {2019},
    month = {May},
    publisher = {American Physical Society},
    doi = {10.1103/PhysRevA.99.052323},
    url = {https://link.aps.org/doi/10.1103/PhysRevA.99.052323}
}
```
    """

    """ Configuration """

    class argsCore(NamedTuple):
        expsName: str = 'exps',
        wave: Union[QuantumCircuit, any, None] = None,
        degree: Optional[int] = None,
        times: int = 100,

    # Initialize
    def initialize(self) -> dict[str, any]:
        """Configuration to Initialize haarMeasure.

        Returns:
            dict[str, any]: The basic configuration of `haarMeasure`.
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
        self.shortName = 'qurrent.haar'
        self.__name__ = 'qurrent.haarMeasure'

        return self._expsConfig, self._expsBase

    """Arguments and Parameters control"""

    def paramsControlCore(
        self,
        expsName: str = 'exps',
        wave: Union[QuantumCircuit, any, None] = None,
        degree: Optional[int] = None,
        times: int = 100,
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

            times (int, optional): 
                The number of test to count ensemble average.
                Defaults to `100`.

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

        # times
        if not isinstance(times, int):
            raise ValueError("'times' must be an 'int'.")
        elif times <= 0:
            raise ValueError("'times' must be larger than 0.")

        return {
            'wave': wave,
            'degree': degree,
            'times': times,
            'numQubit': numQubits,
            'expsName': f"w={wave}-deg={degree}-at={times}.{self.shortName}",
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
        argsNow: EntropyMeasureV3.argsMain = self.now
        numQubits = self.waves[argsNow.wave].num_qubits

        qcList = []
        unitaryList = [
            [random_unitary(2) for j in range(numQubits)]
            for i in range(argsNow.times)]

        ABegin = time.time()
        print(f"| Build circuit: {argsNow.wave}", end="\r")
        for i in range(argsNow.times):
            qFunc1 = QuantumRegister(numQubits, 'q1')
            cMeas1 = ClassicalRegister(numQubits, 'c1')
            qcExp1 = QuantumCircuit(qFunc1, cMeas1)

            qcExp1.append(self.waveInstruction(
                wave=argsNow.wave,
                runBy=argsNow.runBy,
                backend=argsNow.backend,
            ), [qFunc1[i] for i in range(numQubits)])

            qcExp1.barrier()
            for j in range(numQubits):
                qcExp1.append(unitaryList[i][j], [j])
            for j in range(numQubits):
                qcExp1.measure(qFunc1[j], cMeas1[j])

            qcList.append(qcExp1)
            print(
                f"| Build circuit: {argsNow.wave}" +
                f" - {i+1}/{argsNow.times} - {round(time.time() - ABegin, 3)}s.", end="\r")

        print(
            f"| Circuit completed: {argsNow.wave}" +
            f" - {i+1}/{argsNow.times} - {round(time.time() - ABegin, 3)}s." +
            " "*30)

        self.exps[self.IDNow]['sideProduct']['randomized'] = {
            i: [self.qubitOpToPauliCoeff(unitaryList[i][j])
                for j in range(numQubits)]
            for i in range(argsNow.times)}

        return qcList

    @classmethod
    def quantity(
        cls,
        shots: int,
        result: Optional[Union[Result, ManagedResults]] = None,
        resultIdxList: Optional[list[int]] = None,
        times: int = 0,
        degree: int = None,
        
        counts: list[dict[str, int]] = [],
        **otherArgs,
    ) -> tuple[dict, dict]:
        """Computing specific quantity.
        Where should be overwritten by each construction of new measurement.

        Returns:
            tuple[dict, dict]:
                Counts, purity, entropy of experiment.
        """
        if resultIdxList == None:
            resultIdxList = [i for i in range(times)]
        elif isinstance(resultIdxList, list):
            if len(resultIdxList) > 1:
                ...
            elif len(resultIdxList) != times:
                raise ValueError(
                    f"The element number of 'resultIdxList': {len(resultIdxList)} is different with 'times': {times}.")
            else:
                raise ValueError(
                    f"The element number of 'resultIdxList': {len(resultIdxList)} needs to be more than 1 for 'haarMeasure'.")
        else:
            raise ValueError("'resultIdxList' needs to be 'list'.")

        purity = -100
        entropy = -100
        purityCellList = []

        Begin = time.time()

        print(f"| Calculating overlap ...", end="\r")
        if len(counts) < 1:
            for i in range(times):
                t1 = resultIdxList[i]
                print(
                    f"| Calculating overlap {t1} and {t1}" +
                    f" - {i+1}/{times} - {round(time.time() - Begin, 3)}s.", end="\r")

                try:    
                    allMeas1 = result.get_counts(t1)
                    counts.append(allMeas1)
                except IBMQManagedResultDataNotAvailable as err:
                    counts.append(None)
                    print("| Failed Job result skip, index:", i, err)
                    continue
        
        if (times == len(counts)):
            ...
        elif (times == 0):
            times == len(counts)
        else:
            times == len(counts)
            warnings.warn(f"times: {times} and counts number: {len(counts)} are different, use counts number.")

        for i in range(times):
            allMeas1 = counts[i]
            t1 = resultIdxList[i]
            purityCell = 0
            
            allMeasUnderDegree = dict.fromkeys(
                [k[:degree] for k in allMeas1], 0)
            for kMeas in list(allMeas1):
                allMeasUnderDegree[kMeas[:degree]] += allMeas1[kMeas]
            numAllMeasUnderDegree = len(allMeasUnderDegree)

            print(
                f"| Calculating overlap {t1} and {t1} " +
                f"by summarize {numAllMeasUnderDegree**2} values - {i+1}/{times}" +
                f" - {round(time.time() - Begin, 3)}s.", end="\r")
            for sAi, sAiMeas in allMeasUnderDegree.items():
                for sAj, sAjMeas in allMeasUnderDegree.items():
                    purityCell += cls.ensembleCell(
                        sAi, sAiMeas, sAj, sAjMeas, degree, shots)

            purityCellList.append(purityCell)
            print(
                f"| Calculating overlap end - {i+1}/{times}" +
                f" - {round(time.time() - Begin, 3)}s." +
                " "*30, end="\r")

        purity = np.mean(purityCellList)
        entropy = -np.log2(purity)
        quantity = {
            'purity': purity,
            'entropy': entropy,
            '_purityCellList': purityCellList,
        }
        return counts, quantity

    """ Main Process: Main Control"""

    def measure(
        self,
        wave: Union[QuantumCircuit, any, None] = None,
        degree: Optional[int] = None,
        times: int = 100,
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
            times=times,
            expsName=expsName,
            **otherArgs,
        )
