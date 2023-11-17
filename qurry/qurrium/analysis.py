"""
================================================================
Analysis Instance
(:mod:`qurry.qurrium.analysis`)
================================================================

"""
from typing import Optional, NamedTuple, Iterable, Any
from abc import abstractmethod
import warnings

from ..capsule import jsonablize
from ..capsule.hoshi import Hoshi
from ..exceptions import QurryInvalidInherition
from ..tools.datetime import current_time


class AnalysisPrototype:
    """The instance for the analysis of :cls:`QurryExperiment`."""

    __name__ = "AnalysisPrototype"

    class AnalysisHeader(NamedTuple):
        """Construct the experiment's output.
        A standard `analysis` namedtuple will contain
        ['serial', 'time', 'summoner', 'run_log', 'sideProduct']
        for more information storing.
        If it does not contain will raise `QurryInvalidInherition`.
        """

        serial: int
        """Serial Number of analysis."""
        datetime: str
        """Written time of analysis."""
        summoner: Optional[tuple] = None
        """Which multiManager makes this analysis. 
        If it's an independent one, then usr the default 'None'."""
        log: dict = {}
        """Other info will be recorded."""

    @abstractmethod
    class AnalysisInput(NamedTuple):
        """To set the analysis."""

    @abstractmethod
    class AnalysisContent(NamedTuple):
        """To set the analysis."""

        sampling: int
        """Number of circuit been repeated."""

    @classmethod
    def input_filter(cls, *args, **kwargs) -> tuple[AnalysisInput, dict[str, Any]]:
        """Filter the input arguments for analysis.

        Returns:
            tuple[AnalysisInput, dict[str, Any]]: The filtered input and unused arguments.
        """
        if len(args) > 0:
            raise ValueError(
                "analysis filter can't be initialized with positional arguments."
            )
        infields = {}
        outfields = {}

        for k, v in kwargs.items():
            if k in cls.AnalysisInput._fields:
                infields[k] = v
            else:
                outfields[k] = v

        return cls.AnalysisInput(**infields), outfields

    @classmethod
    def content_filter(cls, *args, **kwargs) -> tuple[AnalysisContent, dict[str, Any]]:
        """Filter the content arguments for analysis.

        Returns:
            tuple[AnalysisContent, dict[str, Any]]: The filtered content and unused arguments.
        """
        if len(args) > 0:
            raise ValueError(
                "analysis content filter can't be initialized with positional arguments."
            )
        infields = {}
        outfields = {}
        for k, v in kwargs.items():
            if k in cls.AnalysisContent._fields:
                infields[k] = v
            else:
                outfields[k] = v

        return cls.AnalysisContent(**infields), outfields

    @property
    @abstractmethod
    def default_side_product_fields(self) -> Iterable[str]:
        """The fields that will be stored as side product."""

    def __init__(
        self,
        serial: int = None,
        summoner: Optional[tuple] = None,
        log: Optional[dict[str, Any]] = None,
        side_product_fields: Iterable[str] = None,
        **otherArgs,
    ):
        if log is None:
            log = {}
        self.header = self.AnalysisHeader(
            serial=serial,
            datetime=current_time(),
            summoner=summoner,
            log=log,
        )
        self.input, outfields = self.input_filter(**otherArgs)
        self.content, self.outfields = self.content_filter(**outfields)
        self.side_product_fields = (
            self.default_side_product_fields
            if side_product_fields is None
            else side_product_fields
        )

        duplicate_fields = set(self.AnalysisInput._fields) & set(
            self.AnalysisContent._fields
        )
        if len(duplicate_fields) > 0:
            raise QurryInvalidInherition(
                f"{self.__name__}.AnalysisInput and {self.__name__}"
                + f".AnalysisContent should not have same fields: {duplicate_fields}."
            )

    def __repr__(self) -> str:
        return (
            f"<{self.__name__} with serial={self.header.serial}, "
            + f"{self.input.__repr__()}, "
            + f"{self.content.__repr__()}, "
            + f"{len(self.outfields)} unused arguments>"
        )

    def statesheet(
        self,
        hoshi: bool = False,
    ) -> Hoshi:
        """Generate the state sheet of the analysis.

        Args:
            hoshi (bool, optional):
                If True, show Hoshi name in statesheet. Defaults to False.
        Returns:
            Hoshi: The state sheet of the analysis.
        """
        info = Hoshi(
            [
                ("h1", f"{self.__name__} with serial={self.header.serial}"),
            ],
            name="Hoshi" if hoshi else "QurryAnalysisSheet",
        )
        info.newline(("itemize", "header"))
        for k, v in self.header._asdict().items():
            info.newline(("itemize", str(k), str(v), "", 2))

        info.newline(("itemize", "input"))
        for k, v in self.input._asdict().items():
            info.newline(
                (
                    "itemize",
                    str(k),
                    str(v),
                    (
                        ""
                        if k != "expID"
                        else (
                            "This is ID is generated by Qurry "
                            + "which is different from 'jobID' for pending."
                        )
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
            info.newline(("itemize", str(k), str(v), "", 2))

        info.newline(("itemize", "content"))
        for k, v in self.content._asdict().items():
            info.newline(("itemize", str(k), str(v), "", 2))

        return info

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
        main["input"] = self.input._asdict()
        main["header"] = self.header._asdict()

        main = jsonablize(main)
        tales = jsonablize(tales)
        return main, tales

    @classmethod
    def read(cls, main: dict[str, Any], side: dict[str, Any]) -> "AnalysisPrototype":
        """Read the analysis from main and side product dict.

        Args:
            main (dict[str, Any]): The main product dict.
            side (dict[str, Any]): The side product dict.

        Returns:
            AnalysisPrototype: The analysis instance.
        """
        lost_key = []
        for k in ("input", "header") + cls.AnalysisContent._fields:
            if not (k in main or k in side):
                lost_key.append(k)

        if len(lost_key) > 0:
            print(
                f"| Analysis main product may lost the following keys: {lost_key}."
            )

        content = {k: v for k, v in main.items() if k not in ("input", "header")}
        instance = cls(**main["header"], **main["input"], **content, **side)
        return instance


class QurryAnalysis(AnalysisPrototype):
    """Example of QurryAnalysis."""

    __name__ = "QurryAnalysis"

    class AnalysisInput(NamedTuple):
        """To set the analysis."""

        ultimate_question: str
        """ULtImAte QueStIoN."""

    class AnalysisContent(NamedTuple):
        """To set the analysis."""

        utlmatic_answer: int
        """~The Answer to the Ultimate Question of Life, The Universe, and Everything.~"""
        dummy: int
        """Just a dummy field."""

    @property
    def default_side_product_fields(self) -> Iterable[str]:
        """The fields that will be stored as side product."""
        return ["dummy"]
