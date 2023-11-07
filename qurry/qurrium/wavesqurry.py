from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.quantum_info import Operator

import time
import tqdm
import warnings
import numpy as np
from pathlib import Path
from typing import Union, Optional, NamedTuple, Hashable, Iterable, Type, overload, Any

from ..qurrium import (
    QurryV5Prototype,
    ExperimentPrototype,
    AnalysisPrototype,
)
from ..exceptions import QurryExperimentCountsNotCompleted
from ..tools import qurryProgressBar, ProcessManager, workers_distribution, DEFAULT_POOL_SIZE


class WavesQurryAnalysis(AnalysisPrototype):

    __name__ = 'WavesQurryAnalysis'

    class analysisInput(NamedTuple):
        """To set the analysis."""
        ultimate_question: str
        """ULtImAte QueStIoN."""
    class analysisContent(NamedTuple):
        utlmatic_answer: int
        """~The Answer to the Ultimate Question of Life, The Universe, and Everything.~"""
        dummy: int
        """Just a dummy field."""

    @property
    def default_side_product_fields(self) -> Iterable[str]:
        """The fields that will be stored as side product."""
        return ['dummy']


class WavesQurryExperiment(ExperimentPrototype):

    __name__ = 'WavesQurryExperiment'

    class arguments(NamedTuple):
        """Construct the experiment's parameters for specific options, which is overwritable by the inherition class."""
        expName: str = 'exps'
        waves: Iterable[Hashable] = []

    @classmethod
    @property
    def analysis_container(cls) -> Type[WavesQurryAnalysis]:
        return WavesQurryAnalysis

    @classmethod
    def quantities(cls,
                   shots: int,
                   counts: list[dict[str, int]],
                   ultimate_question: str = '',
                   **otherArgs) -> dict[str, float]:
        """Computing specific squantity.
        Where should be overwritten by each construction of new measurement.

        Returns:
            dict[str, float]: Counts, purity, entropy of experiment.
        """

        dummy = -100
        utlmatic_answer = 42,
        return {
            'dummy': dummy,
            'utlmatic_answer': utlmatic_answer,
        }

    def analyze(self,
                ultimate_question: str = '',
                shots: Optional[int] = None,
                **otherArgs):
        """Analysis of the experiment.
        Where should be overwritten by each construction of new measurement.
        """

        if shots is None:
            shots = self.commons.shots
        if len(self.afterwards.counts) < 1:
            raise QurryExperimentCountsNotCompleted(
                "The counts of the experiment is not completed. So there is no data to analyze."
            )

        qs = self.quantities(
            shots=shots,
            counts=self.afterwards.counts,
            ultimate_question=ultimate_question,
        )

        serial = len(self.reports)
        analysis = self.analysis_container(
            ultimate_question=ultimate_question,
            serial=serial,
            **qs,
        )

        self.reports[serial] = analysis
        return analysis


class WavesExecuter(QurryV5Prototype):

    @classmethod
    @property
    def experiment(cls) -> Type[WavesQurryExperiment]:
        """The container class responding to this QurryV5 class.
        """
        return WavesQurryExperiment

    def paramsControl(
        self,
        expName: str = 'exps',
        waveKey: Hashable = None,
        waves: Iterable[Hashable] = [],
        **otherArgs: Any
    ) -> tuple[WavesQurryExperiment.arguments, WavesQurryExperiment.commonparams, dict[str, Any]]:
        """Handling all arguments and initializing a single experiment.

        Args:
            waveKey (Union[QuantumCircuit, int, None], optional):
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
            otherArgs (Any):
                Other arguments.

        Returns:
            dict: The export will be processed in `.paramsControlCore`
        """

        for w in waves:
            if not self.has(w):
                raise ValueError(
                    f"| The wave '{w}' is not in `.waves`.")

        if len(waves) > 0:
            waveKey = None
        else:
            raise ValueError(
                f"| This is Qurry required multiple waves gvien in `waves` to be measured.")

        return self.experiment.filter(
            expName=expName,
            waveKey=waveKey,
            waves=waves,
            **otherArgs,
        )

    def method(
        self,
        expID: Hashable,
        _pbar: Optional[tqdm.tqdm] = None,
    ) -> list[QuantumCircuit]:

        assert expID in self.exps
        assert self.exps[expID].commons.expID == expID
        currentExp = self.exps[expID]
        args: WavesQurryExperiment.arguments = self.exps[expID].args
        commons: WavesQurryExperiment.commonparams = self.exps[expID].commons

        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str(
                f"Loading specified {len(args.waves)} circuits.")
        circs = [self.waves[c].copy() for c in args.waves]
        currentExp['expName'] = f"{args.expName}-with{len(circs)}circs"

        return circs

    def measure(
        self,
        waves: Iterable[Hashable] = [],
        expName: str = 'exps',
        *args,
        saveLocation: Optional[Union[Path, str]] = None,
        mode: str = 'w+',
        indent: int = 2,
        encoding: str = 'utf-8',
        jsonablize: bool = False,
        **otherArgs: Any
    ):
        """The main function to measure the wave function,
        which is the :meth:`result` with dedicated arguments.

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
            saveLocation (Optional[Union[Path, str]], optional):
                The location to save the experiment. If None, will not save.
                Defaults to None.
            mode (str, optional):
                The mode to open the file. Defaults to 'w+'.
            indent (int, optional):
                The indent of json file. Defaults to 2.
            encoding (str, optional):
                The encoding of json file. Defaults to 'utf-8'.
            jsonablize (bool, optional):
                Whether to jsonablize the experiment output. Defaults to False.

            otherArgs (Any):
                Other arguments in :meth:`result`.

        Returns:
            dict: The output.
        """

        IDNow = self.result(
            wave=None,
            waves=waves,
            expName=expName,
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
