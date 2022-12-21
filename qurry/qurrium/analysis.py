from typing import Optional, NamedTuple, Iterable, Any
from abc import abstractmethod, abstractproperty
from datetime import datetime

from ..mori import jsonablize


class AnalysisPrototype():
    """The container for the analysis of :cls:`QurryExperiment`."""

    __name__ = 'AnalysisPrototype'

    class analysisHeader(NamedTuple):
        """Construct the experiment's output. 
        A standard `analysis` namedtuple will contain ['serial', 'time', 'summoner', 'run_log', 'sideProduct']
        for more information storing. If it does not contain will raise `QurryInvalidInherition`.
        """

        serial: int
        """Serial Number of analysis."""
        datetime: str
        """Written time of analysis."""
        summoner: Optional[tuple] = None
        """Which multiManager makes this analysis. If it's an independent one, then usr the default 'None'."""
        log: dict = {}
        """Other info will be recorded."""

    @abstractmethod
    class analysisInput(NamedTuple):
        """To set the analysis."""

    @abstractmethod
    class analysisContent(NamedTuple):
        sampling: int
        """Number of circuit been repeated."""

    @classmethod
    def input_filter(cls, *args, **kwargs) -> tuple[analysisInput, dict[str, Any]]:
        if len(args) > 0:
            raise ValueError(
                "analysis filter can't be initialized with positional arguments.")
        infields = {}
        outfields = {}
        for k in kwargs:
            if k in cls.analysisInput._fields:
                infields[k] = kwargs[k]
            else:
                outfields[k] = kwargs[k]

        return cls.analysisInput(**infields), outfields

    @classmethod
    def content_filter(cls, *args, **kwargs) -> tuple[analysisContent, dict[str, Any]]:
        if len(args) > 0:
            raise ValueError(
                "analysis content filter can't be initialized with positional arguments.")
        infields = {}
        outfields = {}
        for k in kwargs:
            if k in cls.analysisContent._fields:
                infields[k] = kwargs[k]
            else:
                outfields[k] = kwargs[k]

        return cls.analysisContent(**infields), outfields

    @abstractproperty
    def default_side_product_fields(self) -> Iterable[str]:
        """The fields that will be stored as side product."""

    def __init__(
        self,
        serial: int = None,
        summoner: Optional[tuple] = None,
        log: dict = {},
        side_product_fields: Iterable[str] = None,
        **otherArgs,
    ):

        self.header = self.analysisHeader(
            serial=serial,
            datetime=datetime.now().strftime("%Y-%m-%d_%H:%M:%S"),
            summoner=summoner,
            log=log,
        )
        self.input, outfields = self.input_filter(**otherArgs)
        self.content, self.outfields = self.content_filter(**outfields)
        self.side_product_fields = (
            self.default_side_product_fields if side_product_fields is None else side_product_fields)

    def __repr__(self) -> str:
        return (
            f"<{self.__name__} with serial={self.header.serial}, " +
            f"{self.input.__repr__()}, " +
            f"{self.content.__repr__()}, " +
            f"{len(self.outfields)} unused arguments>")

    def export(self) -> tuple[dict[str, Any], dict[str, Any]]:
        """Export the analysis as main and side product dict.

        ```python
        main = { ...quantities, 'input': { ... }, 'header': { ... }, }
        side = { 'dummyz1': ..., 'dummyz2': ..., ..., 'dummyzm': ... }

        ```

        Returns:
            tuple[dict[str, Any], dict[str, Any]]: `main` and `side` product dict.

        """

        tales = {}
        main = {}
        for k, v in self.content._asdict().items():
            if k in self.side_product_fields:
                tales[k] = v
            else:
                main[k] = v
        main['input'] = self.input._asdict()
        main['header'] = self.header._asdict()

        main = jsonablize(main)
        tales = jsonablize(tales)
        return main, tales

    @classmethod
    def read(cls, main: dict[str, Any], side: dict[str, Any]) -> 'AnalysisPrototype':
        """Read the analysis from main and side product dict."""
        for k in ('input', 'header') + cls.analysisContent._fields:
            if k in main or k in side:
                ...
            else:
                raise ValueError(
                    f"Analysis main product must contain '{k}' key.")

        content = {k: v for k, v in main.items(
        ) if k not in ('input', 'header')}
        instance = cls(**main['header'], **main['input'], **content, **side)
        return instance


class QurryAnalysis(AnalysisPrototype):

    __name__ = 'QurryAnalysis'

    class analysisInput(NamedTuple):
        """To set the analysis."""
        ultimate_question: str
        """ULtImAte QueStIoN."""
    class analysisContent(NamedTuple):
        utlmatic_answer: int
        """~Answer to the ultimate question of life the universe and everything.~"""
        dummy: int
        """Just a dummy field."""

    @property
    def default_side_product_fields(self) -> Iterable[str]:
        """The fields that will be stored as side product."""
        return ['dummy']
