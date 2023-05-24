from typing import Union, Optional, Literal
from pathlib import Path

from ..declare.type import Quantity
from ...mori import TagList


class QuantityContainer(dict[str, TagList[Quantity]]):
    """The container of analysis for :cls:`MultiManager`.
    """
    
    __name__ = "QuantityContainer"

    def __init__(self):
        super().__init__()

    def remove(self, name: str) -> TagList[Quantity]:
        """Removes the analysis.

        Args:
            name (str): The name of the analysis.
        """
        remain = self.pop(name)

        return remain

    def read(
        self,
        key: str,
        saveLocation: Union[str, Path],
        tagListName: str,
        name: Optional[str] = None,
    ):

        self[key] = TagList.read(
            saveLocation=saveLocation,
            tagListName=tagListName,
            name=name,
        )

    def write(
        self,
        saveLocation: Union[str, Path],
        filetype: Literal['json', 'csv'] = 'json',
        indent: int = 2,
        encoding: str = "utf-8",
    ) -> dict[str, str]:
        """Writes the analysis to files.

        Args:
            indent (int, optional): The indent of the json file. Defaults to 2.
            encoding (str, optional): The encoding of the json file. Defaults to "utf-8".

        Returns:
            dict[str, str]: The path of the files.
        """

        quantityOutput = {}
        for k, v in self.items():
            filename = v.export(
                saveLocation=saveLocation,
                tagListName='quantity',
                name=f'{k}',
                filetype=filetype,
                openArgs={
                    'mode': 'w+',
                    'encoding': encoding,
                },
                jsonDumpArgs={
                    'indent': indent,
                }
            )
            quantityOutput[k] = str(filename)

        return quantityOutput

    def __repr__(self):
        return f"<{self.__name__} with {len(self)} analysis results load, a customized dictionary>"
