"""
================================================================
Second Renyi Entropy - Hadamard Test
(:mod:`qurry.qurrent.Hadamard`)
================================================================

"""
from pathlib import Path
from typing import Union, Optional, NamedTuple, Hashable, Iterable, Type, Any

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

from ..qurrium import (
    QurryV5Prototype,
    ExperimentPrototype,
    AnalysisPrototype,
    qubit_selector,
)
from .postprocess import hadamard_entangled_entropy


class EntropyHadamardAnalysis(AnalysisPrototype):
    __name__ = "qurrentHadamard.Analysis"
    shortName = "qurrent_hadamard.report"

    class AnalysisInput(NamedTuple):
        """To set the analysis."""

    class AnalysisContent(NamedTuple):
        """The content of the analysis."""

        purity: float
        """The purity of the system."""
        entropy: float
        """The entanglement entropy of the system."""

        def __repr__(self):
            return f"AnalysisContent(purity={self.purity}, entropy={self.entropy}, and others)"

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
            measure (tuple[int, int], optional):
                Measuring range on quantum circuits. Defaults to None.
            workers_num (Optional[int], optional):
                Number of multi-processing workers,
                if sets to 1, then disable to using multi-processing;
                if not specified, the use 3/4 of cpu counts by `round(cpu_count*3/4)`.
                Defaults to None.

        Returns:
            dict[str, float]: A dictionary contains
                purity, entropy, a list of each overlap, puritySD,
                purity of all system, entropy of all system,
                a list of each overlap in all system, puritySD of all system,
                degree, actual measure range,
                actual measure range in all system, bitstring range.
        """

        result = hadamard_entangled_entropy(
            shots=shots,
            counts=counts,
        )
        return result


class EntropyHadamardExperiment(ExperimentPrototype):
    __name__ = "qurrentHadamard.Experiment"
    shortName = "qurrent_hadamard.exp"

    class arguments(NamedTuple):
        """Arguments for the experiment."""

        expName: str = "exps"
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
                purity of all system, entropy of all system,
                a list of each overlap in all system, puritySD of all system,
                degree, actual measure range,
                actual measure range in all system, bitstring range.
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


class EntropyHadamardTest(QurryV5Prototype):
    """Hadamard test for entanglement entropy.

    - Which entropy:

        The entropy we compute is the Second Order Rényi Entropy.

    """

    __name__ = "qurrentHadamard"
    shortName = "qurrent_hadamard"

    @classmethod
    @property
    def experiment(cls) -> Type[EntropyHadamardExperiment]:
        """The container class responding to this QurryV5 class."""
        return EntropyHadamardExperiment

    def paramsControl(
        self,
        expName: str = "exps",
        waveKey: Hashable = None,
        degree: Union[tuple[int, int], int] = None,
        **otherArgs: any,
    ) -> tuple[
        EntropyHadamardExperiment.arguments,
        EntropyHadamardExperiment.commonparams,
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

        if isinstance(waveKey, (list, tuple)):
            waveKey = "-".join([str(i) for i in waveKey])

        expName = f"w={waveKey}.subsys=from{degree[0]}to{degree[1]}.{self.shortName}"

        return self.experiment.filter(
            expName=expName,
            waveKey=waveKey,
            degree=degree,
            **otherArgs,
        )

    def method(
        self,
        expID: str,
    ) -> list[QuantumCircuit]:
        """Returns a list of quantum circuits.

        Args:
            expID (str): The ID of the experiment.

        Returns:
            list[QuantumCircuit]: The quantum circuits.
        """

        assert expID in self.exps
        assert self.exps[expID].commons.expID == expID
        args: EntropyHadamardExperiment.arguments = self.exps[expID].args
        commons: EntropyHadamardExperiment.commonparams = self.exps[expID].commons
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
                wave=commons.waveKey,
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
            wave=wave,
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
