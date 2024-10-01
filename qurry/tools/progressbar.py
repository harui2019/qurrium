"""
================================================================
Progress Bar for Qurry (:mod:`qurry.tools.progressbar`)
================================================================

"""

from typing import TypeVar, Iterable, Iterator, Optional
import tqdm as real_tqdm
from tqdm.auto import tqdm as real_tqdm_instance

DEFAULT_BAR_FORMAT = {
    "simple": "| {desc} - {elapsed} < {remaining}",
    "qurry-full": "| {n_fmt}/{total_fmt} {percentage:3.0f}%|{bar}|"
    + " - {desc} - {elapsed} < {remaining}",
    "qurry-barless": "| {n_fmt}/{total_fmt} - {desc} - {elapsed} < {remaining}",
}
PROGRESSBAR_ASCII = {
    "4squares": " ▖▘▝▗▚▞█",
    "standard": " ▏▎▍▌▋▊▉█",
    "decimal": " 123456789#",
    "braille": " ⠏⠛⠹⠼⠶⠧⠿",
    "boolen-eq": " =",
}

T = TypeVar("T")
_T = TypeVar("_T")


def default_setup(
    bar_format: str = "qurry-full",
    bar_ascii: str = "4squares",
) -> dict[str, str]:
    """Get the default setup for progress bar.

    Args:
        bar_format (str, optional):
            The format of the bar. Defaults to 'qurry-full'.
        progressbar_ascii (str, optional):
            The ascii of the bar. Defaults to '4squares'.

    Returns:
        dict[str, str]: The default setup for progress bar.
    """

    return {
        "bar_format": DEFAULT_BAR_FORMAT.get(bar_format, bar_format),
        "ascii": PROGRESSBAR_ASCII.get(bar_ascii, bar_ascii),
    }


# pylint: disable=invalid-name,inconsistent-mro
class tqdm(Iterator[_T], real_tqdm_instance):
    """A fake tqdm class for type hint.

    For tqdm not yet implemented their type hint by subscript like:
    >>> some_tqdm: tqdm[int] = tqdm(range(10))

    So, we make a fake tqdm class to make it work.
    And it should be tracked by this issue: https://github.com/tqdm/tqdm/issues/260
    To avoid the conflict,
    you **SHOULD NOT IMPORT** this class and keep it only working
    for :func:`qurry_progressbar` as type hint.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        raise NotImplementedError(
            "This is not real tqdm class, "
            + "but a type hint inherit from `Iterator` "
            + "for function `qurry_progressbar`, you imported the wrong one."
        )


# pylint: enable=invalid-name,inconsistent-mro


def qurry_progressbar(
    iterable: Iterable[T],
    *args,
    bar_format: str = "qurry-full",
    bar_ascii: str = "4squares",
    **kwargs,
) -> tqdm[T]:
    """A progress bar for Qurry.

    Args:
        iterable (Optional[Iterable[T]], optional):
            The iterable object. Defaults to None.
        bar_format (str, optional):
            The format of the bar. Defaults to 'qurry-full'.
        progressbar_ascii (str, optional):
            The ascii of the bar. Defaults to '4squares'.

    Returns:
        tqdm[T]: The progress bar.
    """
    result_setup = default_setup(bar_format, bar_ascii)
    actual_bar_format = result_setup["bar_format"]
    actual_ascii = result_setup["ascii"]

    return real_tqdm_instance(  # type: ignore # for fake tqdm class
        iterable=iterable,
        *args,
        bar_format=actual_bar_format,
        ascii=actual_ascii,
        **kwargs,
    )


def set_pbar_description(pbar: Optional[real_tqdm.tqdm], description: str) -> None:
    """Set the description of the progress bar.

    Args:
        pbar (Optional[tqdm.tqdm]): The progress bar.
        description (str): The description.
    """
    if isinstance(pbar, real_tqdm.tqdm):
        pbar.set_description_str(description)
