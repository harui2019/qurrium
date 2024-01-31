"""
================================================================
Waves Qurry (:mod:`qurry.qurrium.wavesqurry`)
================================================================

It is only for pendings and retrieve to remote backend.
"""

from typing import Union, Optional, Hashable, Iterable, Any
from pathlib import Path
import tqdm

from qiskit import QuantumCircuit

from .experiment import WavesQurryExperiment
from ..qurrium import QurryPrototype
from ..container import ExperimentContainer


class WavesExecuter(QurryPrototype):
    """The pending and retrieve executer for waves."""

    @staticmethod
    def experiment(*args, **kwargs) -> WavesQurryExperiment:
        """The container class responding to this QurryV5 class."""
        return WavesQurryExperiment(*args, **kwargs)

    exps: ExperimentContainer[WavesQurryExperiment]

    def params_control(
        self,
        wave_key: Hashable = None,
        exp_name: str = "exps",
        waves: Optional[list[Hashable]] = None,
        **other_kwargs: Any,
    ) -> tuple[
        WavesQurryExperiment.Arguments,
        WavesQurryExperiment.Commonparams,
        dict[str, Any],
    ]:
        """Handling all arguments and initializing a single experiment.

        Args:
            wave_key (Union[QuantumCircuit, int, None], optional):
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
            other_kwargs (Any):
                Other arguments.

        Returns:
            dict: The export will be processed in `.paramsControlCore`
        """
        if waves is None:
            waves = []

        for w in waves:
            if not self.has(w):
                raise ValueError(f"| The wave '{w}' is not in `.waves`.")

        if len(waves) > 0:
            wave_key = None
        else:
            raise ValueError(
                "| This is Qurry required multiple waves gvien in `waves` to be measured."
            )

        return self.experiment.filter(
            exp_name=exp_name,
            wave_key=wave_key,
            waves=waves,
            **other_kwargs,
        )

    def method(
        self,
        exp_id: Hashable,
        _pbar: Optional[tqdm.tqdm] = None,
    ) -> list[QuantumCircuit]:
        assert exp_id in self.exps
        assert self.exps[exp_id].commons.exp_id == exp_id
        current_exp = self.exps[exp_id]
        args: WavesQurryExperiment.Arguments = self.exps[exp_id].args
        _commons: WavesQurryExperiment.Commonparams = self.exps[exp_id].commons

        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str(f"Loading specified {len(args.waves)} circuits.")
        circs = [self.waves[c].copy() for c in args.waves]
        current_exp["exp_name"] = f"{args.exp_name}-with{len(circs)}circs"

        return circs

    def measure(
        self,
        waves: Iterable[Hashable],
        exp_name: str = "exps",
        *,
        save_location: Optional[Union[Path, str]] = None,
        mode: str = "w+",
        indent: int = 2,
        encoding: str = "utf-8",
        jsonablize: bool = False,
        **other_kwargs: Any,
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
            exp_name (str, optional):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.
            save_location (Optional[Union[Path, str]], optional):
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

            other_kwargs (Any):
                Other arguments in :meth:`result`.

        Returns:
            dict: The output.
        """

        id_now = self.result(
            wave=None,
            waves=waves,
            exp_name=exp_name,
            save_location=None,
            **other_kwargs,
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
