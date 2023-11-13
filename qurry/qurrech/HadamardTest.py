from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

import numpy as np
from pathlib import Path
from typing import Union, Optional, NamedTuple, Hashable, Iterable, Type, Any

from ..qurrium import (
    QurryV5Prototype,
    ExperimentPrototype,
    AnalysisPrototype,
    qubit_selector,
)


def overlap_echo(
    shots: int,
    counts: list[dict[str, int]],
) -> dict[str, float]:
    echo = -100
    onlyCount = counts[0]
    sample_shots = sum(onlyCount.values())
    assert (
        sample_shots == shots
    ), f"shots {shots} does not match sample_shots {sample_shots}"

    isZeroInclude = "0" in onlyCount
    isOneInclude = "1" in onlyCount
    if isZeroInclude and isOneInclude:
        echo = (onlyCount["0"] - onlyCount["1"]) / shots
    elif isZeroInclude:
        echo = onlyCount["0"] / shots
    elif isOneInclude:
        echo = onlyCount["1"] / shots
    else:
        echo = np.Nan
        raise Warning("Expected '0' and '1', but there is no such keys")

    quantity = {
        "echo": echo,
    }
    return quantity


class EntropyHadamardAnalysis(AnalysisPrototype):
    __name__ = "qurrechHadamard.Analysis"
    shortName = "qurrech_hadamard.report"

    class AnalysisInput(NamedTuple):
        """To set the analysis."""

    class AnalysisContent(NamedTuple):
        """The content of the analysis."""

        echo: float
        """The purity of the system."""

        def __repr__(self):
            return f"AnalysisContent(echo={self.echo}, and others)"

    @property
    def default_side_product_fields(self) -> Iterable[str]:
        """The fields that will be stored as side product."""
        return []

    @classmethod
    def quantities(
        cls,
        shots: int,
        counts: list[dict[str, int]],
    ) -> dict[str, float]:
        """Calculate entangled entropy with more information combined.

        Args:
            shots (int): Shots of the experiment on quantum machine.
            counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
            degree (Union[tuple[int, int], int]): Degree of the subsystem.
            measure (tuple[int, int], optional): Measuring range on quantum circuits. Defaults to None.
            workers_num (Optional[int], optional):
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

        result = overlap_echo(
            shots=shots,
            counts=counts,
        )
        return result


class EchoHadamardExperiment(ExperimentPrototype):
    __name__ = "qurrechHadamard.Experiment"
    shortName = "qurrech_hadamard.exp"

    class Arguments(NamedTuple):
        """Arguments for the experiment."""

        expName: str = "exps"
        waveKey2: Hashable = None
        degree: tuple[int, int] = None

    @classmethod
    @property
    def analysis_container(cls) -> Type[EntropyHadamardAnalysis]:
        """The container class responding to this QurryV5 class."""
        return EntropyHadamardAnalysis

    def analyze(self) -> AnalysisPrototype:
        """Calculate entangled entropy with more information combined.

        Args:
            degree (Union[tuple[int, int], int]): Degree of the subsystem.
            workers_num (Optional[int], optional):
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


class EchoHadamardTest(QurryV5Prototype):
    __name__ = "qurrentHadamard"
    shortName = "qurrech_hadamard"

    @classmethod
    @property
    def experiment(cls) -> Type[EchoHadamardExperiment]:
        """The container class responding to this QurryV5 class."""
        return EchoHadamardExperiment

    def params_control(
        self,
        waveKey: Hashable = None,
        waveKey2: Union[Hashable, QuantumCircuit] = None,
        expName: str = "exps",
        degree: Union[tuple[int, int], int] = None,
        **otherArgs: any,
    ) -> tuple[
        EchoHadamardExperiment.Arguments,
        EchoHadamardExperiment.Commonparams,
        dict[str, Any],
    ]:
        """Handling all arguments and initializing a single experiment.

        Args:
            wave (Hashable):
                The index of the wave function in `self.waves` or add new one to calaculation,
                then choose one of waves as the experiment material.
                If input is `QuantumCircuit`, then add and use it.
                If input is the key in `.waves`, then use it.
                If input is `None` or something illegal, then use `.lastWave'.
                Defaults to None.

            wave2 (Hashable):
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
        # wave
        if isinstance(waveKey2, QuantumCircuit):
            waveKey2 = self.add(waveKey2)
        elif isinstance(waveKey2, Hashable):
            if waveKey2 is None:
                ...
            elif not self.has(waveKey2):
                raise KeyError(f"Wave '{waveKey2}' not found in '.waves'")
        else:
            raise TypeError(
                f"'{waveKey2}' is a '{type(waveKey2)}' instead of 'QuantumCircuit' or 'Hashable'"
            )

        numQubits = self.waves[waveKey].num_qubits
        numQubits2 = self.waves[waveKey2].num_qubits
        if numQubits != numQubits2:
            raise ValueError(
                f"The number of qubits of two wave functions must be the same, but {waveKey}: {numQubits} != {waveKey2}: {numQubits2}."
            )

        # measure and unitary location
        degree = qubit_selector(numQubits, degree=degree)

        if isinstance(waveKey, (list, tuple)):
            waveKey = "-".join([str(i) for i in waveKey])
        if isinstance(waveKey2, (list, tuple)):
            waveKey2 = "-".join([str(i) for i in waveKey2])

        expName = f"w={waveKey}+{waveKey2}.overlap=from{degree[0]}to{degree[1]}.{self.shortName}"

        return self.experiment.filter(
            expName=expName,
            waveKey=waveKey,
            waveKey2=waveKey2,
            degree=degree,
            **otherArgs,
        )

    def method(
        self,
        expID: str,
    ) -> list[QuantumCircuit]:
        assert expID in self.exps
        assert self.exps[expID].commons.expID == expID
        args: EchoHadamardExperiment.Arguments = self.exps[expID].args
        commons: EchoHadamardExperiment.Commonparams = self.exps[expID].commons
        circuit = self.waves[commons.waveKey]
        numQubits = circuit.num_qubits

        qAnc = QuantumRegister(1, "ancilla")
        qFunc1 = QuantumRegister(numQubits, "q1")
        qFunc2 = QuantumRegister(numQubits, "q2")
        cMeas1 = ClassicalRegister(1, "c1")
        qcExp1 = QuantumCircuit(qAnc, qFunc1, qFunc2, cMeas1)

        qcExp1.append(
            self.waves.call(
                wave=commons.waveKey,
            ),
            [qFunc1[i] for i in range(numQubits)],
        )

        qcExp1.append(
            self.waves.call(
                wave=args.waveKey2,
            ),
            [qFunc2[i] for i in range(numQubits)],
        )

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
        wave2: Union[QuantumCircuit, any, None] = None,
        degree: Union[int, tuple[int, int], None] = None,
        expName: str = "exps",
        *args,
        saveLocation: Optional[Union[Path, str]] = None,
        mode: str = "w+",
        indent: int = 2,
        encoding: str = "utf-8",
        jsonablize: bool = False,
        **otherArgs: any,
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
            wave=wave,  # First wave will be taken by _paramsControlMain
            waveKey2=wave2,  # Second wave will be taken by paramsControl
            expName=expName,
            degree=degree,
            saveLocation=None,
            **otherArgs,
        )
        assert IDNow in self.exps, f"ID {IDNow} not found."
        assert self.exps[IDNow].commons.expID == IDNow
        currentExp = self.exps[IDNow]

        if isinstance(saveLocation, (Path, str)):
            currentExp.write(
                saveLocation=saveLocation,
                mode=mode,
                indent=indent,
                encoding=encoding,
                jsonable=jsonablize,
            )

        return IDNow
