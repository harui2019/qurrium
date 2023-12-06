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
            measure (tuple[int, int], optional):
                Measuring range on quantum circuits. Defaults to None.
            workers_num (Optional[int], optional):
                Number of multi-processing workers,
                if sets to 1, then disable to using multi-processing;
                if not specified, the use 3/4 of cpu counts by `round(cpu_count*3/4)`.
                Defaults to None.

        Returns:
            dict[str, float]: A dictionary contains
                purity, entropy.
        """

        result = overlap_echo(
            shots=shots,
            counts=counts,
        )
        return result


class EchoHadamardExperiment(ExperimentPrototype):
    """The experiment for calculating entangled entropy with more information combined."""

    __name__ = "qurrechHadamard.Experiment"
    shortName = "qurrech_hadamard.exp"

    class Arguments(NamedTuple):
        """Arguments for the experiment."""

        exp_name: str = "exps"
        wave_key_2: Hashable = None
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
                purity, entropy.
        """

        shots = self.commons.shots
        counts = self.afterwards.counts

        qs = self.quantities(
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

    @classmethod
    def quantities(
        cls,
        shots: int = None,
        counts: list[dict[str, int]] = None,
    ) -> dict[str, float]:
        """Calculate entangled entropy with more information combined.

        Args:
            shots (int): Shots of the experiment on quantum machine.
            counts (list[dict[str, int]]): Counts of the experiment on quantum machine.

        Returns:
            dict[str, float]: A dictionary contains
                purity, entropy.
        """

        if shots is None or counts is None:
            raise ValueError("shots and counts should be specified.")

        return overlap_echo(
            shots=shots,
            counts=counts,
        )


class EchoHadamardTest(QurryV5Prototype):
    """The experiment for calculating entangled entropy with more information combined."""

    __name__ = "qurrentHadamard"
    shortName = "qurrech_hadamard"

    @classmethod
    @property
    def experiment(cls) -> Type[EchoHadamardExperiment]:
        """The container class responding to this QurryV5 class."""
        return EchoHadamardExperiment

    def params_control(
        self,
        wave_key: Hashable = None,
        wave_key_2: Union[Hashable, QuantumCircuit] = None,
        exp_name: str = "exps",
        degree: Union[tuple[int, int], int] = None,
        **other_kwargs: any,
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

            exp_name (str, optional):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.

            otherArgs (any):
                Other arguments.

        Returns:
            dict: The export will be processed in `.paramsControlCore`
        """
        # wave
        if isinstance(wave_key_2, QuantumCircuit):
            wave_key_2 = self.add(wave_key_2)
        elif isinstance(wave_key_2, Hashable):
            if wave_key_2 is None:
                ...
            elif not self.has(wave_key_2):
                raise KeyError(f"Wave '{wave_key_2}' not found in '.waves'")
        else:
            raise TypeError(
                f"'{wave_key_2}' is a '{type(wave_key_2)}' "
                + "instead of 'QuantumCircuit' or 'Hashable'"
            )

        num_qubits = self.waves[wave_key].num_qubits
        num_qubits_2 = self.waves[wave_key_2].num_qubits
        if num_qubits != num_qubits_2:
            raise ValueError(
                "The number of qubits of two wave functions must be the same, "
                + f"but {wave_key}: {num_qubits} != {wave_key_2}: {num_qubits_2}."
            )

        # measure and unitary location
        degree = qubit_selector(num_qubits, degree=degree)

        if isinstance(wave_key, (list, tuple)):
            wave_key = "-".join([str(i) for i in wave_key])
        if isinstance(wave_key_2, (list, tuple)):
            wave_key_2 = "-".join([str(i) for i in wave_key_2])

        exp_name = (
            f"w={wave_key}+{wave_key_2}.overlap="
            + f"from{degree[0]}to{degree[1]}.{self.shortName}"
        )

        return self.experiment.filter(
            exp_name=exp_name,
            wave_key=wave_key,
            wave_key2=wave_key_2,
            degree=degree,
            **other_kwargs,
        )

    def method(
        self,
        exp_id: str,
        _pbar: Optional[Any] = None,
    ) -> list[QuantumCircuit]:
        assert exp_id in self.exps
        assert self.exps[exp_id].commons.exp_id == exp_id
        args: EchoHadamardExperiment.Arguments = self.exps[exp_id].args
        commons: EchoHadamardExperiment.Commonparams = self.exps[exp_id].commons
        circuit = self.waves[commons.wave_key]
        num_qubits = circuit.num_qubits

        q_anc = QuantumRegister(1, "ancilla")
        q_func1 = QuantumRegister(num_qubits, "q1")
        q_func2 = QuantumRegister(num_qubits, "q2")
        c_meas1 = ClassicalRegister(1, "c1")
        qc_exp1 = QuantumCircuit(q_anc, q_func1, q_func2, c_meas1)

        qc_exp1.append(
            self.waves.call(
                wave=commons.wave_key,
            ),
            [q_func1[i] for i in range(num_qubits)],
        )

        qc_exp1.append(
            self.waves.call(
                wave=args.wave_key_2,
            ),
            [q_func2[i] for i in range(num_qubits)],
        )

        qc_exp1.barrier()
        qc_exp1.h(q_anc)
        for i in range(*args.degree):
            qc_exp1.cswap(q_anc[0], q_func1[i], q_func2[i])
        qc_exp1.h(q_anc)
        qc_exp1.measure(q_anc, c_meas1)

        return [qc_exp1]

    def measure(
        self,
        wave: Union[QuantumCircuit, any, None] = None,
        wave2: Union[QuantumCircuit, any, None] = None,
        degree: Union[int, tuple[int, int], None] = None,
        exp_name: str = "exps",
        *args,
        save_location: Optional[Union[Path, str]] = None,
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

            exp_name (str, optional):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.

            otherArgs (any):
                Other arguments.

        Returns:
            dict: The output.
        """

        id_now = self.result(
            wave=wave,  # First wave will be taken by _paramsControlMain
            wave_key_2=wave2,  # Second wave will be taken by paramsControl
            exp_name=exp_name,
            degree=degree,
            save_location=None,
            **otherArgs,
        )
        assert id_now in self.exps, f"ID {id_now} not found."
        assert self.exps[id_now].commons.exp_id == id_now
        current_exp = self.exps[id_now]

        if isinstance(save_location, (Path, str)):
            current_exp.write(
                save_location=save_location,
                mode=mode,
                indent=indent,
                encoding=encoding,
                jsonable=jsonablize,
            )

        return id_now
