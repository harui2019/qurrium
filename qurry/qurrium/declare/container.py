from qiskit import QuantumCircuit
from qiskit.result import Result
from qiskit.providers import Backend
from qiskit.providers.aer import AerSimulator
from qiskit.providers.ibmq import AccountProvider

from pathlib import Path
from typing import Literal, Union, Optional, NamedTuple, Hashable, overload
from abc import abstractmethod, abstractstaticmethod
from collections import namedtuple
import gc

from ...mori import jsonablize


class QurryArgs:
    __name__ = 'QurryArgs'

    @abstractstaticmethod
    class argsCore(NamedTuple):
        """Construct the experiment's parameters."""

    @staticmethod
    class argsMain(NamedTuple):
        # ID of experiment.
        expID: Optional[str] = None

        # Qiskit argument of experiment.
        # Multiple jobs shared
        shots: int = 1024
        backend: Backend = AerSimulator()
        provider: Optional[AccountProvider] = None
        runArgs: dict[str, any] = {}

        # Single job dedicated
        runBy: str = "gate"
        decompose: Optional[int] = 2
        transpileArgs: dict[str, any] = {}

        # Other arguments of experiment
        drawMethod: str = 'text'
        tags: tuple[str] = ()
        resoureControl: dict[str, any] = {}

        saveLocation: Union[Path, str] = Path('./')
        exportLocation: Path = Path('./')

        expIndex: Optional[int] = None

    _v3ArgsMapping = {
        'runConfig': 'runArgs',
    }

    class argsExport(NamedTuple):
        expsID: str = ''
        args: dict[str, any] = {}
        outfields: dict[str, any] = {}

    @classmethod
    def corefilter(cls, *args, **kwargs) -> tuple[argsCore, dict[str, any]]:
        if len(args) > 0:
            raise ValueError(
                "argsCore filter can't be initialized with positional arguments.")
        infields = {}
        outfields = {}
        for k in kwargs:
            if k in cls.argsMain._fields:
                infields[k] = kwargs[k]
            else:
                outfields[k] = kwargs[k]

        return cls.argsCore(**infields), outfields

    def __init__(self, *args, **kwargs) -> None:

        if len(args) > 0:
            raise ValueError(
                f"{self.__name__} can't be initialized with positional arguments.")

        self.combined = namedtuple(
            typename=QurryArgs.__name__+'Combined',
            field_names=self.argsMain._fields+self.argsCore._fields,
            defaults=list(self.argsMain._field_defaults.values()) +
            list(self.argsCore._field_defaults.values()),
        )

        infields = {}
        outfields = {}
        for k in kwargs:
            if k in self.combined._fields:
                infields[k] = kwargs[k]
            else:
                outfields[k] = kwargs[k]

        self.main: Union[QurryArgs.argsMain,
                         QurryArgs.argsCore] = self.combined(*args, **kwargs)
        self.outfields: dict[str, any] = outfields

    def export(self) -> argsExport:

        args = jsonablize(self.main._asdict())

        return self.argsExport(
            expsID=self.main.expsID,
            args=args,
            outfields=jsonablize(self.outfields)
        )

    def __repr__(self) -> str:
        return f"<{self.__name__} with {self.main.__repr__()} and {len(self.outfields)} unused arguments>"


class QurriumArgs(QurryArgs):
    __name__ = 'QurriumArgs'

    class argsCore(NamedTuple):
        expsName: str = 'exps'
        wave: Union[QuantumCircuit, any, None] = None
        sampling: int = 1


class QurryExpsData:
    __name__ = 'QurryExpsData'

    @abstractmethod
    class expsCore(NamedTuple):
        """Construct the experiment's output."""

    class expsMain(NamedTuple):
        # Measurement result
        circuit: list[QuantumCircuit] = []
        figRaw: list[str] = []
        figTranspile: list[str] = []
        result: list[Result] = []
        counts: list[dict[str, int]] = []

        # Export data
        jobID: str = ''
        expsName: str = 'exps'

        # side product
        sideProduct: dict = {}

    _expExceptKeys = ['sideProduct', 'result']

    class expsExport(NamedTuple):
        expsName: str = 'exps'
        legacy: dict[str, any] = {}
        tales: dict[str, any] = {}
        outfields: dict[str, any] = {}

    @classmethod
    def corefilter(cls, *args, **kwargs) -> tuple[expsCore, dict[str, any]]:
        if len(args) > 0:
            raise ValueError(
                "expsCore filter can't be initialized with positional arguments.")
        infields = {}
        outfields = {}
        for k in kwargs:
            if k in cls.expsMain._fields:
                infields[k] = kwargs[k]
            else:
                outfields[k] = kwargs[k]

        return cls.expsCore(**infields), outfields

    def __init__(self, *args, **kwargs) -> None:

        if len(args) > 0:
            raise ValueError(
                f"{self.__name__} can't be initialized with positional arguments.")

        self.combined = namedtuple(
            typename=QurryArgs.__name__+'Combined',
            field_names=self.expsMain._fields+self.expsCore._fields,
            defaults=list(self.expsMain._field_defaults.values()) +
            list(self.expsCore._field_defaults.values()),
        )

        infields = {}
        outfields = {}
        for k in kwargs:
            if k in self.combined._fields:
                infields[k] = kwargs[k]
            else:
                outfields[k] = kwargs[k]

        self.main: Union[QurryExpsData.expsMain,
                         QurryExpsData.expsCore] = self.combined(*args, **kwargs)
        self.outfields: dict[str, any] = outfields

    def export(self) -> expsExport:

        # for writeLegacy, or new name poet
        # for readLegacy, or new name read
        rawData = self.main._asdict()
        legacy = {}
        tales = {}
        expsName = self.main.expsName
        for k, v in rawData.items():
            if k == 'sideProduct':
                tales = v
            elif k in self._expExceptKeys:
                ...
            else:
                legacy[k] = v
        legacy = jsonablize(legacy)
        tales = jsonablize(tales)

        return self.expsExport(expsName=expsName, legacy=legacy, tales=tales, outfields=jsonablize(self.outfields))

    def __setitem__(self, key, value) -> None:
        if key in self.combined._fields:
            self.main = self.main._replace(**{key: value})
            gc.collect()
        else:
            raise ValueError(
                f"{key} is not a valid field of {self.combined.__name__}")

    def __repr__(self) -> str:
        return f"<{self.__name__} with {len(self.combined._fields)} datasets and {len(self.outfields)} extra datasets>"


class QurriumExpsData(QurryExpsData):
    __name__ = 'QurriumExpsData'

    class expsCore(NamedTuple):
        ...
