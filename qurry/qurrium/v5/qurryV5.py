from qiskit import (
    execute, transpile, QuantumRegister, QuantumCircuit
)
from qiskit_aer import AerProvider
from qiskit.quantum_info import Operator
from qiskit.circuit import Gate, Instruction
from qiskit.result import Result
from qiskit.providers import Backend, JobError, JobStatus
from qiskit.providers.ibmq import IBMQBackend, IBMQJobManager, AccountProvider
from qiskit.providers.ibmq.managed import (
    ManagedJobSet,
    # ManagedJob,
    ManagedResults,
    IBMQManagedResultDataNotAvailable,
    # IBMQJobManagerInvalidStateError,
    # IBMQJobManagerUnknownJobSet
)

import glob
import json
import gc
import warnings
import datetime
import time
import os
from uuid import uuid4
from pathlib import Path
from typing import Literal, Union, Optional, NamedTuple, Hashable, Iterable, Type, overload
from abc import abstractmethod, abstractclassmethod, abstractproperty
from matplotlib.figure import Figure

from ...mori import (
    defaultConfig,
    attributedDict,
    defaultConfig,
    syncControl,
    jsonablize,
    quickJSONExport,
    sortHashableAhead,
    TagMap,
)
from ...mori.type import TagMapType
from ...util import Gajima, ResoureWatch

from ..declare.default import (
    transpileConfig,
    managerRunConfig,
    runConfig,
    ResoureWatchConfig,
    containChecker,
)
from .experiment import ExperimentPrototype
from .container import WaveContainer

from ..construct import decomposer
from ...exceptions import (
    UnconfiguredWarning,
    QurryInheritionNoEffect,
)
from ..declare.type import Quantity, Counts, waveGetter, waveReturn

# Qurry V0.5.0 - a Qiskit Macro


def defaultCircuit(numQubit: int) -> QuantumCircuit:
    return QuantumCircuit(
        numQubit, numQubit, name=f'qurry_default_{numQubit}')


DefaultResourceWatch = ResoureWatch()


class QurryV5Prototype:
    """QurryV5
    A qiskit Macro.
    ~Create countless adventure, legacy and tales.~
    """
    __version__ = (0, 5, 0)
    __name__ = 'QurryV5Prototype'
    shortName = 'qurry'

    # container
    @classmethod
    @abstractproperty
    def experiment(cls) -> Type[ExperimentPrototype]:
        """The container class responding to this QurryV5 class.
        """

    # @abstractproperty
    # def multimanager(self) -> property:
    #     return property()

    # Wave
    def add(
        self,
        wave: QuantumCircuit,
        key: Optional[Hashable] = None,
        replace: Literal[True, False, 'duplicate'] = False,
    ) -> Hashable:
        """Add new wave function to measure.

        Args:
            waveCircuit (QuantumCircuit): The wave functions or circuits want to measure.
            key (Optional[Hashable], optional): Given a specific key to add to the wave function or circuit,
                if `key == None`, then generate a number as key.
                Defaults to `None`.
            replace (Literal[True, False, &#39;duplicate&#39;], optional): 
                If the key is already in the wave function or circuit,
                then replace the old wave function or circuit when `True`,
                or duplicate the wave function or circuit when `'duplicate'`,
                otherwise only changes `.lastwave`.
                Defaults to `False`.

        Returns:
            Optional[Hashable]: Key of given wave function in `.waves`.
        """
        return self.waves.add(wave, key, replace)

    def get_wave(
        self,
        wave: Union[list[Hashable], Hashable, None] = None,
        runBy: Optional[Literal['gate', 'operator',
                                'instruction', 'copy']] = None,
        backend: Optional[Backend] = AerProvider(
        ).get_backend('aer_simulator'),
    ) -> Union[list[Union[Gate, Operator, Instruction, QuantumCircuit]], Union[Gate, Operator, Instruction, QuantumCircuit]]:
        """Parse wave Circuit into `Instruction` as `Gate` or `Operator` on `QuantumCircuit`.

        Args:
            wave (Optional[Hashable], optional):
                The key of wave in 'fict' `.waves`.
                If `wave==None`, then chooses `.lastWave` automatically added by last calling of `.addWave`.
                Defaults to None.
            runBy (Optional[str], optional):
                Export as `Gate`, `Operator`, `Instruction` or a copy when input is `None`.
                Defaults to `None`.
            backend (Optional[Backend], optional):
                Current backend which to check whether exports to `IBMQBacked`,
                if does, then no matter what option input at `runBy` will export `Gate`.
                Defaults to AerProvider().get_backend('aer_simulator').

        Returns:
            waveReturn: The result of the wave as `Gate` or `Operator`.
        """
        return self.waves.get_wave(wave, runBy, backend)

    def operator(
        self,
        wave: Union[list[Hashable], Hashable, None] = None,
    ) -> Union[list[Operator], Operator]:
        """Export wave function as `Operator`.

        Args:
            wave (Optional[Hashable], optional):
                The key of wave in 'fict' `.waves`.
                If `wave==None`, then chooses `.lastWave` automatically added by last calling of `.addWave`.
                Defaults to None.

        Returns:
            Operator: The operator of wave function.
        """
        return self.waves.operator(wave)

    def gate(
        self,
        wave: Union[list[Hashable], Hashable, None] = None,
    ) -> Union[list[Gate], Gate]:
        """Export wave function as `Operator`.

        Args:
            wave (Optional[Hashable], optional):
                The key of wave in 'fict' `.waves`.
                If `wave==None`, then chooses `.lastWave` automatically added by last calling of `.addWave`.
                Defaults to None.

        Returns:
            Operator: The operator of wave function.
        """
        return self.waves.gate(wave)

    def copy_circuit(
        self,
        wave: Union[list[Hashable], Hashable, None] = None,
    ) -> Union[list[Gate], Gate]:
        """Export wave function as `Operator`.

        Args:
            wave (Optional[Hashable], optional):
                The key of wave in 'fict' `.waves`.
                If `wave==None`, then chooses `.lastWave` automatically added by last calling of `.addWave`.
                Defaults to None.

        Returns:
            Operator: The operator of wave function.
        """
        return self.waves.copy_circuit(wave)

    def instruction(
        self,
        wave: Union[list[Hashable], Hashable, None] = None,
    ) -> Union[list[Gate], Gate]:
        """Export wave function as `Operator`.

        Args:
            wave (Optional[Hashable], optional):
                The key of wave in 'fict' `.waves`.
                If `wave==None`, then chooses `.lastWave` automatically added by last calling of `.addWave`.
                Defaults to None.

        Returns:
            Operator: The operator of wave function.
        """
        return self.waves.instruction(wave)

    def has(
        self,
        wavename: Hashable,
    ) -> bool:
        """Is there a wave with specific name.

        Args:
            wavename (Hashable): Name of wave which is used in `.waves`

        Returns:
            bool: Exist or not.
        """
        return self.waves.has(wavename)

    def call(self, wavename: Hashable) -> Union[list[QuantumCircuit], QuantumCircuit]:
        """Call the wave function by name.

        Args:
            wavename (Hashable): Name of wave which is used in `.waves`

        Returns:
            QuantumCircuit: The wave function.
        """
        return self.waves.call(wavename)

    @property
    def lastWaveID(self) -> Hashable:
        """The last wave function be called."""
        return self.waves.lastWaveID

    @property
    def lastWave(self) -> Optional[QuantumCircuit]:
        """The last wave function be called.
        Replace the property :prop:`waveNow`. in :cls:`QurryV4`"""
        return self.waves.lastWave

    def __init__(
        self,
        *waves: Union[QuantumCircuit, tuple[Hashable, QuantumCircuit]],
        resourceWatch: ResoureWatch = DefaultResourceWatch,
    ) -> None:

        if isinstance(resourceWatch, ResoureWatch):
            self.resourceWatch = resourceWatch
        else:
            raise TypeError(
                f"resourceWatch must be a ResoureWatch instance, not {type(resourceWatch)}")

        self.waves = WaveContainer()
        """The wave functions container."""
        for w in waves:
            if isinstance(w, QuantumCircuit):
                self.add(w)
            elif isinstance(w, tuple):
                self.add(w[0], w[1])
            else:
                warnings.warn(
                    f"'{w}' is a '{type(w)}' instead of 'QuantumCircuit' or 'tuple' " +
                    "contained hashable key and 'QuantumCircuit', skipped to be adding.",
                    category=TypeError)
        self.exps: dict[str, QurryV5Prototype.experiment] = {}
        """The experiments container."""

        self.multiJob = None
        """The last multiJob be called.
        # TODO: This is a temporary useless until `multimanager` completed.
        Replace the property :prop:`multiNow`. in :cls:`QurryV4`"""

    # state checking
    @property
    def lastExps(self) -> Optional['QurryV5Prototype.experiment']:
        """The last experiment be executed.
        Replace the property :prop:`now`. in :cls:`QurryV4`"""
        if self.lastID == '':
            return None
        else:
            return self.exps[self.lastID]
