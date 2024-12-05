"""
================================================================
Basic Webhook
================================================================

# TODO: 
"""

from typing import NamedTuple, Union, TypedDict
from pathlib import Path
import pickle
import requests


class BasicHookArguments(NamedTuple):
    """BasicHookArguments is the arguments for BasicHook."""

    url: str
    save_location: Union[Path, str]


class BasicHookArgumentsRaw(TypedDict):
    """BasicHookContent is the content for BasicHook."""

    url: str
    save_location: Union[Path, str]


class BasicHook:
    """BasicHook is the basic webhook for CapSule.

    Args:
        url (str):
            The url of webhook.
        save_location (Union[Path, str]):
            The location of saved BasicHook.

    """

    def __init__(self, url: str, save_location: Union[Path, str]):
        self.config = BasicHookArguments(
            url=url,
            save_location=save_location,
        )

    def save(self, save_location: Union[Path, str]) -> None:
        """Save the BasicHook.

        Args:
            save_location (Union[Path, str]):
                The location of saved BasicHook.

        Raises:
            ValueError: If `save_location is None`.
            FileNotFoundError: If `save_location` does not exist.

        """

        if save_location is None:
            save_location = self.config.save_location
        if save_location is None:
            raise ValueError("save_location cannot be None")

        if isinstance(save_location, str):
            save_location = Path(save_location)
        if not save_location.exists():
            raise FileNotFoundError(f"{save_location} does not exist")

        export = self.config._asdict()
        if isinstance(export["save_location"], Path):
            export["save_location"] = str(export["save_location"])

        with open(save_location, "wb") as f:
            pickle.dump(export, f)

    def post(
        self,
        content: dict[str, str],
        header: dict[str, str],
        hide_print: bool = False,
        timeout: int = 10,
        **kwargs,
    ) -> requests.Response:
        """Post the content to webhook.

        Args:
            content (dict[str, str]):
                The content of webhook.
            header (dict[str, str]):
                The header of webhook.
            hide_print (bool, optional):
                Hide the print of result. Defaults to False.
            timeout (int, optional):
                The timeout of post. Defaults to 10.
            **kwargs:
                The kwargs of `requests.post`.

        Returns:
            requests.Response: The result of post.
        """

        result = requests.post(
            self.config.url,
            json=content,
            headers=header,
            timeout=timeout,
            **kwargs,
        )
        if 200 <= result.status_code < 300:
            if not hide_print:
                print(f"Webhook sent {result.status_code}")
        else:
            print(f"Not sent with {result.status_code}, response:\n{result.json()}")

        return result

    @classmethod
    def read(
        cls,
        save_location: Union[Path, str],
    ):
        """Read the saved BasicHook.

        Args:
            save_location (Union[Path, str]):
                The location of saved BasicHook.

        Raises:
            ValueError: If `save_location is None`.
            FileNotFoundError: If `save_location` does not exist.

        Returns:
            BasicHook: The saved BasicHook.
        """

        if save_location is None:
            raise ValueError("save_location cannot be None")
        if isinstance(save_location, str):
            save_location = Path(save_location)

        if not save_location.exists():
            raise FileNotFoundError(f"{save_location} does not exist")

        with open(save_location, "rb") as f:
            export: BasicHookArgumentsRaw = pickle.load(f)

        export["save_location"] = Path(save_location)

        return cls(
            url=export["url"],
            save_location=export["save_location"],
        )
