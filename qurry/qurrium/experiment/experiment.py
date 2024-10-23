"""
================================================================
The experiment prototype 
which is the basic class of all experiments.
(:mod:`qurry.qurrium.experiment.experiment`)
================================================================

"""

import gc
import os
import json
import warnings
from abc import abstractmethod, ABC
from typing import Union, Optional, Any, Type, Literal
from collections.abc import Hashable
from pathlib import Path
import tqdm

from qiskit import transpile, QuantumCircuit
from qiskit.providers import Backend, JobV1 as Job
from qiskit.transpiler.passmanager import PassManager

from .arguments import ArgumentsPrototype, Commonparams
from .beforewards import Before
from .afterwards import After
from .analyses import AnalysesContainer
from .export import Export
from .utils import (
    commons_dealing,
    exp_id_process,
    DEPRECATED_PROPERTIES,
    EXPERIMENT_UNEXPORTS,
)
from ..utils import get_counts_and_exceptions
from ..utils.qasm import qasm_dumps
from ..utils.iocontrol import RJUST_LEN
from ..utils.inputfixer import outfields_check, outfields_hint
from ..analysis import AnalysisPrototype
from ...tools import ParallelManager, DEFAULT_POOL_SIZE
from ...tools.datetime import DatetimeDict
from ...tools.progressbar import set_pbar_description
from ...tools.backend import GeneralSimulator
from ...tools.backend.utils import backend_name_getter
from ...capsule import jsonablize, quickJSON
from ...capsule.hoshi import Hoshi
from ...declare import BaseRunArgs, TranspileArgs
from ...exceptions import (
    QurryInvalidInherition,
    QurryResetSecurityActivated,
    QurryResetAccomplished,
    QurryProtectContent,
    QurrySummonerInfoIncompletion,
    QurryTranspileConfigurationIgnored,
)


class ExperimentPrototype(ABC):
    """The instance of experiment."""

    __name__ = "ExperimentPrototype"
    """Name of the QurryExperiment which could be overwritten."""

    @property
    @abstractmethod
    def arguments_instance(self) -> Type[ArgumentsPrototype]:
        """The arguments instance for this experiment."""
        raise NotImplementedError

    args: ArgumentsPrototype
    """The arguments of the experiment."""

    # analysis
    @property
    @abstractmethod
    def analysis_instance(self) -> Type[AnalysisPrototype]:
        """The analysis instance for this experiment."""
        raise NotImplementedError

    commons: Commonparams
    outfields: dict[str, Any]
    beforewards: Before
    afterwards: After

    def _implementation_check(self):
        """Check whether the experiment is implemented correctly."""
        duplicate_fields = set(self.args._fields) & set(self.commons._fields)
        if len(duplicate_fields) > 0:
            raise QurryInvalidInherition(
                f"{self.__name__}.arguments and {self.__name__}.commonparams "
                f"should not have same fields: {duplicate_fields}."
            )

    def __init__(
        self,
        arguments: Union[ArgumentsPrototype, dict[str, Any]],
        commonparams: Union[Commonparams, dict[str, Any]],
        outfields: dict[str, Any],
        beforewards: Optional[Before] = None,
        afterwards: Optional[After] = None,
        reports: Optional[AnalysesContainer] = None,
    ) -> None:
        """Initialize the experiment.

        Args:
            arguments (Optional[Union[NamedTuple, dict[str, Any]]], optional):
                The arguments of the experiment.
                Defaults to None.
            commonparams (Optional[Union[Commonparams, dict[str, Any]]], optional):
                The common parameters of the experiment.
                Defaults to None.
            outfields (Optional[dict[str, Any]], optional):
                The outfields of the experiment.
                Defaults to None.
            beforewards (Optional[Before], optional):
                The beforewards of the experiment.
                Defaults to None.
            afterwards (Optional[After], optional):
                The afterwards of the experiment.
                Defaults to None.
            reports (Optional[AnalysesContainer], optional):
                The reports of the experiment.
                Defaults to None.
        """
        if isinstance(arguments, self.arguments_instance):
            self.args = arguments
        elif isinstance(arguments, dict):
            self.args = self.arguments_instance(**arguments)
        else:
            raise TypeError(
                f"arguments should be {self.arguments_instance} or dict, not {type(arguments)}"
            )

        if isinstance(commonparams, Commonparams):
            self.commons = commonparams
        elif isinstance(commonparams, dict):
            self.commons = Commonparams(**commons_dealing(commonparams, self.analysis_instance))
        else:
            raise TypeError(
                f"commonparams should be {Commonparams} or dict, not {type(commonparams)}"
            )

        self._implementation_check()

        self.outfields = outfields
        self.beforewards = (
            beforewards
            if isinstance(beforewards, Before)
            else Before(
                target=[],
                target_qasm=[],
                circuit=[],
                circuit_qasm=[],
                fig_original=[],
                job_id="",
                exp_name=self.args.exp_name,
                side_product={},
            )
        )
        self.afterwards = (
            afterwards
            if isinstance(afterwards, After)
            else After(
                result=[],
                counts=[],
            )
        )
        self.reports = reports if isinstance(reports, AnalysesContainer) else AnalysesContainer()

        _summon_check = {
            "serial": self.commons.serial,
            "summoner_id": self.commons.summoner_id,
            "summoner_name": self.commons.summoner_name,
        }
        _summon_detect = any((v is not None) for v in _summon_check.values())
        _summon_fulfill = all((v is not None) for v in _summon_check.values())
        if _summon_detect:
            if not _summon_fulfill:
                summon_msg = Hoshi(ljust_description_len=20)
                summon_msg.newline(("divider",))
                summon_msg.newline(("h3", "Summoner Info Incompletion"))
                summon_msg.newline(("itemize", "Summoner info detect.", _summon_detect))
                summon_msg.newline(("itemize", "Summoner info fulfilled.", _summon_fulfill))
                for k, v in _summon_check.items():
                    summon_msg.newline(("itemize", k, str(v), f"fulfilled: {v is not None}", 2))
                warnings.warn(
                    "Summoner data is not completed, it will export in single experiment mode.",
                    category=QurrySummonerInfoIncompletion,
                )
                summon_msg.print()

        self.after_lock = False
        """Protect the :cls:`afterward` content to be overwritten. 
        When setitem is called and completed, it will be setted as `False` automatically.
        """
        self.mute_auto_lock = False
        """Whether mute the auto-lock message."""

    @classmethod
    @abstractmethod
    def params_control(
        cls, targets: list[tuple[Hashable, QuantumCircuit]], exp_name: str, **custom_kwargs: Any
    ) -> tuple[ArgumentsPrototype, Commonparams, dict[str, Any]]:
        """Control the experiment's parameters.

        Args:
            targets (list[tuple[Hashable, QuantumCircuit]]):
                The circuits of the experiment.
            exp_name (str):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
            custom_kwargs (Any):
                Other custom arguments.

        Raises:
            NotImplementedError: This method should be implemented.
        """

        raise NotImplementedError

    @classmethod
    def _params_control_core(
        cls,
        targets: list[tuple[Hashable, QuantumCircuit]],
        exp_id: Optional[str] = None,
        shots: int = 1024,
        backend: Optional[Backend] = None,
        exp_name: str = "experiment",
        run_args: Optional[Union[BaseRunArgs, dict[str, Any]]] = None,
        transpile_args: Optional[TranspileArgs] = None,
        # multimanager
        tags: Optional[tuple[str, ...]] = None,
        default_analysis: Optional[list[dict[str, Any]]] = None,
        serial: Optional[int] = None,
        summoner_id: Optional[Hashable] = None,
        summoner_name: Optional[str] = None,
        # process tool
        mute_outfields_warning: bool = False,
        pbar: Optional[tqdm.tqdm] = None,
        **custom_kwargs: Any,
    ):
        """Control the experiment's general parameters.

        Args:
            targets (list[tuple[Hashable, QuantumCircuit]]):
                The circuits of the experiment.
            exp_id (Optional[str], optional):
                If input is `None`, then create an new experiment.
                If input is a existed experiment ID, then use it.
                Otherwise, use the experiment with given specific ID.
                Defaults to None.
            shots (int, optional):
                Shots of the job. Defaults to `1024`.
            backend (Backend, optional):
                The quantum backend. Defaults to AerSimulator().
            exp_name (str, optional):
                The name of the experiment.
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'experiment'`.
            run_args (Optional[Union[BaseRunArgs, dict[str, Any]]], optional):
                Arguments for :func:`qiskit.execute`. Defaults to `{}`.
            transpile_args (Optional[TranspileArgs], optional):
                Arguments for :func:`qiskit.transpile`. Defaults to `{}`.
            tags (Optional[tuple[str, ...]], optional):
                Given the experiment multiple tags to make a dictionary for recongnizing it.
                Defaults to None.
            default_analysis (list[dict[str, Any]], optional):
                The analysis methods will be excuted after counts has been computed.
                Defaults to [].
            serial (Optional[int], optional):
                Index of experiment in a multiOutput.
                **!!ATTENTION, this should only be used by `Multimanager`!!**
                Defaults to None.
            summoner_id (Optional[Hashable], optional):
                ID of experiment of the multiManager.
                **!!ATTENTION, this should only be used by `Multimanager`!!**
                Defaults to None.
            summoner_name (Optional[str], optional):
                Name of experiment of the multiManager.
                **!!ATTENTION, this should only be used by `Multimanager`!!**
                _description_. Defaults to None.
            mute_outfields_warning (bool, optional):
                Mute the warning when there are unused arguments detected and stored in outfields.
                Defaults to False.
            pbar (Optional[tqdm.tqdm], optional):
                The progress bar for showing the progress of the experiment.
                Defaults to None.
            custom_kwargs (Any):
                Other custom arguments.

        Raises:
            TypeError: One of default_analysis is not a dict.
            ValueError: One of default_analysis is invalid.

        Returns:
            ExperimentPrototype: The experiment.
        """
        if run_args is None:
            run_args = {}
        if transpile_args is None:
            transpile_args = {}
        if default_analysis is None:
            default_analysis = []
        if backend is None:
            backend = GeneralSimulator()
        if tags is None:
            tags = ()

        # Given parameters and default parameters
        set_pbar_description(pbar, "Prepaing parameters...")

        checked_exp_id = exp_id_process(exp_id)
        arguments, commonparams, outfields = cls.params_control(
            targets=targets,
            exp_id=checked_exp_id,
            shots=shots,
            backend=backend,
            run_args=run_args,
            transpile_args=transpile_args,
            exp_name=exp_name,
            tags=tags,
            default_analysis=default_analysis,
            save_location=Path("./"),
            filename="",
            files={},
            serial=serial,
            summoner_id=summoner_id,
            summoner_name=summoner_name,
            datetimes=DatetimeDict(),
            **custom_kwargs,
        )

        outfield_maybe, outfields_unknown = outfields_check(
            outfields, arguments._fields + commonparams._fields
        )
        outfields_hint(outfield_maybe, outfields_unknown, mute_outfields_warning)

        set_pbar_description(pbar, "Create experiment instance... ")
        new_exps = cls(arguments, commonparams, outfields)

        if len(commonparams.default_analysis) > 0:
            for index, analyze_input in enumerate(commonparams.default_analysis):
                if not isinstance(analyze_input, dict):
                    raise TypeError(
                        "Each element of 'default_analysis' must be a dict, "
                        + f"not {type(analyze_input)}, for index {index} in 'default_analysis'"
                    )
                try:
                    new_exps.analysis_instance.input_filter(**analyze_input)
                except TypeError as e:
                    raise ValueError(
                        f'analysis input filter found index {index} in "default_analysis"'
                    ) from e

        assert isinstance(new_exps.commons.backend, Backend), "Require a valid backend."
        assert len(new_exps.beforewards.circuit) == 0, "New experiment should have no circuit."
        assert len(new_exps.beforewards.fig_original) == 0, "New experiment should have no figure."
        assert len(new_exps.beforewards.circuit_qasm) == 0, "New experiment should have no qasm."
        assert len(new_exps.afterwards.result) == 0, "New experiment should have no result."
        assert len(new_exps.afterwards.counts) == 0, "New experiment should have no counts."

        return new_exps

    @classmethod
    @abstractmethod
    def method(
        cls,
        targets: list[tuple[Hashable, QuantumCircuit]],
        arguments: ArgumentsPrototype,
        pbar: Optional[tqdm.tqdm] = None,
    ) -> tuple[list[QuantumCircuit], dict[str, Any]]:
        """The method to construct circuit.
        Where should be overwritten by each construction of new measurement.

        Args:
            targets (list[tuple[Hashable, QuantumCircuit]]):
                The circuits of the experiment.
            arguments (ArgumentsPrototype):
                The arguments of the experiment.
            pbar (Optional[tqdm.tqdm], optional):
                The progress bar for showing the progress of the experiment.
                Defaults to None.

        Returns:
            tuple[list[QuantumCircuit], dict[str, Any]]:
                The circuits of the experiment and the outfields.
        """
        raise NotImplementedError

    @classmethod
    def build(
        cls,
        targets: list[tuple[Hashable, QuantumCircuit]],
        shots: int = 1024,
        backend: Optional[Backend] = None,
        exp_name: str = "experiment",
        run_args: Optional[Union[BaseRunArgs, dict[str, Any]]] = None,
        transpile_args: Optional[TranspileArgs] = None,
        passmanager_pair: Optional[tuple[str, PassManager]] = None,
        tags: Optional[tuple[str, ...]] = None,
        # multimanager
        default_analysis: Optional[list[dict[str, Any]]] = None,
        serial: Optional[int] = None,
        summoner_id: Optional[Hashable] = None,
        summoner_name: Optional[str] = None,
        # process tool
        qasm_version: Literal["qasm2", "qasm3"] = "qasm3",
        export: bool = False,
        save_location: Optional[Union[Path, str]] = None,
        mode: str = "w+",
        indent: int = 2,
        encoding: str = "utf-8",
        jsonable: bool = False,
        pbar: Optional[tqdm.tqdm] = None,
        **custom_and_main_kwargs: Any,
    ):
        """Construct the experiment.

        Args:
            targets (list[tuple[Hashable, QuantumCircuit]]):
                The circuits of the experiment.
            shots (int, optional):
                Shots of the job. Defaults to `1024`.
            backend (Optional[Backend], optional):
                The quantum backend. Defaults to None.
            exp_name (str, optional):
                The name of the experiment.
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'experiment'`.
            run_args (Optional[Union[BaseRunArgs, dict[str, Any]]], optional):
                Arguments for :func:`qiskit.execute`. Defaults to `{}`.
            transpile_args (Optional[TranspileArgs], optional):
                Arguments for :func:`qiskit.transpile`. Defaults to `{}`.
            passmanager_pair (Optional[tuple[str, PassManager]], optional):
                The passmanager pair for transpile. Defaults to None.
            tags (Optional[tuple[str, ...]], optional):
                Given the experiment multiple tags to make a dictionary for recongnizing it.
                Defaults to None.

            default_analysis (list[dict[str, Any]], optional):
                The analysis methods will be excuted after counts has been computed.
                Defaults to [].
            serial (Optional[int], optional):
                Index of experiment in a multiOutput.
                **!!ATTENTION, this should only be used by `Multimanager`!!**
                Defaults to None.
            summoner_id (Optional[Hashable], optional):
                ID of experiment of the multiManager.
                **!!ATTENTION, this should only be used by `Multimanager`!!**
                Defaults to None.
            summoner_name (Optional[str], optional):
                Name of experiment of the multiManager.
                **!!ATTENTION, this should only be used by `Multimanager`!!**
                _description_. Defaults to None.

            qasm_version (Literal["qasm2", "qasm3"], optional):
                The export version of OpenQASM. Defaults to 'qasm3'.
            export (bool, optional):
                Whether to export the experiment. Defaults to False.
            save_location (Optional[Union[Path, str]], optional):
                The location to save the experiment. Defaults to None.
            mode (str, optional):
                The mode to open the file. Defaults to 'w+'.
            indent (int, optional):
                The indent of json file. Defaults to 2.
            encoding (str, optional):
                The encoding of json file. Defaults to 'utf-8'.
            jsonable (bool, optional):
                Whether to jsonablize the experiment output. Defaults to False.
            pbar (Optional[tqdm.tqdm], optional):
                The progress bar for showing the progress of the experiment.
                Defaults to None.
            custom_and_main_kwargs (Any):
                Other custom arguments.

        Returns:
            ExperimentPrototype: The experiment.
        """

        # preparing
        set_pbar_description(pbar, "Parameter loading...")

        current_exp = cls._params_control_core(
            targets=targets,
            shots=shots,
            backend=backend,
            run_args=run_args,
            transpile_args=transpile_args,
            tags=tags,
            exp_name=exp_name,
            default_analysis=default_analysis,
            serial=serial,
            summoner_id=summoner_id,
            summoner_name=summoner_name,
            pbar=pbar,
            **custom_and_main_kwargs,
        )
        if not isinstance(current_exp.commons.backend, Backend):
            if isinstance(backend, Backend):
                set_pbar_description(pbar, "Backend replacing...")
                current_exp.replace_backend(backend)
            else:
                raise ValueError(
                    "No vaild backend to run, exisited backend: "
                    + f"{current_exp.commons.backend} as type "
                    + f"{type(current_exp.commons.backend)}, "
                    + f"given backend: {backend} as type {type(backend)}."
                )
        assert isinstance(current_exp.commons.backend, Backend), (
            f"Invalid backend: {current_exp.commons.backend} as "
            + f"type {type(current_exp.commons.backend)}."
        )

        # circuit
        set_pbar_description(pbar, "Circuit creating...")

        for tk, tv in targets:
            current_exp.beforewards.target.append((tk, tv))
        cirqs, side_prodict = current_exp.method(
            targets=targets, arguments=current_exp.args, pbar=pbar
        )
        current_exp.beforewards.side_product.update(side_prodict)

        # qasm
        pool = ParallelManager()
        set_pbar_description(pbar, "Exporting OpenQASM string...")

        tmp_qasm = pool.starmap(qasm_dumps, [(q, qasm_version) for q in cirqs])
        for qasm_str in tmp_qasm:
            current_exp.beforewards.circuit_qasm.append(qasm_str)

        targets_keys, targets_values = zip(*targets)
        targets_keys: tuple[Hashable, ...]
        targets_values: tuple[QuantumCircuit, ...]

        tmp_target_qasm_items = zip(
            targets_keys, pool.starmap(qasm_dumps, [(q, qasm_version) for q in targets_values])
        )
        for tk, qasm_str in tmp_target_qasm_items:
            current_exp.beforewards.target_qasm.append((str(tk), qasm_str))

        # transpile
        if passmanager_pair is not None:
            passmanager_name, passmanager = passmanager_pair
            set_pbar_description(
                pbar, f"Circuit transpiling by passmanager '{passmanager_name}'..."
            )
            transpiled_circs = passmanager.run(circuits=cirqs)  # type: ignore
            if len(current_exp.commons.transpile_args) > 0:
                warnings.warn(
                    f"Passmanager '{passmanager_name}' is given, "
                    + f"the transpile_args will be ignored in '{current_exp.exp_id}'",
                    category=QurryTranspileConfigurationIgnored,
                )
        else:
            set_pbar_description(pbar, "Circuit transpiling...")
            transpiled_circs: list[QuantumCircuit] = transpile(
                cirqs,
                backend=current_exp.commons.backend,
                **current_exp.commons.transpile_args,
            )

        set_pbar_description(pbar, "Circuit loading...")
        for _w in transpiled_circs:
            current_exp.beforewards.circuit.append(_w)

        # commons
        datenote, date = current_exp.commons.datetimes.add_only("build")
        set_pbar_description(pbar, f"Building Completed, denoted '{datenote}' date: {date}...")

        if export:
            # export may be slow, consider export at finish or something
            if isinstance(save_location, (Path, str)):
                set_pbar_description(pbar, "Setup data exporting...")
                current_exp.write(
                    save_location=save_location,
                    mode=mode,
                    indent=indent,
                    encoding=encoding,
                    jsonable=jsonable,
                )

        return current_exp

    # local execution
    def run(
        self,
        new_backend: Optional[Backend] = None,
        revive: bool = False,
        replace_circuits: bool = False,
        pbar: Optional[tqdm.tqdm] = None,
    ) -> str:
        """Export the result after running the job.

        Args:
            new_backend (Optional[Backend], optional):
                The new backend for running the job. Defaults to None.
            revive (bool, optional):
                Whether to revive the circuit. Defaults to False.
            replace_circuits (bool, optional):
                Whether to replace the circuits during revive. Defaults to False.
            pbar (Optional[tqdm.tqdm], optional):
                The progress bar for showing the progress of the experiment.
                Defaults to None.

        Raises:
            ValueError: No circuit ready.
            ValueError: The circuit has not been constructed yet.

        Returns:
            str: The ID of the experiment.
        """
        if new_backend is not None:
            set_pbar_description(
                pbar, f"Backend replacing from {self.commons.backend} to {new_backend}..."
            )
            self.replace_backend(new_backend)

        if revive:
            datenote, date = self.commons.datetimes.add_serial("revive")
            set_pbar_description(pbar, f"Reviving, denoted '{datenote}' date: {date}...")
            self.beforewards.revive_circuit(replace_circuits)

        if len(self.beforewards.circuit) == 0:
            if len(self.beforewards.circuit_qasm) > 0:
                raise ValueError("No circuit ready, please revive the circuit first.")
            raise ValueError("The circuit has not been constructed yet.")

        assert isinstance(self.commons.backend, Backend), (
            f"Current backend {self.commons.backend} needs to be backend not "
            + f"{type({self.commons.backend})}."
        )
        assert hasattr(self.commons.backend, "run"), "Current backend is not runnable."

        set_pbar_description(pbar, "Executing...")
        event_name, date = self.commons.datetimes.add_serial("run")
        execution: Job = self.commons.backend.run(  # type: ignore
            self.beforewards.circuit,
            shots=self.commons.shots,
            **self.commons.run_args,
        )
        # commons
        set_pbar_description(pbar, f"Executing completed '{event_name}', denoted date: {date}...")
        # beforewards
        self["job_id"] = execution.job_id()
        # afterwards
        result = execution.result()
        self.afterwards.result.append(result)

        return self.exp_id

    def result(
        self,
        export: bool = False,
        save_location: Optional[Union[Path, str]] = None,
        mode: str = "w+",
        indent: int = 2,
        encoding: str = "utf-8",
        jsonable: bool = False,
        pbar: Optional[tqdm.tqdm] = None,
    ) -> str:
        """Export the result of the experiment.

        Args:
            export (bool, optional):
                Whether to export the experiment. Defaults to False.
            save_location (Optional[Union[Path, str]], optional):
                The location to save the experiment. Defaults to None.
            mode (str, optional):
                The mode to open the file. Defaults to 'w+'.
            indent (int, optional):
                The indent of json file. Defaults to 2.
            encoding (str, optional):
                The encoding of json file. Defaults to 'utf-8'.
            jsonable (bool, optional):
                Whether to jsonablize the experiment output. Defaults to False.
            pbar (Optional[tqdm.tqdm], optional):
                The progress bar for showing the progress of the experiment.
                Defaults to None.

        Returns:
            str: The ID of the experiment.
        """

        if len(self.afterwards.result) == 0:
            raise ValueError("The job has not been executed yet.")
        assert len(self.afterwards.result) == 1, "The job has been executed more than once."

        set_pbar_description(pbar, "Result loading...")
        num = len(self.beforewards.circuit)
        counts, exceptions = get_counts_and_exceptions(
            result=self.afterwards.result[-1],
            num=num,
        )
        if len(exceptions) > 0:
            if "exceptions" not in self.outfields:
                self.outfields["exceptions"] = {}
            for result_id, exception_item in exceptions.items():
                self.outfields["exceptions"][result_id] = exception_item

        set_pbar_description(pbar, "Counts loading...")
        for _c in counts:
            self.afterwards.counts.append(_c)

        if len(self.commons.default_analysis) > 0:
            for i, _analysis in enumerate(self.commons.default_analysis):
                set_pbar_description(
                    pbar, f"Default Analysis executing {i}/{len(self.commons.default_analysis)}..."
                )
                self.analyze(**_analysis)

        if export:
            # export may be slow, consider export at finish or something
            if isinstance(save_location, (Path, str)):
                set_pbar_description(pbar, "Setup data exporting...")
                self.write(
                    save_location=save_location,
                    mode=mode,
                    indent=indent,
                    encoding=encoding,
                    jsonable=jsonable,
                )

        return self.exp_id

    # remote execution
    def _remote_result_taking(
        self,
        counts_tmp_container: dict[int, dict[str, int]],
        summoner_id: str,
        idx_circs: list[int],
        retrieve_times_name: str,
    ) -> list[dict[str, int]]:
        """Take the result from remote execution.

        Args:
            counts_tmp_container (dict[int, dict[str, int]]):
                The counts temporary container.
            summoner_id (str):
                The summoner ID.
            idx_circs (list[int]):
                The index of circuits.
            retrieve_times_name (str):
                The retrieve times name.
            current (str):
                The current time.

        Returns:
            list[dict[str, int]]: The counts.
        """

        self.reset_counts(summoner_id=summoner_id)
        for idx in idx_circs:
            self.afterwards.counts.append(counts_tmp_container[idx])
        self.commons.datetimes.add_only(retrieve_times_name)
        return self.afterwards.counts

    # afterwards manual control
    def reset_counts(self, summoner_id: str) -> None:
        """Reset the counts of the experiment."""
        if summoner_id == self.commons.summoner_id:
            self.afterwards = self.afterwards._replace(counts=[])
            gc.collect()
        else:
            warnings.warn(
                "The summoner_id is not matched, "
                + "the counts will not be reset, it can only be activated by multimanager.",
                category=QurryResetSecurityActivated,
            )

    def replace_backend(self, backend: Backend) -> None:
        """Replace the backend of the experiment.

        Args:
            backend (Backend): The new backend.

        Raises:
            ValueError: If the new backend is not a valid backend.
            ValueError: If the new backend is not a runnable backend.
        """
        if not isinstance(backend, Backend):
            raise ValueError(f"Require a valid backend, but new backend: {backend} does not.")
        if not hasattr(backend, "run"):
            raise ValueError(f"Require a runnable backend, but new backend: {backend} does not.")

        old_backend = self.commons.backend
        old_backend_name = backend_name_getter(old_backend)
        new_backend_name = backend_name_getter(backend)
        self.commons.datetimes.add_serial(f"replace-{old_backend_name}-to-{new_backend_name}")
        self.commons = self.commons._replace(backend=backend)

    def unlock_afterward(self, mute_auto_lock: bool = False):
        """Unlock the :cls:`afterward` content to be overwritten.

        Args:
            mute_auto_lock (bool, optional):
                Mute anto-locked message for the unlock of this time. Defaults to False.
        """
        self.after_lock = True
        self.mute_auto_lock = mute_auto_lock

    def __setitem__(self, key, value) -> None:
        if key in self.beforewards._fields:
            self.beforewards = self.beforewards._replace(**{key: value})
        elif key in self.afterwards._fields:
            if self.after_lock and isinstance(self.after_lock, bool):
                self.afterwards = self.afterwards._replace(**{key: value})
            else:
                raise QurryProtectContent(
                    f"Can't set value to :cls:`afterward` field {key} "
                    + "because it's locked, use `.unlock_afterward()` "
                    + "to unlock before setting item ."
                )
        elif key in DEPRECATED_PROPERTIES:
            raise DeprecationWarning(f"{key} is deprecated.")
        else:
            raise ValueError(
                f"{key} is not a valid field of " + f"'{Before.__name__}' and '{After.__name__}'."
            )

        gc.collect()
        if self.after_lock is not False:
            self.after_lock = False
            if not self.mute_auto_lock:
                print(
                    "after_lock is locked automatically now, you can unlock by "
                    + "using `.unlock_afterward()` to set value to :cls:`afterward`."
                )
            self.mute_auto_lock = False

    def __getitem__(self, key) -> Any:
        if key in self.beforewards._fields:
            return getattr(self.beforewards, key)
        if key in self.afterwards._fields:
            return getattr(self.afterwards, key)
        if key in DEPRECATED_PROPERTIES:
            warnings.warn("This property is deprecated.", DeprecationWarning)
            return "Deprecated"
        raise ValueError(
            f"{key} is not a valid field of " + f"'{Before.__name__}' and '{After.__name__}'."
        )

    # analysis
    @classmethod
    @abstractmethod
    def quantities(cls) -> dict[str, Any]:
        """Computing specific squantity.
        Where should be overwritten by each construction of new measurement.
        """

    @abstractmethod
    def analyze(self) -> AnalysisPrototype:
        """Analyzing the example circuit results in specific method.
        Where should be overwritten by each construction of new measurement.

        Args:
            allArgs: all arguments will pass to `.quantities`.

        Returns:
            analysis: Analysis of the counts from measurement.
        """
        raise NotImplementedError

    def clear_analysis(self, *args, security: bool = False, mute: bool = False) -> None:
        """Reset the measurement and release memory.

        Args:
            args (any):
                Positional arguments handler to protect other keyword arguments.
                It's useless, umm...😐
            security (bool, optional): Security for reset. Defaults to `False`.
            mute (bool, optional): Mute the warning when reset activated. Defaults to `False`.
        """

        if security and isinstance(security, bool):
            self.reports = AnalysesContainer()
            gc.collect()
            if not mute:
                warnings.warn(
                    "The measurement has reset and release memory allocating.",
                    category=QurryResetAccomplished,
                )
        else:
            warnings.warn(
                "Reset does not execute to prevent executing accidentally, "
                + "if you are sure to do this, then use '.reset(security=True)'."
                + (
                    "Attention: any position arguments are not available on this method."
                    if len(args) > 0
                    else ""
                ),
                category=QurryResetSecurityActivated,
            )

    # show info
    def __hash__(self) -> int:
        return hash(self.commons.exp_id)

    @property
    def exp_id(self) -> str:
        """ID of experiment."""
        return self.commons.exp_id

    def __repr__(self) -> str:
        return (
            f"<{self.__name__}(exp_id={self.commons.exp_id}, "
            + f"{self.args.__repr__()}, "
            + f"{self.commons.__repr__()}, "
            + f"unused_args_num={len(self.outfields)}, "
            + f"analysis_num={len(self.reports)})>"
        )

    def _repr_no_id(self) -> str:
        return (
            f"<{self.__name__}("
            + f"{self.args}, "
            + f"{self.commons}, "
            + f"unused_args_num={len(self.outfields)}, "
            + f"analysis_num={len(self.reports)})>"
        )

    def _repr_pretty_(self, p, cycle):
        if cycle:
            p.text(
                f"<{self.__name__}(exp_id={self.commons.exp_id}, "
                + f"{self.args}, "
                + f"{self.commons}, "
                + f"unused_args_num={len(self.outfields)}, "
                + f"analysis_num={len(self.reports)})>"
            )
        else:
            with p.group(2, f"<{self.__name__}(", ")>"):
                p.text(f"exp_id={self.commons.exp_id}, ")
                p.breakable()
                p.text(f"{self.args},")
                p.breakable()
                p.text(f"{self.commons},")
                p.breakable()
                p.text(f"unused_args_num={len(self.outfields)},")
                p.breakable()
                p.text(f"analysis_num={len(self.reports)})")

    def statesheet(
        self,
        report_expanded: bool = False,
        hoshi: bool = False,
    ) -> Hoshi:
        """Show the state of experiment.

        Args:
            report_expanded (bool, optional): Show more infomation. Defaults to False.
            hoshi (bool, optional): Showing name of Hoshi. Defaults to False.

        Returns:
            Hoshi: Statesheet of experiment.
        """

        info = Hoshi(
            [
                ("h1", f"{self.__name__} with exp_id={self.commons.exp_id}"),
            ],
            name="Hoshi" if hoshi else "QurryExperimentSheet",
        )
        info.newline(("itemize", "arguments"))
        for k, v in self.args._asdict().items():
            info.newline(("itemize", str(k), str(v), "", 2))

        info.newline(("itemize", "commonparams"))
        for k, v in self.commons._asdict().items():
            info.newline(
                (
                    "itemize",
                    str(k),
                    str(v),
                    (
                        ""
                        if k != "exp_id"
                        else "This is ID is generated by Qurry "
                        + "which is different from 'job_id' for pending."
                    ),
                    2,
                )
            )

        info.newline(
            (
                "itemize",
                "outfields",
                len(self.outfields),
                "Number of unused arguments.",
                1,
            )
        )
        for k, v in self.outfields.items():
            info.newline(("itemize", str(k), v, "", 2))

        info.newline(("itemize", "beforewards"))
        for k, v in self.beforewards._asdict().items():
            if isinstance(v, str):
                info.newline(("itemize", str(k), str(v), "", 2))
            else:
                info.newline(("itemize", str(k), len(v), f"Number of {k}", 2))

        info.newline(("itemize", "afterwards"))
        for k, v in self.afterwards._asdict().items():
            if k == "job_id":
                info.newline(
                    (
                        "itemize",
                        str(k),
                        str(v),
                        "If it's null meaning this experiment "
                        + "doesn't use online backend like IBMQ.",
                        2,
                    )
                )
            elif isinstance(v, str):
                info.newline(("itemize", str(k), str(v), "", 2))
            else:
                info.newline(("itemize", str(k), len(v), f"Number of {k}", 2))

        info.newline(("itemize", "reports", len(self.reports), "Number of analysis.", 1))
        if report_expanded:
            for ser, item in self.reports.items():
                info.newline(
                    (
                        "itemize",
                        "serial",
                        f"k={ser}, serial={item.header.serial}",
                        None,
                        2,
                    )
                )
                info.newline(("txt", item, 3))

        return info

    def export(
        self,
        save_location: Optional[Union[Path, str]] = None,
        export_transpiled_circuit: bool = False,
    ) -> Export:
        """Export the data of experiment.

        For the `.write` function actually exports 4 different files
        respecting to `adventure`, `legacy`, `tales`, and `reports` like:

        ```python
        files = {
            'folder': './blabla_experiment/',
            'qurryinfo': './blabla_experiment/qurryinfo.json',

            'args': './blabla_experiment/args/blabla_experiment.id={exp_id}.args.json',
            'advent': './blabla_experiment/advent/blabla_experiment.id={exp_id}.advent.json',
            'legacy': './blabla_experiment/legacy/blabla_experiment.id={exp_id}.legacy.json',
            'tales.dummyx1': './blabla_experiment/tales/blabla_experiment.id={exp_id}.dummyx1.json',
            'tales.dummyx2': './blabla_experiment/tales/blabla_experiment.id={exp_id}.dummyx2.json',
            ...
            'tales.dummyxn': './blabla_experiment/tales/blabla_experiment.id={exp_id}.dummyxn.json',
            'reports': ./blabla_experiment/reports/blabla_experiment.id={exp_id}.reports.json,
            'reports.tales.dummyz1':
                './blabla_experiment/tales/blabla_experiment.id={exp_id}.dummyz1.reports.json',
            'reports.tales.dummyz2':
                './blabla_experiment/tales/blabla_experiment.id={exp_id}.dummyz2.reports.json',
            ...
            'reports.tales.dummyzm':
                './blabla_experiment/tales/blabla_experiment.id={exp_id}.dummyzm.reports.json',
        }
        ```
        which `blabla_experiment` is the example filename.
        If this experiment is called by :cls:`multimanager`,
        then the it will be named after `` as known as the name of :cls:`multimanager`.

        ```python
        files = {
            'folder': './BLABLA_project/',
            'qurryinfo': './BLABLA_project/qurryinfo.json',

            'args': './BLABLA_project/args/index={serial}.id={exp_id}.args.json',
            'advent': './BLABLA_project/advent/index={serial}.id={exp_id}.advent.json',
            'legacy': './BLABLA_project/legacy/index={serial}.id={exp_id}.legacy.json',
            'tales.dummyx1': './BLABLA_project/tales/index={serial}.id={exp_id}.dummyx1.json',
            'tales.dummyx2': './BLABLA_project/tales/index={serial}.id={exp_id}.dummyx2.json',
            ...
            'tales.dummyxn': './BLABLA_project/tales/index={serial}.id={exp_id}.dummyxn.json',
            'reports': ./BLABLA_project/reports/index={serial}.id={exp_id}.reports.json,
            'reports.tales.dummyz1':
                './BLABLA_project/tales/index={serial}.id={exp_id}.dummyz1.reports.json',
            'reports.tales.dummyz2':
                './BLABLA_project/tales/index={serial}.id={exp_id}.dummyz2.reports.json',
            ...
            'reports.tales.dummyzm':
                './BLABLA_project/tales/index={serial}.id={exp_id}.dummyzm.reports.json',
        }
        ```
        which `BLBLA_project` is the example :cls:`multimanager` name
        stored at :prop:`commonparams.`.
        At this senerio, the `exp_name` will never apply as filename.

        - reports formats.

        ```
        reports = {
            1: { ...quantities, 'input': { ... }, 'header': { ... }, },
            2: { ...quantities, 'input': { ... }, 'header': { ... }, },
            ...
            {serial}: { ...quantities, 'input': { ... }, 'header': { ... }, },
        }
        ```

        - tales_reports formats.

        ```
        tales_reports = {
            'dummyz1': {
                1: { ... },
                2: { ... },
                ...
                {serial}: { ... },
            },
            'dummyz2': {
                1: { ... },
                2: { ... },
                ...
                {serial}: { ... },
            },
            ...
            'dummyz': {
                1: { ... },
                2: { ... },
                ...
                {serial}: { ... },
            },
        }
        ```

        Returns:
            Export: A namedtuple containing the data of experiment
                which can be more easily to export as json file.
        """
        if isinstance(save_location, Path):
            ...
        elif isinstance(save_location, str):
            save_location = Path(save_location)
        elif save_location is None:
            save_location = Path(self.commons.save_location)
            if self.commons.save_location is None:
                raise ValueError("save_location is None, please provide a valid save_location")
        else:
            raise TypeError(f"save_location must be Path or str, not {type(save_location)}")

        if self.commons.save_location != save_location:
            self.commons = self.commons._replace(save_location=save_location)

        adventures, tales = self.beforewards.export(
            unexports=EXPERIMENT_UNEXPORTS,
            export_transpiled_circuit=export_transpiled_circuit,
        )
        legacy = self.afterwards.export(unexports=EXPERIMENT_UNEXPORTS)
        reports, tales_reports = self.reports.export()

        # filename
        filename = ""
        folder = ""

        # multi-experiment mode
        if all(
            (v is not None)
            for v in [
                self.commons.serial,
                self.commons.summoner_id,
                self.commons.summoner_id,
            ]
        ):
            folder += f"./{self.commons.summoner_name}/"
            filename += f"index={self.commons.serial}.id={self.commons.exp_id}"
        else:
            repeat_times = 1
            tmp = (
                folder + f"./{self.beforewards.exp_name}.{str(repeat_times).rjust(RJUST_LEN, '0')}/"
            )
            while os.path.exists(tmp):
                repeat_times += 1
                tmp = (
                    folder
                    + f"./{self.beforewards.exp_name}."
                    + f"{str(repeat_times).rjust(RJUST_LEN, '0')}/"
                )
            folder = tmp
            filename += (
                f"{self.beforewards.exp_name}."
                + f"{str(repeat_times).rjust(RJUST_LEN, '0')}.id={self.commons.exp_id}"
            )

        self.commons = self.commons._replace(filename=filename)
        files = {
            "folder": folder,
            "qurryinfo": folder + "qurryinfo.json",
            "args": folder + f"args/{filename}.args.json",
            "advent": folder + f"advent/{filename}.advent.json",
            "legacy": folder + f"legacy/{filename}.legacy.json",
        }
        for k in tales:
            files[f"tales.{k}"] = folder + f"tales/{filename}.{k}.json"
        files["reports"] = folder + f"reports/{filename}.reports.json"
        for k in tales_reports:
            files[f"reports.tales.{k}"] = folder + f"tales/{filename}.{k}.reports.json"

        return Export(
            exp_id=str(self.commons.exp_id),
            exp_name=str(self.beforewards.exp_name),
            serial=(None if self.commons.serial is None else int(self.commons.serial)),
            summoner_id=(None if self.commons.summoner_id else str(self.commons.summoner_id)),
            summoner_name=(None if self.commons.summoner_name else str(self.commons.summoner_name)),
            filename=str(filename),
            files={k: str(Path(v)) for k, v in files.items()},
            args=jsonablize(self.args._asdict()),
            commons=self.commons.export(),
            outfields=jsonablize(self.outfields),
            adventures=jsonablize(adventures),
            legacy=jsonablize(legacy),
            tales=jsonablize(tales),
            reports=reports,
            tales_reports=tales_reports,
        )

    def write(
        self,
        save_location: Optional[Union[Path, str]] = None,
        mode: str = "w+",
        indent: int = 2,
        encoding: str = "utf-8",
        jsonable: bool = False,
        export_transpiled_circuit: bool = False,
        _pbar: Optional[tqdm.tqdm] = None,
        _qurryinfo_hold_access: Optional[str] = None,
    ) -> tuple[str, dict[str, str]]:
        """Export the experiment data, if there is a previous export, then will overwrite.

        - example of filename:

        ```python
        files = {
            'folder': './blabla_experiment/',
            'qurrtinfo': './blabla_experiment/qurrtinfo',

            'args': './blabla_experiment/args/blabla_experiment.id={exp_id}.args.json',
            'advent': './blabla_experiment/advent/blabla_experiment.id={exp_id}.advent.json',
            'legacy': './blabla_experiment/legacy/blabla_experiment.id={exp_id}.legacy.json',
            'tales.dummyx1': './blabla_experiment/tales/blabla_experiment.id={exp_id}.dummyx1.json',
            'tales.dummyx2': './blabla_experiment/tales/blabla_experiment.id={exp_id}.dummyx2.json',
            ...
            'tales.dummyxn': './blabla_experiment/tales/blabla_experiment.id={exp_id}.dummyxn.json',
            'reports': ./blabla_experiment/reports/blabla_experiment.id={exp_id}.reports.json,
            'reports.tales.dummyz1':
                './blabla_experiment/tales/blabla_experiment.id={exp_id}.dummyz1.reports.json',
            'reports.tales.dummyz2':
                './blabla_experiment/tales/blabla_experiment.id={exp_id}.dummyz2.reports.json',
            ...
            'reports.tales.dummyzm':
                './blabla_experiment/tales/blabla_experiment.id={exp_id}.dummyzm.reports.json',
        }
        ```

        Args:
            save_location (Optional[Union[Path, str]], optional):
                Where to save the export content as `json` file.
                If `save_location == None`, then use the value in `self.commons` to be exported,
                if it's None too, then raise error.
                Defaults to `None`.

            mode (str):
                Mode for :func:`open` function, for :func:`mori.quickJSON`. Defaults to 'w+'.
            indent (int, optional):
                Indent length for json, for :func:`mori.quickJSON`. Defaults to 2.
            encoding (str, optional):
                Encoding method, for :func:`mori.quickJSON`. Defaults to 'utf-8'.
            jsonable (bool, optional):
                Whether to transpile all object to jsonable via :func:`mori.jsonablize`,
                for :func:`mori.quickJSON`. Defaults to False.
            mute (bool, optional):
                Whether to mute the output, for :func:`mori.quickJSON`. Defaults to False.
            _qurryinfo_hold_access (str, optional):
                Whether to hold the I/O of `qurryinfo`, then export by :cls:`multimanager`,
                it should be control by :cls:`multimanager`.
                Defaults to None.

        Returns:
            tuple[str, dict[str, str]]: The id of the experiment and the files location.
        """
        if _pbar is not None:
            _pbar.set_description_str("Preparing to export...")

        # experiment write
        export_material = self.export(
            save_location=save_location,
            export_transpiled_circuit=export_transpiled_circuit,
        )
        exp_id, files = export_material.write(
            mode=mode,
            indent=indent,
            encoding=encoding,
            jsonable=jsonable,
            _pbar=_pbar,
        )
        assert "qurryinfo" in files, "qurryinfo location is not in files."
        # qurryinfo write
        real_save_location = Path(self.commons.save_location)
        if (
            _qurryinfo_hold_access == self.commons.summoner_id
            and self.commons.summoner_id is not None
        ):
            ...
        elif os.path.exists(real_save_location / export_material.files["qurryinfo"]):
            with open(
                real_save_location / export_material.files["qurryinfo"],
                "r",
                encoding="utf-8",
            ) as f:
                qurryinfo_found: dict[str, dict[str, str]] = json.load(f)
                content = {**qurryinfo_found, **{exp_id: files}}

            quickJSON(
                content=content,
                filename=str(real_save_location / files["qurryinfo"]),
                mode=mode,
                indent=indent,
                encoding=encoding,
                jsonable=jsonable,
                mute=True,
            )
        else:
            quickJSON(
                content={exp_id: files},
                filename=str(real_save_location / files["qurryinfo"]),
                mode=mode,
                indent=indent,
                encoding=encoding,
                jsonable=jsonable,
                mute=True,
            )

        del export_material
        gc.collect()

        return exp_id, files

    @classmethod
    def _read_core(
        cls,
        exp_id: str,
        file_index: dict[str, str],
        save_location: Union[Path, str] = Path("./"),
        encoding: str = "utf-8",
    ) -> "ExperimentPrototype":
        """Core of read function.

        Args:
            exp_id (str): The id of the experiment to be read.
            file_index (dict[str, str]): The index of the experiment to be read.
            save_location (Union[Path, str]): The location of the experiment to be read.
            encoding (str): Encoding method, for :func:`mori.quickJSON`.

        Raises:
            ValueError: 'save_location' needs to be the type of 'str' or 'Path'.
            FileNotFoundError: When `save_location` is not available.

        Returns:
            QurryExperiment: The experiment to be read.
        """

        if isinstance(save_location, (Path, str)):
            save_location = Path(save_location)
        else:
            raise ValueError("'save_location' needs to be the type of 'str' or 'Path'.")
        if not os.path.exists(save_location):
            raise FileNotFoundError(f"'save_location' does not exist, '{save_location}'.")

        # Construct the experiment
        # arguments, commonparams, outfields
        export_material_set = {}
        (
            export_material_set["arguments"],
            export_material_set["commonparams"],
            export_material_set["outfields"],
        ) = Commonparams.read_with_arguments(
            exp_id=exp_id,
            file_index=file_index,
            save_location=save_location,
            encoding=encoding,
        )
        exp_instance = cls(
            export_material_set["arguments"],
            export_material_set["commonparams"],
            export_material_set["outfields"],
            beforewards=Before.read(
                file_index=file_index, save_location=save_location, encoding=encoding
            ),
            afterwards=After.read(
                file_index=file_index, save_location=save_location, encoding=encoding
            ),
            reports=AnalysesContainer(),
        )

        reports_read = exp_instance.analysis_instance.read(
            file_index=file_index,
            save_location=save_location,
            encoding=encoding,
        )
        for k, v in reports_read.items():
            exp_instance.reports[k] = v

        return exp_instance

    @classmethod
    def _read_core_wrapper(
        cls,
        args: tuple[str, dict[str, str], Union[Path, str], str],
    ) -> "ExperimentPrototype":
        """Wrapper of :func:`_read_core` for multiprocessing.

        Args:
            args (tuple[str, dict[str, str], Union[Path, str], str]):
                exp_id, file_index, save_location, encoding.

        Returns:
            QurryExperiment: The experiment to be read.
        """
        assert isinstance(args[1], dict), (
            "file_index should be dict, " + f"but we get {type(args[1])}, {args[1]}."
        )
        return cls._read_core(*args)

    @classmethod
    def read(
        cls,
        name_or_id: Union[Path, str],
        save_location: Union[Path, str] = Path("./"),
        encoding: str = "utf-8",
        workers_num: Optional[int] = None,
    ) -> list:
        """Read the experiment from file.
        Replacement of :func:`QurryV4().readLegacy`

        Args:
            name_or_id (Union[Path, str]):
                The name or id of the experiment to be read.
            save_location (Union[Path, str], optional):
                The location of the experiment to be read.
                Defaults to Path('./').
            indent (int, optional):
                Indent length for json, for :func:`mori.quickJSON`. Defaults to 2.
            encoding (str, optional):
                Encoding method, for :func:`mori.quickJSON`. Defaults to 'utf-8'.

        Raises:
            ValueError: 'save_location' needs to be the type of 'str' or 'Path'.
            FileNotFoundError: When `save_location` is not available.

        Returns:
            list: The list of the experiments to be read.
        """

        if isinstance(save_location, (Path, str)):
            save_location = Path(save_location)
        else:
            raise ValueError("'save_location' needs to be the type of 'str' or 'Path'.")
        if not os.path.exists(save_location):
            raise FileNotFoundError(f"'save_location' does not exist, '{save_location}'.")

        export_location = save_location / name_or_id
        if not os.path.exists(export_location):
            raise FileNotFoundError(f"'ExportLoaction' does not exist, '{export_location}'.")

        qurryinfo: dict[str, dict[str, str]] = {}
        qurryinfo_location = export_location / "qurryinfo.json"
        if not os.path.exists(qurryinfo_location):
            raise FileNotFoundError(
                f"'qurryinfo.json' does not exist at '{save_location}'. "
                + "It's required for loading all experiment data."
            )

        with open(qurryinfo_location, "r", encoding=encoding) as f:
            qurryinfo_found: dict[str, dict[str, str]] = json.load(f)
            qurryinfo = {**qurryinfo_found, **qurryinfo}

        if workers_num is None:
            workers_num = DEFAULT_POOL_SIZE
        pool = ParallelManager(workers_num)

        quene = pool.process_map(
            cls._read_core,
            [
                (exp_id, file_index, save_location, encoding)
                for exp_id, file_index in qurryinfo.items()
            ],
            desc=f"{len(qurryinfo)} experiments found, loading by {workers_num} workers.",
        )

        return quene
