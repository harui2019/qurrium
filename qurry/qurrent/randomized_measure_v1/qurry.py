"""
===========================================================
EntropyMeasureRandomizedV1 - Qurry
(:mod:`qurry.qurrent.randomized_measure_v1.qurry`)
===========================================================

This is a deprecated version of the randomized measure module.

"""

from typing import Union, Optional, Any, Type, Literal, Iterable
from collections.abc import Hashable
from pathlib import Path
import tqdm

from qiskit import QuantumCircuit
from qiskit.providers import Backend
from qiskit.transpiler.passmanager import PassManager

from .arguments import (
    SHORT_NAME,
    EntropyMeasureRandomizedV1OutputArgs,
    EntropyMeasureRandomizedV1MeasureArgs,
    EntropyMeasureRandomizedV1AnalyzeArgs,
)
from .experiment import (
    EntropyMeasureRandomizedV1Experiment,
    PostProcessingBackendLabel,
    DEFAULT_PROCESS_BACKEND,
)
from ...qurrium.qurrium import QurriumPrototype
from ...qurrium.container import ExperimentContainer
from ...tools.backend import GeneralSimulator
from ...declare import BaseRunArgs, TranspileArgs


class EntropyMeasureRandomizedV1(QurriumPrototype):
    """Randomized Measure for entangled entropy.
    The entropy we compute is the Second Order Rényi Entropy.

    .. note::
        - Probing Rényi entanglement entropy via randomized measurements -
        Tiff Brydges, Andreas Elben, Petar Jurcevic, Benoît Vermersch,
        Christine Maier, Ben P. Lanyon, Peter Zoller, Rainer Blatt ,and Christian F. Roos ,
        [doi:10.1126/science.aau4963](
            https://www.science.org/doi/abs/10.1126/science.aau4963)

        - Simple mitigation of global depolarizing errors in quantum simulations -
        Vovrosh, Joseph and Khosla, Kiran E. and Greenaway, Sean and Self,
        Christopher and Kim, M. S. and Knolle, Johannes,
        [PhysRevE.104.035309](
            https://link.aps.org/doi/10.1103/PhysRevE.104.035309)

    .. code-block:: bibtex

        @article{doi:10.1126/science.aau4963,
            author = {Tiff Brydges  and Andreas Elben  and Petar Jurcevic
                and Benoît Vermersch  and Christine Maier  and Ben P. Lanyon
                and Peter Zoller  and Rainer Blatt  and Christian F. Roos },
            title = {Probing Rényi entanglement entropy via randomized measurements},
            journal = {Science},
            volume = {364},
            number = {6437},
            pages = {260-263},
            year = {2019},
            doi = {10.1126/science.aau4963},
            URL = {https://www.science.org/doi/abs/10.1126/science.aau4963},
            eprint = {https://www.science.org/doi/pdf/10.1126/science.aau4963},
            abstract = {Quantum systems are predicted to be better at information
            processing than their classical counterparts, and quantum entanglement
            is key to this superior performance. But how does one gauge the degree
            of entanglement in a system? Brydges et al. monitored the build-up of
            the so-called Rényi entropy in a chain of up to 10 trapped calcium ions,
            each of which encoded a qubit. As the system evolved,
            interactions caused entanglement between the chain and the rest of
            the system to grow, which was reflected in the growth of
            the Rényi entropy. Science, this issue p. 260 The buildup of entropy
            in an ion chain reflects a growing entanglement between the chain
            and its complement. Entanglement is a key feature of many-body quantum systems.
            Measuring the entropy of different partitions of a quantum system
            provides a way to probe its entanglement structure.
            Here, we present and experimentally demonstrate a protocol
            for measuring the second-order Rényi entropy based on statistical correlations
            between randomized measurements. Our experiments, carried out with a trapped-ion
            quantum simulator with partition sizes of up to 10 qubits,
            prove the overall coherent character of the system dynamics and
            reveal the growth of entanglement between its parts,
            in both the absence and presence of disorder.
            Our protocol represents a universal tool for probing and
            characterizing engineered quantum systems in the laboratory,
            which is applicable to arbitrary quantum states of up to
            several tens of qubits.}}

        @article{PhysRevE.104.035309,
            title = {Simple mitigation of global depolarizing errors in quantum simulations},
            author = {Vovrosh, Joseph and Khosla, Kiran E. and Greenaway, Sean and Self,
            Christopher and Kim, M. S. and Knolle, Johannes},
            journal = {Phys. Rev. E},
            volume = {104},
            issue = {3},
            pages = {035309},
            numpages = {8},
            year = {2021},
            month = {Sep},
            publisher = {American Physical Society},
            doi = {10.1103/PhysRevE.104.035309},
            url = {https://link.aps.org/doi/10.1103/PhysRevE.104.035309}
        }
    """

    __name__ = "EntropyRandomizedMeasureV1"
    short_name = SHORT_NAME

    @property
    def experiment_instance(self) -> Type[EntropyMeasureRandomizedV1Experiment]:
        """The container class responding to this QurryV5 class."""
        return EntropyMeasureRandomizedV1Experiment

    exps: ExperimentContainer[EntropyMeasureRandomizedV1Experiment]

    def measure_to_output(
        self,
        wave: Optional[Union[QuantumCircuit, Hashable]] = None,
        times: int = 100,
        measure: Union[int, tuple[int, int], None] = None,
        unitary_loc: Union[int, tuple[int, int], None] = None,
        random_unitary_seeds: Optional[dict[int, dict[int, int]]] = None,
        # basic inputs
        shots: int = 1024,
        backend: Optional[Backend] = None,
        exp_name: str = "experiment",
        run_args: Optional[Union[BaseRunArgs, dict[str, Any]]] = None,
        transpile_args: Optional[TranspileArgs] = None,
        passmanager: Optional[Union[str, PassManager, tuple[str, PassManager]]] = None,
        tags: Optional[tuple[str, ...]] = None,
        # process tool
        qasm_version: Literal["qasm2", "qasm3"] = "qasm3",
        export: bool = False,
        save_location: Optional[Union[Path, str]] = None,
        mode: str = "w+",
        indent: int = 2,
        encoding: str = "utf-8",
        jsonable: bool = False,
        pbar: Optional[tqdm.tqdm] = None,
    ) -> EntropyMeasureRandomizedV1OutputArgs:
        """Trasnform :meth:`measure` arguments form into :meth:`output` form.

        Args:
            wave (Union[QuantumCircuit, Hashable]):
                The key or the circuit to execute.
            times (int, optional):
                The number of random unitary operator.
                It will denote as `N_U` in the experiment name.
                Defaults to `100`.
            measure (Union[int, tuple[int, int], None], optional):
                The measure range. Defaults to `None`.
            unitary_loc (Union[int, tuple[int, int], None], optional):
                The range of the unitary operator. Defaults to `None`.
            random_unitary_seeds (Optional[dict[int, dict[int, int]]], optional):
                The seeds for all random unitary operator.
                This argument only takes input as type of `dict[int, dict[int, int]]`.
                The first key is the index for the random unitary operator.
                The second key is the index for the qubit.

                .. code-block:: python
                    {
                        0: {0: 1234, 1: 5678},
                        1: {0: 2345, 1: 6789},
                        2: {0: 3456, 1: 7890},
                    }

                If you want to generate the seeds for all random unitary operator,
                you can use the function `generate_random_unitary_seeds`
                in `qurry.qurrium.utils.random_unitary`.

                .. code-block:: python
                    from qurry.qurrium.utils.random_unitary import generate_random_unitary_seeds
                    random_unitary_seeds = generate_random_unitary_seeds(100, 2)
            shots (int, optional):
                Shots of the job. Defaults to `1024`.
            backend (Optional[Backend], optional):
                The quantum backend. Defaults to None.
            exp_name (str, optional):
                The name of the experiment.
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.
            run_args (Optional[Union[BaseRunArgs, dict[str, Any]]], optional):
                Arguments for :func:`qiskit.execute`. Defaults to `{}`.
            transpile_args (Optional[TranspileArgs], optional):
                Arguments for :func:`qiskit.transpile`. Defaults to `{}`.
            passmanager (Optional[Union[str, PassManager, tuple[str, PassManager]], optional):
                The passmanager. Defaults to None.
            tags (Optional[tuple[str, ...]], optional):
                The tags of the experiment. Defaults to None.

            qasm_version (Literal["qasm2", "qasm3"], optional):
                The version of OpenQASM. Defaults to "qasm3".
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
            EntropyMeasureRandomizedOutputArgs: The output arguments.
        """
        if wave is None:
            raise ValueError("The `wave` must be provided.")

        return {
            "circuits": [wave],
            "times": times,
            "measure": measure,
            "unitary_loc": unitary_loc,
            "random_unitary_seeds": random_unitary_seeds,
            "shots": shots,
            "backend": backend,
            "exp_name": exp_name,
            "run_args": run_args,
            "transpile_args": transpile_args,
            "passmanager": passmanager,
            "tags": tags,
            # process tool
            "qasm_version": qasm_version,
            "export": export,
            "save_location": save_location,
            "mode": mode,
            "indent": indent,
            "encoding": encoding,
            "jsonable": jsonable,
            "pbar": pbar,
        }

    def measure(
        self,
        wave: Optional[Union[QuantumCircuit, Hashable]] = None,
        times: int = 100,
        measure: Union[int, tuple[int, int], None] = None,
        unitary_loc: Union[int, tuple[int, int], None] = None,
        random_unitary_seeds: Optional[dict[int, dict[int, int]]] = None,
        # basic inputs
        shots: int = 1024,
        backend: Optional[Backend] = None,
        exp_name: str = "experiment",
        run_args: Optional[Union[BaseRunArgs, dict[str, Any]]] = None,
        transpile_args: Optional[TranspileArgs] = None,
        passmanager: Optional[Union[str, PassManager, tuple[str, PassManager]]] = None,
        tags: Optional[tuple[str, ...]] = None,
        # process tool
        qasm_version: Literal["qasm2", "qasm3"] = "qasm3",
        export: bool = False,
        save_location: Optional[Union[Path, str]] = None,
        mode: str = "w+",
        indent: int = 2,
        encoding: str = "utf-8",
        jsonable: bool = False,
        pbar: Optional[tqdm.tqdm] = None,
    ) -> str:
        """Execute the experiment.

        Args:
            wave (Union[QuantumCircuit, Hashable]):
                The key or the circuit to execute.
            times (int, optional):
                The number of random unitary operator.
                It will denote as `N_U` in the experiment name.
                Defaults to `100`.
            measure (Union[int, tuple[int, int], None], optional):
                The measure range. Defaults to `None`.
            unitary_loc (Union[int, tuple[int, int], None], optional):
                The range of the unitary operator. Defaults to `None`.
            random_unitary_seeds (Optional[dict[int, dict[int, int]]], optional):
                The seeds for all random unitary operator.
                This argument only takes input as type of `dict[int, dict[int, int]]`.
                The first key is the index for the random unitary operator.
                The second key is the index for the qubit.

                .. code-block:: python
                    {
                        0: {0: 1234, 1: 5678},
                        1: {0: 2345, 1: 6789},
                        2: {0: 3456, 1: 7890},
                    }

                If you want to generate the seeds for all random unitary operator,
                you can use the function `generate_random_unitary_seeds`
                in `qurry.qurrium.utils.random_unitary`.

                .. code-block:: python
                    from qurry.qurrium.utils.random_unitary import generate_random_unitary_seeds
                    random_unitary_seeds = generate_random_unitary_seeds(100, 2)
            shots (int, optional):
                Shots of the job. Defaults to `1024`.
            backend (Optional[Backend], optional):
                The quantum backend. Defaults to None.
            exp_name (str, optional):
                The name of the experiment.
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.
            run_args (Optional[Union[BaseRunArgs, dict[str, Any]]], optional):
                Arguments for :func:`qiskit.execute`. Defaults to `{}`.
            transpile_args (Optional[TranspileArgs], optional):
                Arguments for :func:`qiskit.transpile`. Defaults to `{}`.
            passmanager (Optional[Union[str, PassManager, tuple[str, PassManager]], optional):
                The passmanager. Defaults to None.
            tags (Optional[tuple[str, ...]], optional):
                The tags of the experiment. Defaults to None.

            qasm_version (Literal["qasm2", "qasm3"], optional):
                The version of OpenQASM. Defaults to "qasm3".
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
            str: The experiment ID.
        """

        output_args = self.measure_to_output(
            wave=wave,
            times=times,
            measure=measure,
            unitary_loc=unitary_loc,
            random_unitary_seeds=random_unitary_seeds,
            shots=shots,
            backend=backend,
            exp_name=exp_name,
            run_args=run_args,
            transpile_args=transpile_args,
            passmanager=passmanager,
            tags=tags,
            # process tool
            qasm_version=qasm_version,
            export=export,
            save_location=save_location,
            mode=mode,
            indent=indent,
            encoding=encoding,
            jsonable=jsonable,
            pbar=pbar,
        )

        return self.output(**output_args)

    def multiOutput(
        self,
        config_list: list[Union[dict[str, Any], EntropyMeasureRandomizedV1MeasureArgs]],
        summoner_name: str = "exps",
        summoner_id: Optional[str] = None,
        shots: int = 1024,
        backend: Backend = GeneralSimulator(),
        tags: Optional[tuple[str, ...]] = None,
        manager_run_args: Optional[Union[BaseRunArgs, dict[str, Any]]] = None,
        save_location: Union[Path, str] = Path("./"),
        compress: bool = False,
    ) -> str:
        """Output the multiple experiments.

        Args:
            config_list (list[Union[dict[str, Any], EntropyMeasureRandomizedV1MeasureArgs]]):
                The list of default configurations of multiple experiment. Defaults to [].
            summoner_name (str, optional):
                Name for multimanager. Defaults to 'exps'.
            summoner_id (Optional[str], optional):
                Name for multimanager. Defaults to None.
            shots (int, optional):
                Shots of the job. Defaults to `1024`.
            backend (Backend, optional):
                The quantum backend.
                Defaults to AerSimulator().
            tags (Optional[tuple[str, ...]], optional):
                Tags of experiment of the MultiManager. Defaults to None.
            manager_run_args (Optional[Union[BaseRunArgs, dict[str, Any]]], optional):
                The extra arguments for running the job,
                but for all experiments in the multimanager.
                For :meth:`backend.run()` from :cls:`qiskit.providers.backend`. Defaults to `{}`.
            save_location (Union[Path, str], optional):
                Where to save the export content as `json` file.
                If `save_location == None`, then cancelled the file to be exported.
                Defaults to Path('./').
            compress (bool, optional):
                Whether to compress the export file. Defaults to False.

        Returns:
            str: The summoner_id of multimanager.
        """

        return super().multiOutput(
            config_list=config_list,
            summoner_name=summoner_name,
            summoner_id=summoner_id,
            shots=shots,
            backend=backend,
            tags=tags,
            manager_run_args=manager_run_args,
            save_location=save_location,
            compress=compress,
        )

    def multiAnalysis(
        self,
        summoner_id: str,
        analysis_name: str = "report",
        no_serialize: bool = False,
        specific_analysis_args: Optional[
            dict[Hashable, Union[dict[str, Any], EntropyMeasureRandomizedV1AnalyzeArgs, bool]]
        ] = None,
        compress: bool = False,
        write: bool = True,
        # analysis arguments
        degree: Optional[Union[tuple[int, int], int]] = None,
        counts_used: Optional[Iterable[int]] = None,
        workers_num: Optional[int] = None,
        independent_all_system: bool = False,
        backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
        **analysis_args,
    ) -> str:
        """Run the analysis for multiple experiments.

        Args:
            summoner_id (str): The summoner_id of multimanager.
            analysis_name (str, optional):
                The name of analysis. Defaults to 'report'.
            no_serialize (bool, optional):
                Whether to serialize the analysis. Defaults to False.
            specific_analysis_args
                Optional[dict[Hashable, Union[
                    dict[str, Any], EntropyMeasureRandomizedAnalyzeArgs, bool]
                ]]], optional
            ):
                The specific arguments for analysis. Defaults to None.
            compress (bool, optional):
                Whether to compress the export file. Defaults to False.
            write (bool, optional):
                Whether to write the export file. Defaults to True.

            degree (Union[tuple[int, int], int]): Degree of the subsystem.
            counts_used (Optional[Iterable[int]], optional):
                The index of the counts used.
                If not specified, then use all counts.
                Defaults to None.
            workers_num (Optional[int], optional):
                Number of multi-processing workers,
                if sets to 1, then disable to using multi-processing;
                if not specified, then use the number of all cpu counts - 2 by `cpu_count() - 2`.
                Defaults to None.
            independent_all_system (bool, optional):
                If True, then calculate the all system independently.
                Otherwise, use the existed all system source with same `count_used`.
            backend (PostProcessingBackendLabel, optional):
                Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.

        Returns:
            str: The summoner_id of multimanager.
        """

        return super().multiAnalysis(
            summoner_id=summoner_id,
            analysis_name=analysis_name,
            no_serialize=no_serialize,
            specific_analysis_args=specific_analysis_args,
            compress=compress,
            write=write,
            # analysis arguments
            degree=degree,
            counts_used=counts_used,
            workers_num=workers_num,
            independent_all_system=independent_all_system,
            backend=backend,
            **analysis_args,
        )
