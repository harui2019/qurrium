from qiskit import QuantumCircuit

import warnings
from pathlib import Path
from typing import Literal, Union, Optional, NamedTuple, Hashable, Iterable, Type, overload, Any

from ..qurrium import QurryV5Prototype, ExperimentPrototype, AnalysisPrototype

class EntropyRandomizedAnalysis(AnalysisPrototype):

    __name__ = 'qurrent.RandomizedAnalysis'

    class analysisInput(NamedTuple):
        """To set the analysis."""
        
        degree: tuple[int, int]
        
    class analysisContent(NamedTuple):
        """The content of the analysis."""
        
        purtiy: float
        """The purity of the system."""
        entropy: float
        purtiySD: float
        purityCellList: list[float]
        bitStringRange: tuple[int, int]
        
        purityAllSys: float
        entropyAllSys: float
        purityCellListAllSys: list[float]
        puritySDAllSys: float
        bitsStringRangeAllSys: tuple[int, int]
        
        # errorMitigatedPurity: float
        # errorMitigatedEntropy: float
        # errorMitigatedPuritySD: float
        # errorMitigatedPurityCellList: list[float]
        
        degree: tuple[int, int]
        measure: tuple[int, int]

    @property
    def default_side_product_fields(self) -> Iterable[str]:
        """The fields that will be stored as side product."""
        return [
            'purityCellList', 
            'purityCellListAllSys', 
            'errorMitigatedPurityCellList'
        ]


class EntropyRandomizedExperiment(ExperimentPrototype):
    
    __name__ = 'qurrient.RandomizedExperiment'
    
    class arguments(NamedTuple):
        """Arguments for the experiment."""
        expName: str = 'exps'
        wave: QuantumCircuit = None
        sampling: int = 100
        measure: tuple[int, int] = None
        unitary_set: tuple[int, int] = None
        
    @classmethod
    @property
    def analysis_container(cls) -> Type[EntropyRandomizedAnalysis]:
        """The container class responding to this QurryV5 class.
        """
        return EntropyRandomizedAnalysis

class EntropyRandomizedMeasure(QurryV5Prototype):
    
    __name__ = 'qurrent.Randomized'
    

    @classmethod
    @property
    def experiment(cls) -> Type[EntropyRandomizedExperiment]:
        """The container class responding to this QurryV5 class.
        """
        return EntropyRandomizedExperiment

    def paramsControl(
        self,
        expName: str = 'exps',
        wave: Optional[QuantumCircuit] = None,
        sampling: int = 1,
        **otherArgs: any
    ) -> tuple[EntropyRandomizedExperiment.arguments, EntropyRandomizedExperiment.commonparams, dict[str, Any]]:
        """Handling all arguments and initializing a single experiment.

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
            dict: The export will be processed in `.paramsControlCore`
        """

        if isinstance(sampling, int):
            ...
        else:
            sampling = 1
            warnings.warn(f"'{sampling}' is not an integer, use 1 as default")

        return self.experiment.filter(
            expName=expName,
            wave=wave,
            sampling=sampling,
            **otherArgs,
        )

    def method(self) -> list[QuantumCircuit]:

        assert self.lastExp is not None
        args: EntropyRandomizedExperiment.arguments = self.lastExp.args
        circuit = args.wave
        numQubits = circuit.num_qubits

        self.lastExp['expName'] = f"{args.expName}-{self.lastExp.commons.waveKey}-x{args.sampling}"
        print(
            f"| Directly call: {self.lastExp.commons.waveKey} with sampling {args.sampling} times.")

        return [circuit for i in range(args.sampling)]

    def measure(
        self,
        wave: Union[QuantumCircuit, any, None] = None,
        expsName: str = 'exps',
        sampling: int = 1,
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

            expsName (str, optional):
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
            expsName=expsName,
            sampling=sampling,
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
