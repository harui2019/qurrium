'''Progress Bar for Qurrium (:mod:`qurry.tools.progressbar`)

For the followings GitHub issues on https://tqdm.github.io/

-   https://github.com/tqdm/tqdm/issues/260
    We do some improvement in our package.
    We make a fake tqdm class :class:`tqdm` for type hint.

-   https://github.com/tqdm/tqdm/issues/705
    The intersphinx usage in docstring like:

    .. code-block:: python

        """Dummy docstring.

        Hey, it's a :class:`~tqdm.tqdm`
        """

    It's not available, so we replace them by:

    .. code-block:: python

        """Dummy docstring.

        Hey, it's a `tqdm.tqdm <https://tqdm.github.io/>`
        """

    by the external link to the `tqdm <https://tqdm.github.io/>`_ documentation,
    which follows `Links to External Web Pages
    <https://sublime-and-sphinx-guide.readthedocs.io/\
        en/latest/references.html#links-to-external-web-pages>`_

'''

from typing import TypeVar
from collections.abc import Iterable, Iterator
import tqdm as real_tqdm
from tqdm.auto import tqdm as real_tqdm_instance

DEFAULT_BAR_FORMAT = {
    "simple": "| {desc} - {elapsed} < {remaining}",
    "qurry-full": "| {n_fmt}/{total_fmt} {percentage:3.0f}%|{bar}|"
    + " - {desc} - {elapsed} < {remaining}",
    "qurry-barless": "| {n_fmt}/{total_fmt} - {desc} - {elapsed} < {remaining}",
}
"""Default bar format for progress bar.

- "simple":
    A simple format with description, elapsed time, and remaining time.

    .. code-block:: python

        "| {desc} - {elapsed} < {remaining}"

- "qurry-full":
    A full format with count, percentage, bar, description, elapsed time, and remaining time.

    .. code-block:: python

        "| {n_fmt}/{total_fmt} {percentage:3.0f}%|{bar}| - {desc} - {elapsed} < {remaining}"

- "qurry-barless":
    A format without the bar, showing count, description, elapsed time, and remaining time.

    .. code-block:: python

        "| {n_fmt}/{total_fmt} - {desc} - {elapsed} < {remaining}"
"""
PROGRESSBAR_ASCII = {
    "4squares": " ▖▘▝▗▚▞█",
    "standard": " ▏▎▍▌▋▊▉█",
    "decimal": " 123456789#",
    "braille": " ⠏⠛⠹⠼⠶⠧⠿",
    "boolen-eq": " =",
}
"""Default ASCII characters for progress bar.

- "4squares":
    A 4-squares ASCII style.
- "standard":
    A standard ASCII style with 8 segments.
- "decimal":
    A decimal ASCII style with numbers 1-9 and a hash.
- "braille":
    A braille ASCII style with 7 segments.
- "boolen-eq":
    A boolean equal sign ASCII style with just an equal sign.

.. code-block:: python

    {
        "4squares": " ▖▘▝▗▚▞█",
        "standard": " ▏▎▍▌▋▊▉█",
        "decimal": " 123456789#",
        "braille": " ⠏⠛⠹⠼⠶⠧⠿",
        "boolen-eq": " =",
    }    
"""

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


# pylint: disable=invalid-name,inconsistent-mro,abstract-method
class tqdm(Iterator[_T], real_tqdm_instance):
    """A fake tqdm class for type hint.

    For tqdm not yet implemented their type hint by subscript like:

    .. code-block:: python

        some_tqdm: tqdm[int] = tqdm(range(10))

    So, we make a fake tqdm class to make it work.

    And it should be tracked by this issue:
    https://github.com/tqdm/tqdm/issues/260 to avoid the conflict.

    You **SHOULD NOT IMPORT** this class and keep it only working
    for :func:`qurry_progressbar` as type hint.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        raise NotImplementedError(
            "This is not real tqdm class, "
            "but a type hint inherit from 'Iterator' "
            "for function 'qurry_progressbar', you imported the wrong one."
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
        iterable (Iterable[T]): The iterable object.
        bar_format (str, optional): The format of the bar. Defaults to 'qurry-full'.
        bar_ascii (str, optional): The ascii of the bar. Defaults to '4squares'.

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


def set_pbar_description(pbar: real_tqdm.tqdm | None, description: str) -> None:
    """Set the description of the progress bar.

    Args:
        pbar (tqdm.tqdm | None): The progress bar.
        description (str): The description.
    """
    if isinstance(pbar, real_tqdm.tqdm):
        pbar.set_description_str(description)
