from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

import time
import warnings
import numpy as np
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Union, Optional, NamedTuple, Hashable, Iterable, Type, overload, Any

from ..qurrium import (
    QurryV5Prototype,
    ExperimentPrototype,
    AnalysisPrototype,
    qubit_selector
)

def entangle_entropy(
    shots: int,
    counts: list[dict[str, int]],
) -> dict[str, float]:

    purity = -100
    entropy = -100
    onlyCount = counts[0]
    sample_shots = sum(onlyCount.values())
    assert sample_shots == shots, f"shots {shots} does not match sample_shots {sample_shots}"

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

class EntropyHadamardAnalysis(AnalysisPrototype):

    __name__ = 'qurrent.HadamardAnalysis'

    class analysisInput(NamedTuple):
        """To set the analysis."""
        shots: int

    class analysisContent(NamedTuple):
        """The content of the analysis."""
        # TODO: args hint

        purity: float
        """The purity of the system."""
        entropy: float
        """The entanglement entropy of the system."""

        def __repr__(self):
            return f"analysisContent(purity={self.purity}, entropy={self.entropy}, and others)"

    @property
    def default_side_product_fields(self) -> Iterable[str]:
        """The fields that will be stored as side product."""
        return []

    @classmethod
    def quantities(
        cls,
        shots: int,
        counts: list[dict[str, int]],
        measure: tuple[int, int] = None,
    ) -> dict[str, float]:
        """Calculate entangled entropy with more information combined.

        Args:
            shots (int): Shots of the experiment on quantum machine.
            counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
            degree (Union[tuple[int, int], int]): Degree of the subsystem.
            measure (tuple[int, int], optional): Measuring range on quantum circuits. Defaults to None.
            _workers_num (Optional[int], optional): 
                Number of multi-processing workers, 
                if sets to 1, then disable to using multi-processing;
                if not specified, the use 3/4 of cpu counts by `round(cpu_count*3/4)`.
                Defaults to None.

        Returns:
            dict[str, float]: A dictionary contains 
                purity, entropy, a list of each overlap, puritySD, 
                purity of all system, entropy of all system, a list of each overlap in all system, puritySD of all system,
                degree, actual measure range, actual measure range in all system, bitstring range.
        """

        result = entangle_entropy(
            shots=shots,
            counts=counts,
        )
        return result
    

class EntropyHadamardExperiment(ExperimentPrototype):

    __name__ = 'qurrent.HadamardExperiment'
    shortName = 'qurrent'

    class arguments(NamedTuple):
        """Arguments for the experiment."""
        expName: str = 'exps'
        times: int = 100
        degree: tuple[int, int] = None
        
    @classmethod
    @property
    def analysis_container(cls) -> Type[EntropyHadamardAnalysis]:
        """The container class responding to this QurryV5 class.
        """
        return EntropyHadamardAnalysis
    
    def analyze(
        self
    ) -> AnalysisPrototype:
        """Calculate entangled entropy with more information combined.

        Args:
            degree (Union[tuple[int, int], int]): Degree of the subsystem.
            _workers_num (Optional[int], optional): 
                Number of multi-processing workers, 
                if sets to 1, then disable to using multi-processing;
                if not specified, the use 3/4 of cpu counts by `round(cpu_count*3/4)`.
                Defaults to None.

        Returns:
            dict[str, float]: A dictionary contains 
                purity, entropy, a list of each overlap, puritySD, 
                purity of all system, entropy of all system, a list of each overlap in all system, puritySD of all system,
                degree, actual measure range, actual measure range in all system, bitstring range.
        """

        shots = self.commons.shots
        unitary_loc = self.args.unitary_loc
        counts = self.afterwards.counts

        qs = self.analysis_container.quantities(
            shots=shots,
            counts=counts,
        )

        serial = len(self.reports)
        analysis = self.analysis_container(
            serial=serial,
            shots=shots,
            **qs,
        )

        self.reports[serial] = analysis
        return analysis

class EntropyHadamardMeasure(QurryV5Prototype):

    __name__ = 'qurrent.Randomized'

    @classmethod
    @property
    def experiment(cls) -> Type[EntropyHadamardExperiment]:
        """The container class responding to this QurryV5 class.
        """
        return EntropyHadamardExperiment

    def paramsControl(
        self,
        expName: str = 'exps',
        waveKey: Hashable = None,
        degree: Union[tuple[int, int], int] = None,
        **otherArgs: any
    ) -> tuple[EntropyHadamardExperiment.arguments, EntropyHadamardExperiment.commonparams, dict[str, Any]]:
        """Handling all arguments and initializing a single experiment.

        Args:
            waveKey (Hashable):
                The index of the wave function in `self.waves` or add new one to calaculation,
                then choose one of waves as the experiment material.
                If input is `QuantumCircuit`, then add and use it.
                If input is the key in `.waves`, then use it.
                If input is `None` or something illegal, then use `.lastWave'.
                Defaults to None.

            expName (str, optional):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.

            otherArgs (any):
                Other arguments.

        Returns:
            dict: The export will be processed in `.paramsControlCore`
        """


        # measure and unitary location
        numQubits = self.waves[waveKey].num_qubits
        degree = qubit_selector(numQubits, degree=degree)

        expName = f"w={waveKey}-deg={degree[0]}-{degree[1]}.{self.shortName}"

        return self.experiment.filter(
            expName=expName,
            waveKey=waveKey,
            degree=degree,
            **otherArgs,
        )

    def method(self) -> list[QuantumCircuit]:

        assert self.lastExp is not None
        args: EntropyHadamardExperiment.arguments = self.lastExp.args
        commons: EntropyHadamardExperiment.commonparams = self.lastExp.commons
        circuit = self.waves[commons.waveKey]
        numQubits = circuit.num_qubits

        qAnc = QuantumRegister(1, 'ancilla')
        qFunc1 = QuantumRegister(numQubits, 'q1')
        qFunc2 = QuantumRegister(numQubits, 'q2')
        cMeas1 = ClassicalRegister(1, 'c1')
        qcExp1 = QuantumCircuit(qAnc, qFunc1, qFunc2, cMeas1)
        
        qcExp1.append(self.waves.call(
            wave=commons.waveKey,
        ), [qFunc1[i] for i in range(numQubits)])

        qcExp1.append(self.waves.call(
            wave=commons.waveKey,
        ), [qFunc2[i] for i in range(numQubits)])
        
        qcExp1.barrier()
        qcExp1.h(qAnc)
        for i in range(*args.degree):
            qcExp1.cswap(qAnc[0], qFunc1[i], qFunc2[i])
        qcExp1.h(qAnc)
        qcExp1.measure(qAnc, cMeas1)

        return [qcExp1]

    def measure(
        self,
        wave: Union[QuantumCircuit, any, None] = None,
        degree: Union[int, tuple[int, int], None] = None,
        expName: str = 'exps',
        *args,
        saveLocation: Optional[Union[Path, str]] = None,
        mode: str = 'w+',
        indent: int = 2,
        encoding: str = 'utf-8',
        jsonablize: bool = False,
        **otherArgs: any
    ):
        """

        Args:
            wave (Union[QuantumCircuit, int, None], optional):
                The index of the wave function in `self.waves` or add new one to calaculation,
                then choose one of waves as the experiment material.
                If input is `QuantumCircuit`, then add and use it.
                If input is the key in `.waves`, then use it.
                If input is `None` or something illegal, then use `.lastWave'.
                Defaults to None.

            expName (str, optional):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.

            otherArgs (any):
                Other arguments.

        Returns:
            dict: The output.
        """

        IDNow = self.result(
            wave=wave,
            expName=expName,
            degree=degree,
            saveLocation=None,
            **otherArgs,
        )
        assert IDNow == self.lastID
        assert self.lastExp is not None

        if isinstance(saveLocation, (Path, str)):
            self.lastExp.write(
                saveLocation=saveLocation,
                mode=mode,
                indent=indent,
                encoding=encoding,
                jsonablize=jsonablize,
            )

        return IDNow
