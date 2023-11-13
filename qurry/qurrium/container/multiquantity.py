"""
================================================================
The container for quantities of analysis for :cls:`MultiManager`.
(:mod:`qurry.qurrium.container.multiquantity`)
================================================================
"""
from typing import Union, Optional, Literal
from pathlib import Path

from ...tools import qurry_progress_bar
from ...capsule.mori import TagList


class QuantityContainer(dict[str, TagList[dict[str, float]]]):
    """The container for quantities of analysis for :cls:`MultiManager`."""

    __name__ = "QuantityContainer"

    def remove(self, name: str) -> TagList[dict[str, float]]:
        """Removes the analysis.

        Args:
            name (str): The name of the analysis.
        """
        remain = self.pop(name)

        return remain

    def read(
        self,
        key: str,
        save_location: Union[str, Path],
        taglist_name: str,
        name: Optional[str] = None,
    ):
        """Reads the analysis.

        Args:
            key (str): The key of the analysis.
            save_location (Union[str, Path]): The save location of the analysis.
            taglist_name (str): The name of the taglist.
            name (Optional[str], optional): The name of the analysis. Defaults to None.
        """
        self[key] = TagList.read(
            saveLocation=save_location,
            tagListName=taglist_name,
            name=name,
        )

    def write(
        self,
        save_location: Union[str, Path],
        filetype: Literal["json", "csv"] = "json",
        indent: int = 2,
        encoding: str = "utf-8",
    ) -> dict[str, str]:
        """Writes the analysis to files.

        Args:
            save_location (Union[str, Path]): The save location of the analysis.
            filetype (Literal[&#39;json&#39;, &#39;csv&#39;], optional):
                The filetype of the analysis. Defaults to "json".
            indent (int, optional): The indent of the json file. Defaults to 2.
            encoding (str, optional): The encoding of the json file. Defaults to "utf-8".

        Returns:
            dict[str, str]: The path of the files.
        """

        quantity_output = {}
        if len(self) == 0:
            print("| No quantity to export.")
            return quantity_output

        quantity_progress = qurry_progress_bar(
            self.items(),
            desc="exporting quantity",
            bar_format="qurry-barless",
        )

        for i, (k, v) in enumerate(quantity_progress):
            quantity_progress.set_description_str(f"exporting quantity: {k}")
            filename = v.export(
                saveLocation=save_location,
                tagListName="quantity",
                name=f"{k}",
                filetype=filetype,
                openArgs={
                    "mode": "w+",
                    "encoding": encoding,
                },
                jsonDumpArgs={
                    "indent": indent,
                },
            )
            quantity_output[k] = str(filename)

            if i == len(self) - 1:
                quantity_progress.set_description_str("exported quantity complete")

        return quantity_output

    def __repr__(self):
        inner_lines = "\n".join([f"    {k}: ..." for k in self.keys()])
        inner_lines2 = "{\n%s\n}" % inner_lines
        return (
            f"<{self.__name__}={inner_lines2} with {len(self)} "
            + "analysis results load, a customized dictionary>"
        )
