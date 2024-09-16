"""
================================================================
Analysis Instance
(:mod:`qurry.qurrium.analysis`)
================================================================

"""

from typing import Optional, NamedTuple, Iterable, Any
from abc import abstractmethod
from pathlib import Path
import json
import gc

from ...capsule import jsonablize
from ...capsule.hoshi import Hoshi
from ...exceptions import QurryInvalidInherition
from ...tools.datetime import current_time


class AnalysisPrototype:
    """The instance for the analysis of :cls:`QurryExperiment`."""

    __name__ = "AnalysisPrototype"

    class AnalysisHeader(NamedTuple):
        """Construct the experiment's output.
        A standard `analysis` namedtuple will contain
        ['serial', 'time', 'summoner', 'run_log', 'side_product']
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
            raise ValueError("analysis filter can't be initialized with positional arguments.")
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
    def side_product_fields(self) -> Iterable[str]:
        """The fields that will be stored as side product."""

    def __init__(
        self,
        serial: int,
        summoner: Optional[tuple] = None,
        log: Optional[dict[str, Any]] = None,
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

        duplicate_fields = set(self.AnalysisInput._fields) & set(self.AnalysisContent._fields)
        if len(duplicate_fields) > 0:
            raise QurryInvalidInherition(
                f"{self.__name__}.AnalysisInput and {self.__name__}"
                + f".AnalysisContent should not have same fields: {duplicate_fields}."
            )

    def __repr__(self) -> str:
        return (
            f"<{self.__name__}("
            + f"serial={self.header.serial}, "
            + f"{self.input.__repr__()}, "
            + f"{self.content.__repr__()}), "
            + f"unused_args_num={len(self.outfields)}>"
        )

    def _repr_pretty_(self, p, cycle):
        if cycle:
            p.text(
                f"<{self.__name__}("
                + f"serial={self.header.serial}, "
                + f"{self.input}, "
                + f"{self.content}), "
                + f"unused_args_num={len(self.outfields)}>"
            )
        else:
            with p.group(2, f"<{self.__name__}("):
                p.breakable()
                p.text(f"serial={self.header.serial},")
                p.breakable()
                p.text(f"{self.input},")
                p.breakable()
                p.text(f"{self.content}),")
                p.breakable()
                p.text(f"unused_args_num={len(self.outfields)}")
                p.breakable()
                p.text(")>")

    def __str__(self) -> str:
        return (
            f"{self.__name__} with serial={self.header.serial}, "
            + f"{self.input.__str__()}, "
            + f"{self.content.__str__()}, "
            + f"{len(self.outfields)} unused arguments"
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
                        if k != "exp_id"
                        else (
                            "This is ID is generated by Qurry "
                            + "which is different from 'job_id' for pending."
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
    def load(cls, main: dict[str, Any], side: dict[str, Any]) -> "AnalysisPrototype":
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

        content = {k: v for k, v in main.items() if k not in ("input", "header")}
        instance = cls(**main["header"], **main["input"], **content, **side)
        instance.header.log["lost_key"] = lost_key
        return instance

    @classmethod
    def read(
        cls,
        file_index: dict[str, str],
        save_location: Path,
        encoding: str = "utf-8",
    ) -> dict[str, "AnalysisPrototype"]:
        """Read the analysis from file index.

        Args:
            file_index (dict[str, str]): The file index.
            save_location (Path): The save location.
            encoding (str, optional): The encoding of the file. Defaults to "utf-8".

        Returns:
            dict[str, AnalysisPrototype]: The analysis instances in dictionary.
        """

        export_material_set = {}
        export_set = {}
        for filekey, filename in file_index.items():
            filekeydiv = filekey.split(".")
            if filekey == "reports":
                with open(save_location / filename, "r", encoding=encoding) as f:
                    export_set["reports"] = json.load(f)
                export_material_set["reports"] = export_set["reports"]["reports"]

            elif filekeydiv[0] == "reports" and filekeydiv[1] == "tales":
                with open(save_location / filename, "r", encoding=encoding) as f:
                    export_set[filekey] = json.load(f)
                if "tales_report" not in export_material_set:
                    export_material_set["tales_report"] = {}
                export_material_set["tales_report"][filekeydiv[2]] = export_set[filekey]

        del export_set
        gc.collect()

        if "reports" in export_material_set:
            mains = dict(export_material_set["reports"].items())
            sides = {k: {} for k in export_material_set["reports"]}
        else:
            mains = {}
            sides = {}
        if "tales_report" in export_material_set:
            for tk, tv in export_material_set["tales_report"].items():
                for k, v in tv.items():
                    if k not in sides:
                        sides[k] = {}
                        mains[k] = {}
                    sides[k][tk] = v
        del export_material_set
        gc.collect()

        analysis_dict: dict[str, "AnalysisPrototype"] = {}
        for k, v in mains.items():
            analysis_dict[k] = cls.load(v, sides[k])

        return analysis_dict
