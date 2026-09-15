"""ExperimentPrototype - The instance of experiment (:mod:`qurry.qurrium.experiment.experiment`)"""

import os
import warnings
from abc import abstractmethod, ABC
from typing import Any, Generic
from pathlib import Path
from dataclasses import replace
import tqdm

from qiskit import QuantumCircuit
from qiskit.providers import Backend, JobV1 as Job
from qiskit.transpiler.passmanager import PassManager

from .beforewards import Before
from .tales import Tales
from .afterwards import After
from .export import Export, QurryInfo
from .utils import (
    exp_id_process,
    memory_usage_factor_expect,
    implementation_check,
    summonner_check,
    process_transpilation,
    make_statesheet,
    create_save_location,
    decide_folder_and_filename,
    ensure_runnable_backend,
)
from ..container import WCKeyable, RunArgsType, TranspileArgs
from ..analysis import AnalysesContainer, _R
from ..arguments import Commonparams, _A, create_all_arguments
from ..utils import (
    get_counts_and_exceptions,
    outfields_check,
    outfields_hint,
    qasm_dumps,
    AvailableQASMVersions,
)
from ..utils.file_structure import is_old_v7_file_structure
from ..exceptions import ResetSecurityActivated
from ...tools import (
    very_easy_chunk_size,
    DatetimeDict,
    set_pbar_description,
    backend_name_getter,
    DEFAULT_POOL_SIZE,
    make_multiprocess_pool,
    qurry_progressbar,
    GeneralSimulator,
)
from ...capsule import Hoshi, DEFAULT_INDENT


class ExperimentPrototype(ABC, Generic[_A, _R]):
    """The instance of experiment."""

    __name__ = "ExperimentPrototype"
    """Name of the QurryExperiment which could be overwritten."""

    @classmethod
    @abstractmethod
    def arguments_type(cls) -> type[_A]:
        """The arguments type for this experiment."""
        raise NotImplementedError("This method should be implemented.")

    @property
    def arguments_instance(self) -> type[_A]:
        """The arguments instance for this experiment."""
        return self.arguments_type()

    @classmethod
    @abstractmethod
    def analysis_type(cls) -> type[_R]:
        """The analysis type for this experiment."""
        raise NotImplementedError("This method should be implemented.")

    @property
    def analysis_instance(self) -> type[_R]:
        """The analysis instance for this experiment."""
        return self.analysis_type()

    @classmethod
    def side_product_type(cls) -> type[Tales]:
        """The side product container type for this experiment."""
        return Tales

    @property
    def side_product_instance(self) -> type[Tales]:
        """The side product container instance for this experiment."""
        return self.side_product_type()

    @property
    def is_auto_analysis(self) -> bool:
        """Check if the experiment has auto analysis,
        which means no postprocess and no middleware entries needed.

        Returns:
            bool: True if the experiment has auto analysis, False otherwise.
        """
        return self.analysis_type().is_auto_analysis()

    @property
    def is_hold_by_multimanager(self) -> bool:
        """Check if the experiment is hold by a multimanager.

        Returns:
            bool: True if the experiment is hold by a multimanager, False otherwise.
        """
        return summonner_check(
            self.commons.serial, self.commons.summoner_id, self.commons.summoner_name
        )

    args: _A
    """The arguments of the experiment."""
    commons: Commonparams
    """The common parameters of the experiment."""
    outfields: dict[str, Any]
    """The outfields of the experiment."""
    beforewards: Before
    """The beforewards of the experiment."""
    afterwards: After
    """The afterwards of the experiment."""
    memory_usage_factor: int = -1
    """The factor of the memory usage of the experiment.
    When the experiment is created, it will be set to -1 for no measurement yet.
    When the experiment is built, it will be set to the memory usage of the experiment.

    The memory usage is estimated by the number of instructions in the circuits and
    the number of shots. The factor is calculated by the formula:

    .. code-block:: text

        factor = target_circuit_instructions_num + sqrt(shots) * target_circuit_instructions_num

    where `target_circuit_instructions_num` is the number of instructions in the target circuits,
    `transpiled_circuit_instructions_num` is the number of instructions in the circuits
    which has been transpiled and will be run on the backend,
    and `shots` is the number of shots.

    The factor is rounded to the nearest integer.
    The factor is used to estimate the memory usage of the experiment.
    """

    def __init__(
        self,
        arguments: _A | dict[str, Any],
        commonparams: Commonparams | dict[str, Any],
        outfields: dict[str, Any],
        beforewards: Before | None = None,
        side_products: Tales | None = None,
        afterwards: After | None = None,
        reports: AnalysesContainer[_R] | None = None,
    ) -> None:
        """Initialize the experiment.

        Args:
            arguments (_A | dict[str, Any]):
                The arguments of the experiment.
            commonparams (Commonparams | dict[str, Any]):
                The common parameters of the experiment.
            outfields (dict[str, Any]):
                The outfields of the experiment.
            beforewards (Before | None, optional):
                The beforewards of the experiment. Defaults to None.
            side_products (Tales | None, optional):
                The side products of the experiment. Defaults to None.
            afterwards (After | None, optional):
                The afterwards of the experiment. Defaults to None.
            reports (AnalysesContainer[_R] | None, optional):
                The reports of the experiment. Defaults to None.
        """
        self.args, self.commons, self.outfields = create_all_arguments(
            arguments, commonparams, outfields, self.arguments_instance
        )
        implementation_check(self.__name__, self.args, self.commons)
        summonner_check(self.commons.serial, self.commons.summoner_id, self.commons.summoner_name)

        self.beforewards = Before.create(beforewards)
        self.afterwards = After.create(afterwards)
        self.side_products = (
            self.side_product_instance(side_products.items())
            if side_products is not None
            else self.side_product_instance()
        )
        self.reports: AnalysesContainer[_R] = AnalysesContainer.create(
            reports, analysis_instance=self.analysis_instance
        )
        """The reports of the experiment."""

    @classmethod
    @abstractmethod
    def params_control(
        cls, targets: list[tuple[WCKeyable, QuantumCircuit]], exp_name: str, **custom_kwargs: Any
    ) -> tuple[_A, Commonparams, dict[str, Any]]:
        """Control the experiment's parameters.

        Args:
            targets (list[tuple[WCKeyable, QuantumCircuit]]): The circuits of the experiment.
            exp_name (str):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
            custom_kwargs (Any): Other custom arguments.

        Raises:
            NotImplementedError: This method should be implemented.
        """

        raise NotImplementedError("This method should be implemented.")

    @classmethod
    def _params_control_core(
        cls,
        targets: list[tuple[WCKeyable, QuantumCircuit]],
        exp_id: str | None = None,
        shots: int = 1024,
        backend: Backend | None = None,
        exp_name: str = "experiment",
        run_args: RunArgsType = None,
        transpile_args: TranspileArgs | None = None,
        # multimanager
        tags: tuple[str, ...] | None = None,
        serial: int | None = None,
        summoner_id: str | None = None,
        summoner_name: str | None = None,
        # process tool
        mute_outfields_warning: bool = False,
        pbar: tqdm.tqdm | None = None,
        **custom_kwargs: Any,
    ):
        """Control the experiment's general parameters.

        Args:
            targets (list[tuple[WCKeyable, QuantumCircuit]]): The circuits of the experiment.
            exp_id (str | None, optional):
                If input is `None`, then create an new experiment.
                If input is a existed experiment ID, then use it.
                Otherwise, use the experiment with given specific ID.
                Defaults to None.
            shots (int, optional): Shots of the job. Defaults to `1024`.
            backend (Backend | None, optional): The quantum backend. Defaults to None.
            exp_name (str, optional):
                The name of the experiment.
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'experiment'`.
            run_args (RunArgsType, optional):
                Arguments for :meth:`Backend.run`. Defaults to None.
            transpile_args (TranspileArgs | None, optional):
                Arguments of :func:`~qiskit.compiler.transpile`.
                Defaults to None.
            tags (tuple[str, ...] | None, optional):
                Given tags for the experiment to describe it.
                Defaults to None.
            serial (int | None, optional):
                Index of experiment in
                :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`.
                **!!ATTENTION, this should only be used by
                :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`!!**
                Defaults to None.
            summoner_id (str | None, optional):
                ID of experiment of
                :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`.
                **!!ATTENTION, this should only be used by
                :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`!!**
                Defaults to None.
            summoner_name (str | None, optional):
                Name of experiment of
                :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`.
                **!!ATTENTION, this should only be used by
                :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`!!**
                Defaults to None.
            mute_outfields_warning (bool, optional):
                Mute the warning when there are unused arguments detected and stored in outfields.
                Defaults to False.
            pbar (tqdm.tqdm | None, optional):
                The progress bar for showing the progress of the experiment.
                Defaults to None.
            custom_kwargs (Any):
                Other custom arguments.

        Returns:
            ExperimentPrototype: The experiment.
        """
        if run_args is None:
            run_args = {}
        if transpile_args is None:
            transpile_args = {}
        if backend is None:
            backend = GeneralSimulator()
        if tags is None:
            tags = ()

        # Given parameters and default parameters
        set_pbar_description(pbar, "Prepaing parameters...")

        arguments, commonparams, outfields = cls.params_control(
            targets=targets,
            exp_id=exp_id_process(exp_id),
            shots=shots,
            backend=backend,
            run_args=run_args,
            transpile_args=transpile_args,
            exp_name=exp_name,
            tags=tags,
            save_location=Path("./"),
            serial=serial,
            summoner_id=summoner_id,
            summoner_name=summoner_name,
            datetimes=DatetimeDict(),
            **custom_kwargs,
        )

        outfield_maybe, outfields_unknown = outfields_check(
            outfields, arguments.fields + commonparams.fields
        )
        outfields_hint(outfield_maybe, outfields_unknown, mute_outfields_warning)

        set_pbar_description(pbar, "Create experiment instance... ")
        new_exps = cls(arguments, commonparams, outfields)

        assert isinstance(new_exps.commons.backend, Backend), "Require a valid backend."
        assert len(new_exps.beforewards.circuit) == 0, "New experiment should have no circuit."
        assert len(new_exps.beforewards.circuit_qasm) == 0, "New experiment should have no qasm."
        assert len(new_exps.afterwards.result) == 0, "New experiment should have no result."
        assert len(new_exps.afterwards.counts) == 0, "New experiment should have no counts."

        return new_exps

    @classmethod
    @abstractmethod
    def method(
        cls, targets: list[tuple[WCKeyable, QuantumCircuit]], arguments: _A
    ) -> tuple[list[QuantumCircuit], dict[str, Any]]:
        """The method to construct circuit.
        Where should be overwritten by each construction of new measurement.

        Args:
            targets (list[tuple[WCKeyable, QuantumCircuit]]): The circuits of the experiment.
            arguments (_Arg): The arguments of the experiment.

        Returns:
            tuple[list[QuantumCircuit], dict[str, Any]]:
                The circuits of the experiment and the outfields.
        """
        raise NotImplementedError("This method should be implemented.")

    @classmethod
    def build(
        cls,
        targets: list[tuple[WCKeyable, QuantumCircuit]],
        shots: int = 1024,
        backend: Backend | None = None,
        exp_name: str = "experiment",
        run_args: RunArgsType = None,
        transpile_args: TranspileArgs | None = None,
        passmanager_pair: tuple[str, PassManager] | None = None,
        tags: tuple[str, ...] | None = None,
        # multimanager
        serial: int | None = None,
        summoner_id: str | None = None,
        summoner_name: str | None = None,
        # process tool
        qasm_version: AvailableQASMVersions = "qasm3",
        export: bool = False,
        save_location: Path | str | None = None,
        pbar: tqdm.tqdm | None = None,
        multiprocess: bool = True,
        **custom_and_main_kwargs: Any,
    ):
        """Construct the experiment.

        Args:
            targets (list[tuple[WCKeyable, QuantumCircuit]]): The circuits of the experiment.
            shots (int, optional): Shots of the job. Defaults to `1024`.
            backend (Backend | None, optional): The quantum backend. Defaults to None.
            exp_name (str, optional):
                The name of the experiment.
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'experiment'`.
            run_args (RunArgsType, optional):
                Arguments for :meth:`Backend.run`. Defaults to None.
            transpile_args (TranspileArgs | None, optional):
                Arguments of :func:`~qiskit.compiler.transpile`.
                Defaults to None.
            passmanager_pair (tuple[str, PassManager] | None, optional):
                The passmanager pair for transpile. Defaults to None.
            tags (tuple[str, ...] | None, optional):
                Given tags for the experiment to describe it.
                Defaults to None.

            serial (int | None, optional):
                Index of experiment in
                :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`.
                **!!ATTENTION, this should only be used by
                :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`!!**
                Defaults to None.
            summoner_id (str | None, optional):
                ID of experiment of
                :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`.
                **!!ATTENTION, this should only be used by
                :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`!!**
                Defaults to None.
            summoner_name (str | None, optional):
                Name of experiment of
                :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`.
                **!!ATTENTION, this should only be used by
                :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`!!**
                Defaults to None.

            qasm_version (AvailableQASMVersions, optional):
                The export version of OpenQASM. Defaults to 'qasm3'.
            export (bool, optional):
                Whether to export the experiment. Defaults to False.
            save_location (Path | str | None, optional):
                The location to save the experiment. Defaults to None.
            pbar (tqdm.tqdm | None, optional):
                The progress bar for showing the progress of the experiment.
                Defaults to None.
            multiprocess (bool, optional):
                Whether to use multiprocessing. Defaults to `True`.

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
            serial=serial,
            summoner_id=summoner_id,
            summoner_name=summoner_name,
            pbar=pbar,
            **custom_and_main_kwargs,
        )
        assert isinstance(current_exp.commons.backend, Backend), (
            f"Invalid backend: {current_exp.commons.backend} as "
            + f"type {type(current_exp.commons.backend)}. "
            + "This should be ensure in the function '_params_control_core'."
        )

        # circuit
        set_pbar_description(pbar, "Creating circuits...")
        current_exp.beforewards.target.extend(targets)
        circs, side_prodict = current_exp.method(targets, current_exp.args)
        current_exp.side_products.update(side_prodict)

        # qasm
        set_pbar_description(pbar, "Exporting OpenQASM string...")
        current_exp.beforewards.circuit_qasm.extend(
            qasm_dumps(circ, qasm_version) for circ in circs
        )
        current_exp.beforewards.target_qasm.extend(
            (str(key), qasm_dumps(circ, qasm_version)) for key, circ in targets
        )

        # transpile
        set_pbar_description(pbar, "Transpiling circuits...")
        transpiled_circs = process_transpilation(
            circs,
            current_exp.commons.transpile_args.copy(),
            current_exp.commons.backend,
            passmanager_pair,
            current_exp.exp_id,
            multiprocess=multiprocess,
            pbar=pbar,
        )
        current_exp.beforewards.circuit.extend(transpiled_circs)

        # memory usage factor
        current_exp.memory_usage_factor = memory_usage_factor_expect(
            target=current_exp.beforewards.target,
            circuits=current_exp.beforewards.circuit,
            commonparams=current_exp.commons,
        )

        # commons
        note_and_date = current_exp.commons.datetimes.add_only("build")
        set_pbar_description(
            pbar, f"Building Completed, denoted '{note_and_date[0]}' date: {note_and_date[1]}..."
        )

        # export may be slow, consider export at finish or something
        if isinstance(save_location, (Path, str)) and export:
            set_pbar_description(pbar, "Setup data exporting...")
            current_exp.write(save_location=save_location)

        return current_exp

    @classmethod
    def build_for_multiprocess(cls, config: dict[str, Any]):
        """Build wrapper for multiprocess.

        Args:
            config (dict[str, Any]): The arguments of the experiment.

        Returns:
            ExperimentPrototype: The experiment.
        """

        config.pop("multiprocess", None)
        config.pop("pbar", None)
        config["multiprocess"] = False
        return cls.build(**config), config

    # local execution
    def run(self, pbar: tqdm.tqdm | None = None) -> str:
        """Export the result after running the job.

        Args:
            pbar (tqdm.tqdm | None, optional):
                The progress bar for showing the progress of the experiment. Defaults to None.

        Returns:
            str: The ID of the experiment.
        """
        if len(self.beforewards.circuit) == 0:
            raise ValueError("The circuit has not been constructed yet.")

        ensure_runnable_backend(self.commons.backend)
        assert isinstance(self.commons.backend, Backend), "Backend should be ensured at this point."

        set_pbar_description(pbar, "Executing...")
        event_name, date = self.commons.datetimes.add_serial("run")
        execution: Job = self.commons.backend.run(  # type: ignore
            self.beforewards.circuit, shots=self.commons.shots, **self.commons.run_args
        )
        # commons
        set_pbar_description(pbar, f"Executing completed '{event_name}', denoted date: {date}...")
        # beforewards
        self.beforewards.job_id.append(execution.job_id())
        # afterwards
        result = execution.result()
        self.afterwards.result.append(result)

        return self.exp_id

    def result(
        self,
        export: bool = False,
        save_location: Path | str | None = None,
        pbar: tqdm.tqdm | None = None,
    ) -> str:
        """Export the result of the experiment.

        Args:
            export (bool, optional): Whether to export the experiment. Defaults to False.
            save_location (Path | str | None, optional):
                The location to save the experiment. Defaults to None.
            pbar (tqdm.tqdm | None, optional):
                The progress bar for showing the progress of the experiment. Defaults to None.

        Returns:
            str: The ID of the experiment.
        """

        if len(self.afterwards.result) == 0:
            raise ValueError("The job has not been executed yet.")
        assert len(self.afterwards.result) == 1, "The job has been executed more than once."

        set_pbar_description(pbar, "Result loading...")
        counts, exceptions = get_counts_and_exceptions(
            result=self.afterwards.result[-1], num=len(self.beforewards.circuit)
        )
        if len(exceptions) > 0:
            self.outfields["exceptions"] = {**self.outfields.get("exceptions", {}), **exceptions}
        set_pbar_description(pbar, "Counts loading...")
        self.afterwards.counts.extend(counts)

        if self.is_auto_analysis:
            if self.is_hold_by_multimanager:
                set_pbar_description(
                    pbar,
                    "Auto running analysis will take over by "
                    f"{self.commons.summoner_id}: "
                    f"{self.commons.summoner_name} after all experiments are done.",
                )
            else:
                set_pbar_description(pbar, "Running analysis for no input required...")
                self.analyze()

        if isinstance(save_location, (Path, str)) and export:
            # export may be slow, consider export at finish or something
            set_pbar_description(pbar, "Setup data exporting...")
            self.write(save_location=save_location)

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
            counts_tmp_container (dict[int, dict[str, int]]): The counts temporary container.
            summoner_id (str): The summoner ID.
            idx_circs (list[int]): The index of circuits.
            retrieve_times_name (str): The retrieve times name.
            current (str): The current time.

        Returns:
            list[dict[str, int]]: The counts.
        """
        if summoner_id == self.commons.summoner_id:
            self.afterwards.counts.clear()
            self.afterwards.result.clear()
            for idx in idx_circs:
                self.afterwards.counts.append(counts_tmp_container[idx])
            self.commons.datetimes.add_only(retrieve_times_name)
        else:
            warnings.warn(
                f"Summoner ID {summoner_id} is not equal to"
                + f" current summoner ID {self.commons.summoner_id}. "
                + "The counts will not be updated.",
                category=ResetSecurityActivated,
            )
        return self.afterwards.counts

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
        self.commons = replace(self.commons, backend=backend)

    @abstractmethod
    def analyze(self) -> _R:
        """Analyzing the example circuit results in specific method.
        Where should be overwritten by each construction of new measurement.

        If the analysis requires additional parameters,
        they should be passed as arguments to this method.
        Also, they should be defined in the
        :meth:`~qurry.qurrium.analysis.AnalysisPrototype.input_type`
        for :meth:`result` will count the input fields from the analysis to determine
        whether to call this method for no input required.

        Returns:
            _R: The result of the analysis.
        """
        raise NotImplementedError("This method should be implemented.")

    # show info
    def __hash__(self) -> int:
        return hash(self.commons.exp_id)

    @property
    def exp_id(self) -> str:
        """ID of experiment."""
        return self.commons.exp_id

    def __repr__(self) -> str:
        return (
            f'<{self.__name__}(exp_id="{self.commons.exp_id}", '
            + f"args={self.args}, "
            + f"commons={self.commons}, "
            + f"unused_args_num={len(self.outfields)}, "
            + f"analysis_num={len(self.reports)})>"
        )

    def _repr_short(self) -> str:
        # pylint: disable=protected-access
        return (
            f"<{self.__name__}("
            + f"args={self.args._repr_short()}, "
            + f"commons={self.commons._repr_short()}, "
            + f"unused_args_num={len(self.outfields)}, "
            + f"analysis_num={len(self.reports)})>"
        )
        # pylint: enable=protected-access

    def _repr_pretty_(self, p, cycle):
        if cycle:
            # pylint: disable=protected-access
            p.text(self._repr_short())
            # pylint: enable=protected-access
            return

        basic_info = {
            "exp_id": self.commons.exp_id,
            "args": self.args,
            "commons": self.commons,
            "unused_args_num": len(self.outfields),
            "analysis_num": len(self.reports),
        }
        with p.group(DEFAULT_INDENT, f"<{self.__name__}(", ")>"):
            for i, (k, v) in enumerate(basic_info.items()):
                p.breakable()
                p.text(f"{k}=")
                p.pretty(v)
                if i != len(basic_info) - 1:
                    p.text(",")

    def statesheet(self, report_expanded: bool = False, hoshi: bool = False) -> Hoshi:
        """Show the state of experiment.

        Args:
            report_expanded (bool, optional): Show more infomation. Defaults to False.
            hoshi (bool, optional): Showing name of Hoshi. Defaults to False.

        Returns:
            Hoshi: Statesheet of experiment.
        """

        return make_statesheet(
            exp_name=self.__name__,
            args=self.args,
            commons=self.commons,
            outfields=self.outfields,
            beforewards=self.beforewards,
            afterwards=self.afterwards,
            reports=self.reports,
            report_expanded=report_expanded,
            hoshi=hoshi,
        )

    def export(
        self,
        save_location: Path | str | None = None,
        export_transpiled_circuit: bool = False,
    ) -> Export:
        """Export the data of experiment into specific namedtuples for exporting.

        Args:
            save_location (Path | str | None, optional):
                The location to save the experiment. Defaults to None.
            export_transpiled_circuit (bool, optional):
                Whether to export the transpiled circuit as txt. Defaults to False.
                When set to True, the transpiled circuit will be exported as txt.
                Otherwise, the circuit will be not exported but circuit qasm remains.

        Returns:
            Export: A namedtuple containing the data of experiment
                which can be more easily exported as a json file.
        """
        save_location = create_save_location(save_location, self.commons)
        if self.commons.save_location != save_location:
            self.commons = replace(self.commons, save_location=save_location)

        # multi-experiment mode
        save_loc_folder, exp_identifier = decide_folder_and_filename(self.commons, self.args)

        return Export.make(
            identifier=exp_identifier,
            save_location=save_location,
            writable_objects_params=[
                {
                    "file_writable_obj": self.args,
                    "content_dumping_kwargs": {
                        "commonparams": self.commons,
                        "outfields": self.outfields,
                    },
                },
                {
                    "file_writable_obj": self.beforewards,
                    "content_dumping_kwargs": {
                        "export_transpiled_circuit": export_transpiled_circuit
                    },
                },
                {"file_writable_obj": self.afterwards},
                {"file_writable_obj": self.side_products},
                {"file_writable_obj": self.reports},
            ],
            exp_id=str(self.commons.exp_id),
            folder=save_loc_folder,
        )

    def write(
        self,
        save_location: Path | str | None = None,
        export_transpiled_circuit: bool = False,
        qurryinfo_lock: str | None = None,
        pbar: tqdm.tqdm | None = None,
    ) -> tuple[str, dict[str, str]]:
        """Export the experiment data, if there is a previous export, then will overwrite.

        Args:
            save_location (Path | str | None, optional):
                Where to save the export content as `json` file.
                If `save_location == None`, then use the value in `self.commons` to be exported,
                if it's None too, then raise error. Defaults to None.
            export_transpiled_circuit (bool, optional):
                Whether to export the transpiled circuit as txt. Defaults to False.
                When set to True, the transpiled circuit will be exported as txt.
                Otherwise, the circuit will be not exported but circuit qasm remains.
            qurryinfo_lock (str | None, optional):
                If set to the same as `self.commons.summoner_id`,
                then export by :class:`~qurry.qurrium.multimanager.multimanager.MultiManager`.
                Defaults to None.
            pbar (tqdm.tqdm | None, optional):
                The progress bar for showing the progress of the experiment. Defaults to None.

        Returns:
            tuple[str, dict[str, str]]: The id of the experiment and the files location.
        """
        set_pbar_description(pbar, "Preparing to export...")

        # experiment write
        export_material = self.export(save_location, export_transpiled_circuit)
        exp_id, files = export_material.write()
        assert "qurryinfo" in files, (
            "qurryinfo must be in the exported files. It should be ensured."
        )

        if self.commons.summoner_id is not None and qurryinfo_lock == self.commons.summoner_id:
            return exp_id, files

        real_export_location = Path(self.commons.save_location) / export_material.folder
        qurry_info = QurryInfo.read(real_export_location)
        qurry_info.update_qurryinfo({exp_id: files})
        qurry_info.write(real_export_location)

        return exp_id, qurry_info[exp_id]

    @classmethod
    def _read_core(
        cls,
        exp_id: str,
        file_index: dict[str, str],
        save_location: Path | str | None = Path("./"),
    ):
        """Core of read function.

        Args:
            exp_id (str): The id of the experiment to be read.
            file_index (dict[str, str]): The index of the experiment to be read.
            save_location (Path | str | None): The location of the experiment to be read.

        Raises:
            ValueError: 'save_location' needs to be the type of 'str' or 'Path'.
            FileNotFoundError: When `save_location` is not available.

        Returns:
            QurryExperiment: The experiment to be read.
        """

        save_location = create_save_location(save_location)
        if not os.path.exists(save_location):
            raise FileNotFoundError(f"'save_location' does not exist, '{save_location}'.")

        arguments, commonparams, outfields = cls.arguments_type().read(
            file_index=file_index, save_location=save_location, exp_id=exp_id
        )
        if is_old_v7_file_structure(file_index):
            commonparams.datetimes.add_only("migrated_to_v15")
        exp_instance = cls(
            arguments=arguments,
            commonparams=commonparams,
            outfields=outfields,
            side_products=cls.side_product_type().read(
                file_index=file_index, save_location=save_location
            ),
            beforewards=Before.read(file_index=file_index, save_location=save_location),
            afterwards=After.read(file_index=file_index, save_location=save_location),
            reports=AnalysesContainer.read(
                file_index=file_index,
                save_location=save_location,
                analysis_instance=cls.analysis_type(),
            ),
        )
        if exp_instance.reports.analysis_instance != cls.analysis_type():
            raise ValueError(
                "The analysis type of the experiment is not compatible with "
                + f"the current class analysis type, {exp_instance.reports.analysis_instance} "
                + f"vs {cls.analysis_type()}."
            )

        return exp_instance

    @classmethod
    def _read_core_multiprocess(cls, all_arugments: tuple[str, dict[str, str], Path | str]):
        """Core of read function for multiprocess.

        Args:
            all_arugments (tuple[str, dict[str, str], Path | str]):
                The arguments of the experiment to be read.

                - exp_id (str): The id of the experiment to be read.
                - file_index (dict[str, str]): The index of the experiment to be read.
                - save_location (Path | str): The location of the experiment to be read.
        Returns:
            QurryExperiment: The experiment to be read.
        """
        return cls._read_core(*all_arugments)

    @classmethod
    def read(
        cls,
        exp_or_summoner_name: Path | str,
        save_location: Path | str | None = Path("./"),
        multiprocess: bool = True,
    ):
        """Read the experiment from file.

        Args:
            exp_or_summoner_name (Path | str):
                The experiment name or multimanager name to be read.
            save_location (Path | str | None, optional):
                The location of the experiment to be read. Defaults to Path('./').
            multiprocess (bool, optional):
                Whether to use multiprocessing. Defaults to `True`.

        Raises:
            ValueError: 'save_location' needs to be the type of 'str' or 'Path'.
            FileNotFoundError: When `save_location` is not available.

        Returns:
            list[ExperimentPrototype]: The experiment to be read.
        """

        save_location = create_save_location(save_location)
        if not os.path.exists(save_location):
            raise FileNotFoundError(f"'save_location' does not exist, '{save_location}'.")
        export_location = save_location / exp_or_summoner_name
        if not os.path.exists(export_location):
            raise FileNotFoundError(f"'ExportLoaction' does not exist, '{export_location}'.")

        qurryinfo: QurryInfo = QurryInfo.read(save_location=export_location)
        num_exps = len(qurryinfo)
        if not multiprocess or len(qurryinfo) == 1:
            return [
                cls._read_core(
                    exp_id=exp_id,
                    file_index=file_index,
                    save_location=save_location,
                )
                for exp_id, file_index in qurryinfo.items()
            ]

        chunks_num = very_easy_chunk_size(
            tasks_num=num_exps,
            num_process=DEFAULT_POOL_SIZE,
            max_chunk_size=min(max(1, num_exps // DEFAULT_POOL_SIZE), 40),
        )
        with make_multiprocess_pool(maxtasksperchild=chunks_num * 2) as pool:
            return list(
                qurry_progressbar(
                    pool.imap_unordered(
                        cls._read_core_multiprocess,
                        (
                            (exp_id, file_index, save_location)
                            for exp_id, file_index in qurryinfo.items()
                        ),
                    ),
                    total=num_exps,
                    desc=f"Loading {num_exps} experiments ...",
                )
            )
