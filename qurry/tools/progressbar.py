from tqdm.auto import tqdm as real_tqdm
from typing import Optional, Iterable, TypeVar, Iterable, Iterator

DEFAULT_BAR_FORMAT = {
    'simple': '| {desc} - {elapsed} < {remaining}',
    'qurry-full': '| {n_fmt}/{total_fmt} {percentage:3.0f}%|{bar}| - {desc} - {elapsed} < {remaining}',
    'qurry-barless': '| {n_fmt}/{total_fmt} - {desc} - {elapsed} < {remaining}',
}
PROGRESSBAR_ASCII = {
    '4squares': " ▖▘▝▗▚▞█",
    'standard': " ▏▎▍▌▋▊▉█",
    'decimal': " 123456789#",
    'braille': " ⠏⠛⠹⠼⠶⠧⠿",
    'boolen-eq': " =",
}

T = TypeVar('T')
_T = TypeVar("_T")


def default_setup(
    bar_format: str = 'qurry-full',
    ascii: str = '4squares',
) -> dict[str, str]:
    if bar_format in DEFAULT_BAR_FORMAT:
        actual_bar_format = DEFAULT_BAR_FORMAT[bar_format]
    else:
        actual_bar_format = bar_format

    if ascii in PROGRESSBAR_ASCII:
        actual_ascii = PROGRESSBAR_ASCII[ascii]
    else:
        actual_ascii = ascii

    return {
        'bar_format': actual_bar_format,
        'ascii': actual_ascii,
    }


class tqdm(Iterator[_T], real_tqdm):
    """A fake tqdm class for type hint.
    
    For tqdm not yet implemented their type hint by subscript like:
    >>> some_tqdm: tqdm[int] = tqdm(range(10))
    
    So, we make a fake tqdm class to make it work.
    And it should be tracked by this issue: https://github.com/tqdm/tqdm/issues/260
    To avoid the conflict, you **SHOULD NOT IMPORT** this class and keep it only working for :func:`qurryProgressBar` as type hint.

    """
    ...

    def __init__(*args, **kwargs):
        raise NotImplementedError(
            "This is not real tqdm class, but a type hint inherit from `Iterator` for function `qurryProgressBar`, you imported the wrong one.")


def qurryProgressBar(
    iterable: Optional[Iterable[T]] = None,
    *args,
    bar_format: str = 'qurry-full',
    ascii: str = '4squares',
    **kwargs,
) -> tqdm[T]:
    result_setup = default_setup(bar_format, ascii)
    actual_bar_format = result_setup['bar_format']
    actual_ascii = result_setup['ascii']

    return real_tqdm(
        iterable=iterable,
        *args,
        bar_format=actual_bar_format,
        ascii=actual_ascii,
        **kwargs
    )
