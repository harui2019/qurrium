from typing import Union, Optional, Literal
from pathlib import Path

from ...tools import qurryProgressBar
from ...capsule.mori import TagList


class QuantityContainer(dict[str, TagList[dict[str, float]]]):
    """The container of analysis for :cls:`MultiManager`.
    """

    __name__ = "QuantityContainer"

    def __init__(self):
        super().__init__()

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
        if len(self) == 0:
            print(f"| No quantity to export.")
            return quantityOutput
        
        quantityProgress = qurryProgressBar(
            self.items(),
            desc='exporting quantity',
            bar_format='qurry-barless',
        )

        for i, (k, v) in enumerate(quantityProgress):
            quantityProgress.set_description_str(f'exporting quantity: {k}')
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

            if i == len(self) - 1:
                quantityProgress.set_description_str(f'exported quantity complete')

        return quantityOutput

    def __repr__(self):
        inner_lines = '\n'.join('    %s: ...' % k for k in self.keys())
        inner_lines2 = "{\n%s\n}" % inner_lines
        return f"<{self.__name__}={inner_lines2} with {len(self)} analysis results load, a customized dictionary>"
