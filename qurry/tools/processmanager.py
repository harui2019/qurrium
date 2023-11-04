import warnings
from tqdm.contrib.concurrent import process_map
from multiprocessing import Pool, cpu_count
from typing import Optional, Iterable, Callable, TypeVar, Any

from .progressbar import qurryProgressBar, default_setup
# Ready for issue #75 https://github.com/harui2019/qurry/issues/75

DEFAULT_POOL_SIZE = cpu_count()


def workers_distribution(
    workers_num: Optional[int] = None,
    default: int = DEFAULT_POOL_SIZE,
) -> int:
    if default < 1:
        warnings.warn(
            f"| Available worker number {cpu_count()} is equal orsmaller than 2." +
            "This computer may not be able to run this program for the program will allocate all available threads.")
        default = cpu_count()

    if workers_num is None:
        launch_worker = default
    else:
        if workers_num > cpu_count():
            warnings.warn(
                f"| Worker number {workers_num} is larger than cpu count {cpu_count()}.")
            launch_worker = default
        elif workers_num < 1:
            warnings.warn(
                f"| Worker number {workers_num} is smaller than 1. Use single worker.")
            launch_worker = 1
        else:
            launch_worker = workers_num

    return launch_worker


T_map = TypeVar('T_map')


def _caller_wrapper(func: Callable[[Any], T_map]) -> T_map:
    def _caller_inner(iterable: Iterable[Any]):
        return func(*iterable)

    return _caller_inner


class ProcessManager:

    def __init__(
        self,
        workers_num: Optional[int] = DEFAULT_POOL_SIZE,
        *args, **kwargs,
    ):
        self.workers_num = workers_distribution(workers_num)
        self.pool = Pool(
            processes=self.workers_num, *args, **kwargs)

    def starmap(
        self,
        func: Callable[[Iterable[Any]], T_map],
        args: Iterable[Iterable[Any]],
        **kwargs,
    ) -> list[T_map]:
        if self.workers_num == 1:
            return list(map(_caller_wrapper(func), args, **kwargs))
        else:
            return self.pool.starmap(func, args, **kwargs)

    def process_map(
        self,
        func: Callable[[Any], T_map],
        args: Iterable[Any],
        bar_format: str = 'qurry-full',
        ascii: str = '4squares',
        **kwargs,
    ) -> list[T_map]:
        result_setup = default_setup(bar_format, ascii)
        actual_bar_format = result_setup['bar_format']
        actual_ascii = result_setup['ascii']

        return process_map(
            func, args, **kwargs,
            ascii=actual_ascii,
            bar_format=actual_bar_format,
            max_workers=self.workers_num
        )
