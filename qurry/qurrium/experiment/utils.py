"""Experiment Utilities (:mod:`qurry.qurrium.experiment.utils`)"""

import os
import warnings
from pathlib import Path
from uuid import uuid4, UUID
import tqdm
import numpy as np

from qiskit import QuantumCircuit, transpile
from qiskit.providers import Backend
from qiskit.transpiler.passmanager import PassManager

from .beforewards import Before
from .afterwards import After
from ..analysis import AnalysesContainer
from ..container import WCKeyable, TranspileArgs
from ..arguments import Commonparams, ArgumentsPrototype
from ..utils.iocontrol import RJUST_LEN
from ..exceptions import (
    InvalidExpIdReplacementWarning,
    InvalidSummonerConfiguration,
    InvalidInherition,
    DummyClassWarning,
    TranspileConfigurationIgnored,
    UnrunableBackendError,
    ABOUT_UNRUNNABLE_IBM_BACKEND,
    ABOUT_UNRUNNABLE_THIRD_PARTY,
)
from ...capsule.hoshi import Hoshi
from ...tools import set_pbar_description


def exp_id_process(exp_id: str | None) -> str:
    """Check the exp_id is valid or not, if not, then generate a new one.

    Args:
        exp_id (str | None): The id of the experiment to be checked.

    Raises:
        TypeError: If the exp_id is not a string.
        QurryHashIDInvalid: If the exp_id is not a valid UUID.

    Returns:
        str: The valid exp_id.
    """

    if exp_id is None:
        return str(uuid4())
    if not isinstance(exp_id, str):
        raise TypeError(f"exp_id must be str, not {type(exp_id)}.")

    try:
        UUID(exp_id, version=4)
    except ValueError as e:
        warnings.warn(
            f"exp_id is not a valid UUID, it will be generated automatically.\n{e}",
            category=InvalidExpIdReplacementWarning,
        )
        return str(uuid4())

    return exp_id


def memory_usage_factor_expect(
    target: list[tuple[WCKeyable, QuantumCircuit | str]],
    circuits: list[QuantumCircuit],
    commonparams: Commonparams,
) -> int:
    """Estimate the memory usage of
    :class:`~qurry.qurrium.experiment.experiment.ExperimentPrototype` by the circuits.

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

    Args:
        target (list[tuple[WCKeyable, QuantumCircuit | str]]):
            The target circuits of the experiment.
        circuits (list[QuantumCircuit]): The transpiled circuits of the experiment.
        commonparams (Commonparams): The common parameters of the experiment.

    Returns:
        int: The factor of the memory usage.
    """

    circuit_instructions_num = sum(len(circuit.data) for circuit in circuits)

    factor = circuit_instructions_num * np.sqrt(commonparams.shots)
    factor += sum(len(circuit.data) for _, circuit in target if isinstance(circuit, QuantumCircuit))

    return int(np.round(factor))


def implementation_check(name_exps: str, args: ArgumentsPrototype, commons: Commonparams) -> None:
    """Check whether the experiment is implemented correctly.

    Args:
        name_exps (str): The name of the experiment.
        args (ArgumentsPrototype): The arguments of the experiment.
        commons (Commonparams): The common parameters of the experiment.

    Raises:
        QurryInvalidInherition:
            If the experiment's arguments and common parameters have duplicate fields.
        UnconfiguredWarning:
            If the experiment's name is not configured.
    """

    duplicate_fields = set(args.fields) & set(commons.fields)
    if len(duplicate_fields) > 0:
        raise InvalidInherition(
            f"{name_exps}.arguments which and {name_exps}.commonparams "
            f"should not have same fields: {duplicate_fields}."
        )
    if name_exps == "ExperimentPrototype":
        warnings.warn(
            "You should set a new __name__ for your experiment class, "
            + "otherwise it will be considered as an abstract class of Qurrium during printing.",
            category=DummyClassWarning,
        )


def summonner_check(serial: int | None, summoner_id: str | None, summoner_name: str | None):
    """Check the summoner information taken from the experiment.

    Args:
        serial (int | None): The serial number of the experiment.
        summoner_id (str | None): The ID of the summoner.
        summoner_name (str | None): The name of the summoner.

    Raises:
        QurrySummonerInvalid: If the summoner information is not completed.

    Returns:
        bool: True if the summoner information is completed, False otherwise.
    """

    summon_check = {
        "serial": serial,
        "summoner_id": summoner_id,
        "summoner_name": summoner_name,
    }
    summon_detect = any((v is not None) for v in summon_check.values())
    summon_fulfill = all((v is not None) for v in summon_check.values())
    if summon_detect and not summon_fulfill:
        summon_msg = Hoshi(ljust_description_len=20)
        summon_msg.newline(("divider",))
        summon_msg.newline(("h3", "Summoner Info Incompletion"))
        summon_msg.newline(("itemize", "Summoner info detect.", summon_detect))
        summon_msg.newline(("itemize", "Summoner info fulfilled.", summon_fulfill))
        for k, v in summon_check.items():
            summon_msg.newline(("itemize", k, str(v), f"fulfilled: {v is not None}", 2))
        summon_msg.print()
        raise InvalidSummonerConfiguration(
            "Summoner data is not completed, it will export in single experiment mode.",
        )
    return summon_fulfill


def inner_process_transpile_func(
    circuits: list[QuantumCircuit],
    transpile_args: TranspileArgs,
    backend: Backend,
    multiprocess: bool = False,
    pbar: tqdm.tqdm | None = None,
) -> list[QuantumCircuit]:
    """The inner process for transpiling the circuits without passmanager.

    Args:
        circuits (list[QuantumCircuit]):
            The circuits to be transpiled.
        transpile_args (TranspileArgs):
            The transpile arguments.
        backend (Backend):
            The backend to be used for transpilation.
        exp_id (str):
            The experiment ID, used for warning messages.
        multiprocess (bool, optional):
            Whether to use multiprocessing. Defaults to False.
        pbar (tqdm.tqdm | None, optional):
            The progress bar. Defaults to None.

    Returns:
        list[QuantumCircuit]: The transpiled circuits.
    """
    set_pbar_description(pbar, "Circuit transpiling...")
    transpile_args.pop("num_processes", None)
    transpiled_circs = transpile(
        circuits,
        backend=backend,
        num_processes=None if multiprocess else 1,
        **transpile_args,
    )
    return transpiled_circs


def inner_process_passmanager(
    circuits: list[QuantumCircuit],
    transpile_args: TranspileArgs,
    passmanager_pair: tuple[str, PassManager],
    exp_id: str,
    multiprocess: bool = False,
    pbar: tqdm.tqdm | None = None,
) -> list[QuantumCircuit]:
    """The inner process for transpiling the circuits with passmanager.

    Args:
        circuits (list[QuantumCircuit]):
            The circuits to be transpiled.
        transpile_args (TranspileArgs):
            The transpile arguments.
        passmanager_pair (tuple[str, PassManager]):
            The passmanager name and the passmanager to be used.
        exp_id (str):
            The experiment ID, used for warning messages.
        multiprocess (bool, optional):
            Whether to use multiprocessing. Defaults to False.
        pbar (tqdm.tqdm | None, optional):
            The progress bar. Defaults to None.

    Returns:
        list[QuantumCircuit]: The transpiled circuits.
    """

    passmanager_name, passmanager = passmanager_pair
    if not isinstance(passmanager, PassManager):
        raise TypeError(
            "The passmanager must be an instance of PassManager, "
            + f"not {type(passmanager)} in '{exp_id}'"
        )
    set_pbar_description(pbar, f"Circuit transpiling by passmanager '{passmanager_name}'...")
    transpiled_circs = passmanager.run(
        circuits=circuits,
        num_processes=None if multiprocess else 1,  # type: ignore
    )
    if len(transpile_args) > 0:
        warnings.warn(
            f"Passmanager '{passmanager_name}' is given, "
            + f"the transpile_args will be ignored in '{exp_id}'",
            category=TranspileConfigurationIgnored,
        )
    return transpiled_circs


def process_transpilation(
    circuits: list[QuantumCircuit],
    transpile_args: TranspileArgs,
    backend: Backend,
    passmanager_pair: tuple[str, PassManager] | None,
    exp_id: str,
    multiprocess: bool = False,
    pbar: tqdm.tqdm | None = None,
) -> list[QuantumCircuit]:
    """Process the transpilation of the circuits.

    Args:
        circuits (list[QuantumCircuit]):
            The circuits to be transpiled.
        transpile_args (TranspileArgs):
            The transpile arguments.
        backend (Backend):
            The backend to be used for transpilation.
        passmanager_pair (tuple[str, PassManager] | None):
            The passmanager name and the passmanager to be used.
        exp_id (str):
            The experiment ID, used for warning messages.
        multiprocess (bool, optional):
            Whether to use multiprocessing. Defaults to False.
        pbar (tqdm.tqdm | None, optional):
            The progress bar. Defaults to None.

    Returns:
        list[QuantumCircuit]: The transpiled circuits.
    """
    if passmanager_pair is None:
        return inner_process_transpile_func(circuits, transpile_args, backend, multiprocess, pbar)

    return inner_process_passmanager(
        circuits, transpile_args, passmanager_pair, exp_id, multiprocess, pbar
    )


def process_duo_transpilation(
    circuits: list[QuantumCircuit],
    backend: Backend,
    transpile_args: TranspileArgs,
    passmanager_pair: tuple[str, PassManager] | None,
    second_backend: Backend | None,
    second_transpile_args: TranspileArgs | None,
    second_passmanager_pair: tuple[str, PassManager] | None,
    times: int,
    # other args
    exp_id: str,
    multiprocess: bool = False,
    pbar: tqdm.tqdm | None = None,
) -> list[QuantumCircuit]:
    """Process the transpilation of the circuits between 2 list of quantum circuits
    with respecting to the given backend and transpile arguments.

    Args:
        circuits (list[QuantumCircuit]):
            The circuits to be transpiled.
        backend (Backend):
            The backend to be used for transpilation.
        transpile_args (TranspileArgs):
            The transpile arguments.
        passmanager_pair (tuple[str, PassManager] | None):
            The passmanager name and the passmanager to be used.
        second_backend (Backend | None):
            The backend to be used for transpilation of the second list of circuits.
        second_transpile_args (TranspileArgs | None):
            The transpile arguments of the second circuit.
        second_passmanager_pair (tuple[str, PassManager] | None):
            The passmanager name and the passmanager to be used for the second list of circuits.
        times (int):
            The number of circuits for each quantum circuit.

        exp_id (str):
            The experiment ID, used for warning messages.
        multiprocess (bool, optional):
            Whether to use multiprocessing. Defaults to False.
        pbar (tqdm.tqdm | None, optional):
            The progress bar. Defaults to None.

    Returns:
        list[QuantumCircuit]: The transpiled circuits.
    """
    if len(circuits) != 2 * times:
        raise ValueError(
            "The number of circuits should be 2 times the 'times' argument."
            + f" Get {len(circuits)}, expect {2 * times}."
        )

    transpiled_circs = process_transpilation(
        circuits=circuits[:times],
        backend=backend,
        transpile_args=transpile_args,
        passmanager_pair=passmanager_pair,
        exp_id=exp_id,
        multiprocess=multiprocess,
        pbar=pbar,
    )

    assert len(transpiled_circs) == times, (
        "The number of transpiled circuits is not correct."
        + f" Get {len(transpiled_circs)}, expect {times}."
    )

    actual_second_backend = backend if second_backend is None else second_backend
    if second_passmanager_pair is not None:
        ignored_transpile_args = (
            transpile_args if second_transpile_args is None else second_transpile_args
        )
        transpiled_circs += inner_process_passmanager(
            circuits[times:],
            ignored_transpile_args,
            second_passmanager_pair,
            exp_id,
            multiprocess,
            pbar,
        )
    elif second_transpile_args is not None:
        transpiled_circs += inner_process_transpile_func(
            circuits[times:], second_transpile_args, actual_second_backend, multiprocess, pbar
        )
    elif passmanager_pair is not None:
        transpiled_circs += inner_process_passmanager(
            circuits[times:], transpile_args, passmanager_pair, exp_id, multiprocess, pbar
        )
    else:
        transpiled_circs += inner_process_transpile_func(
            circuits[times:], transpile_args, actual_second_backend, multiprocess, pbar
        )

    assert len(transpiled_circs) == 2 * times, (
        "The number of transpiled circuits is not correct, "
        + f"expected {2 * times}, but got {len(transpiled_circs)}."
    )

    return transpiled_circs


def make_statesheet(
    exp_name: str,
    args: ArgumentsPrototype,
    commons: Commonparams,
    outfields: dict[str, str],
    beforewards: Before,
    afterwards: After,
    reports: AnalysesContainer,
    report_expanded: bool = False,
    hoshi: bool = False,
) -> Hoshi:
    """Show the state of experiment.

    Args:
        exp_name (str): Name of the experiment.
        args (ArgumentsPrototype): Arguments of the experiment.
        commons (Commonparams): Common parameters of the experiment.
        outfields (dict[str, str]): Unused arguments.
        beforewards (Before): Beforewards of the experiment.
        afterwards (After): Afterwards of the experiment.
        reports (AnalysesContainer): Reports of the experiment.
        report_expanded (bool, optional): Show more infomation. Defaults to False.
        hoshi (bool, optional): Showing name of Hoshi. Defaults to False.

    Returns:
        Hoshi: Statesheet of experiment.
    """

    info = Hoshi(
        [
            ("h1", f"{exp_name} with exp_id={commons.exp_id}"),
        ],
        name="Hoshi" if hoshi else "QurryExperimentSheet",
    )
    info.newline(("itemize", "arguments"))
    for k, v in args.asdict().items():
        info.newline(("itemize", str(k), str(v), "", 2))

    info.newline(("itemize", "commonparams"))
    for k, v in commons.asdict().items():
        info.newline(
            (
                "itemize",
                str(k),
                str(v),
                (),
                2,
            )
        )

    info.newline(
        (
            "itemize",
            "outfields",
            len(outfields),
            "Number of unused arguments.",
            1,
        )
    )
    for k, v in outfields.items():
        info.newline(("itemize", str(k), v, "", 2))

    info.newline(("itemize", "beforewards"))
    for k, v in beforewards.asdict().items():
        if isinstance(v, str):
            info.newline(("itemize", str(k), str(v), "", 2))
        else:
            info.newline(("itemize", str(k), len(v), f"Number of {k}", 2))

    info.newline(("itemize", "afterwards"))
    for k, v in afterwards.asdict().items():
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

    info.newline(("itemize", "reports", len(reports), "Number of analysis.", 1))
    if report_expanded:
        for ser, item in reports.items():
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


def create_save_location(
    save_location: str | Path | None, commons: Commonparams | None = None
) -> Path:
    """Create a save location for the experiment.

    Args:
        save_location (str | Path | None): The save location of the experiment.
        commons (Commonparams | None, optional):
            The common parameters of the experiment.
            It is used to get the default save location if `save_location` is None.

    Returns:
        Path: The save location as a Path object.

    Raises:
        ValueError:
            If `save_location` is not a Path or str,
            or if it is None and `commons` is also None.
    """
    if isinstance(save_location, Path):
        return save_location
    if isinstance(save_location, str):
        return Path(save_location)
    if save_location is None and commons is not None:
        if commons.save_location is None:
            raise ValueError("save_location is None, please provide a valid save_location")
        return Path(commons.save_location)

    raise ValueError(f"save_location must be Path or str, not {type(save_location)}")


def folder_with_repeat_times(exp_name: str, repeat_times: int) -> str:
    """Create a folder with repeat times.

    Args:
        exp_name (str): The name of the experiment.
        repeat_times (int, optional): The repeat times of the experiment. Defaults to 1.

    Returns:
        str: The folder name with repeat times.
    """
    return f"{exp_name}.{str(repeat_times).rjust(RJUST_LEN, '0')}"


def decide_folder_and_filename(commons: Commonparams, args: ArgumentsPrototype) -> tuple[str, str]:
    """Decide the folder and filename for the experiment.

    Args:
        commons (Commonparams): The common parameters of the experiment.
        args (ArgumentsPrototype): The arguments of the experiment.

    Returns:
        tuple[str, str]: The folder and filename for the experiment.
    """

    if (
        commons.serial is not None
        and commons.exp_id is not None
        and commons.summoner_name is not None
    ):
        return (
            commons.summoner_name,
            f"index={commons.serial}.id={commons.exp_id}",
        )

    if commons.folder is not None:
        return str(commons.folder), f"id={commons.exp_id}"

    repeat_times = 1
    folder = folder_with_repeat_times(args.exp_name, repeat_times)
    while os.path.exists(folder):
        repeat_times += 1
        folder = folder_with_repeat_times(args.exp_name, repeat_times)
    return folder, f"id={commons.exp_id}"


def ensure_runnable_backend(backend: Backend | str) -> None:
    """Ensure the backend is runnable.

    Args:
        backend (Backend | str): The backend to be checked.

    Raises:
        ValueError: If the backend is given as a string.
        ValueError: If the backend is not an instance of Backend.
        UnrunableBackendError: If the backend is unrunable.
    """

    if isinstance(backend, str):
        raise ValueError(
            "The backend is given as a string. "
            + "If you just read the experiment from output files, "
            + "please replace it first by method 'replace_backend' of the experiment instance."
        )
    if not isinstance(backend, Backend):
        raise ValueError(
            f"Require a valid backend to run the experiment. Got {backend} as {type(backend)}."
        )

    if not hasattr(backend, "run"):
        raise UnrunableBackendError(ABOUT_UNRUNNABLE_THIRD_PARTY.format(backend))
    try:
        # pylint: disable=import-outside-toplevel
        from qiskit_ibm_runtime import IBMBackend
        # pylint: enable=import-outside-toplevel

        if isinstance(backend, IBMBackend):
            raise UnrunableBackendError(ABOUT_UNRUNNABLE_IBM_BACKEND.format(backend))
    except ImportError:
        pass
