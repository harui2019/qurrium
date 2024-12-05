"""
===========================================================
ShadowUnveil - Qurry
(:mod:`qurry.qurrent.classical_shadow.qurry`)
===========================================================

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
    ShadowUnveilOutputArgs,
    ShadowUnveilMeasureArgs,
    ShadowUnveilAnalyzeArgs,
)
from .experiment import (
    ShadowUnveilExperiment,
    PostProcessingBackendLabel,
    DEFAULT_PROCESS_BACKEND,
)
from ...qurrium.qurrium import QurriumPrototype
from ...qurrium.container import ExperimentContainer
from ...tools.backend import GeneralSimulator
from ...declare import BaseRunArgs, TranspileArgs


class ShadowUnveil(QurriumPrototype):
    r"""Classical Shadow with The Results of Second Order Renyi Entropy.

    .. note::
        - Predicting many properties of a quantum system from very few measurements -
        Huang, Hsin-Yuan and Kueng, Richard and Preskill, John
        [doi:10.1038/s41567-020-0932-7](
            https://doi.org/10.1038/s41567-020-0932-7)

        - The randomized measurement toolbox -
        Elben, Andreas and Flammia, Steven T. and Huang, Hsin-Yuan and Kueng,
        Richard and Preskill, John and Vermersch, Benoît and Zoller, Peter
        [doi:10.1038/s42254-022-00535-2](
            https://doi.org/10.1038/s42254-022-00535-2)

    .. code-block:: bibtex

        @article{cite-key,
            abstract = {
                Predicting the properties of complex,
                large-scale quantum systems is essential for developing quantum technologies.
                We present an efficient method for constructing an approximate classical
                description of a quantum state using very few measurements of the state.
                different properties; order
                {\$}{\$}{\{}{$\backslash$}mathrm{\{}log{\}}{\}}{$\backslash$},(M){\$}{\$}
                measurements suffice to accurately predict M different functions of the state
                with high success probability. The number of measurements is independent of
                the system size and saturates information-theoretic lower bounds. Moreover,
                target properties to predict can be selected after the measurements are completed.
                We support our theoretical findings with extensive numerical experiments.
                We apply classical shadows to predict quantum fidelities,
                entanglement entropies, two-point correlation functions,
                expectation values of local observables and the energy variance of
                many-body local Hamiltonians.
                The numerical results highlight the advantages of classical shadows relative to
                previously known methods.},
            author = {Huang, Hsin-Yuan and Kueng, Richard and Preskill, John},
            date = {2020/10/01},
            date-added = {2024-12-03 15:00:55 +0800},
            date-modified = {2024-12-03 15:00:55 +0800},
            doi = {10.1038/s41567-020-0932-7},
            id = {Huang2020},
            isbn = {1745-2481},
            journal = {Nature Physics},
            number = {10},
            pages = {1050--1057},
            title = {Predicting many properties of a quantum system from very few measurements},
            url = {https://doi.org/10.1038/s41567-020-0932-7},
            volume = {16},
            year = {2020},
            bdsk-url-1 = {https://doi.org/10.1038/s41567-020-0932-7}}

        @article{cite-key,
            abstract = {
                Programmable quantum simulators and quantum computers are opening unprecedented
                opportunities for exploring and exploiting the properties of highly entangled
                complex quantum systems. The complexity of large quantum systems is the source
                of computational power but also makes them difficult to control precisely or
                characterize accurately using measured classical data. We review protocols
                for probing the properties of complex many-qubit systems using measurement
                schemes that are practical using today's quantum platforms. In these protocols,
                a quantum state is repeatedly prepared and measured in a randomly chosen basis;
                then a classical computer processes the measurement outcomes to estimate the
                desired property. The randomization of the measurement procedure has distinct
                advantages. For example, a single data set can be used multiple times to pursue
                a variety of applications, and imperfections in the measurements are mapped to
                a simplified noise model that can more easily be mitigated. We discuss a range of
                cases that have already been realized in quantum devices, including Hamiltonian
                simulation tasks, probes of quantum chaos, measurements of non-local order
                parameters, and comparison of quantum states produced in distantly separated
                laboratories. By providing a workable method for translating a complex quantum
                state into a succinct classical representation that preserves a rich variety of
                relevant physical properties, the randomized measurement toolbox strengthens our
                ability to grasp and control the quantum world.},
            author = {
                Elben, Andreas and Flammia, Steven T. and Huang, Hsin-Yuan and Kueng,
                Richard and Preskill, John and Vermersch, Beno{\^\i}t and Zoller, Peter},
            date = {2023/01/01},
            date-added = {2024-12-03 15:06:15 +0800},
            date-modified = {2024-12-03 15:06:15 +0800},
            doi = {10.1038/s42254-022-00535-2},
            id = {Elben2023},
            isbn = {2522-5820},
            journal = {Nature Reviews Physics},
            number = {1},
            pages = {9--24},
            title = {The randomized measurement toolbox},
            url = {https://doi.org/10.1038/s42254-022-00535-2},
            volume = {5},
            year = {2023},
            bdsk-url-1 = {https://doi.org/10.1038/s42254-022-00535-2}}

    """

    __name__ = "EntropyRandomizedMeasure"
    short_name = SHORT_NAME

    @property
    def experiment_instance(self) -> Type[ShadowUnveilExperiment]:
        """The container class responding to this QurryV5 class."""
        return ShadowUnveilExperiment

    exps: ExperimentContainer[ShadowUnveilExperiment]

    def measure_to_output(
        self,
        wave: Optional[Union[QuantumCircuit, Hashable]] = None,
        times: int = 100,
        measure: Union[int, tuple[int, int], None] = None,
        unitary_loc: Union[int, tuple[int, int], None] = None,
        unitary_loc_not_cover_measure: bool = False,
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
    ) -> ShadowUnveilOutputArgs:
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
            unitary_loc_not_cover_measure (bool, optional):
                Whether the range of the unitary operator is not cover the measure range.
                Defaults to `False`.
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
            ShadowUnveilOutputArgs: The output arguments.
        """
        if wave is None:
            raise ValueError("The `wave` must be provided.")

        return {
            "circuits": [wave],
            "times": times,
            "measure": measure,
            "unitary_loc": unitary_loc,
            "unitary_loc_not_cover_measure": unitary_loc_not_cover_measure,
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
        unitary_loc_not_cover_measure: bool = False,
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
            unitary_loc_not_cover_measure (bool, optional):
                Whether the range of the unitary operator is not cover the measure range.
                Defaults to `False`.
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
            unitary_loc_not_cover_measure=unitary_loc_not_cover_measure,
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
        config_list: list[Union[dict[str, Any], ShadowUnveilMeasureArgs]],
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
            config_list (list[Union[dict[str, Any], ShadowUnveilMeasureArgs]]):
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
            dict[Hashable, Union[dict[str, Any], ShadowUnveilAnalyzeArgs, bool]]
        ] = None,
        compress: bool = False,
        write: bool = True,
        # analysis arguments
        selected_qubits: Optional[list[int]] = None,
        backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
        counts_used: Optional[Iterable[int]] = None,
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
                    dict[str, Any], ShadowUnveilAnalyzeArgs, bool]
                ]]], optional
            ):
                The specific arguments for analysis. Defaults to None.
            compress (bool, optional):
                Whether to compress the export file. Defaults to False.
            write (bool, optional):
                Whether to write the export file. Defaults to True.

            selected_qubits (Optional[list[int]], optional):
                The selected qubits. Defaults to None.
            backend (PostProcessingBackendLabel, optional):
                The backend for the postprocessing. Defaults to DEFAULT_PROCESS_BACKEND.
            counts_used (Optional[Iterable[int]], optional):
                The counts used for the analysis. Defaults to None.

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
            selected_qubits=selected_qubits,
            backend=backend,
            counts_used=counts_used,
            **analysis_args,
        )
