"""
================================================================
ProcessManager (:mod:`qurry.tools.processmanager`)
================================================================

"""

import warnings
from typing import Optional, Iterable, Callable, TypeVar, Any
from multiprocessing import Pool, cpu_count
from tqdm.contrib.concurrent import process_map

from .progressbar import default_setup
from ..exceptions import QurryWarning

# Ready for issue #75 https://github.com/harui2019/qurry/issues/75

DEFAULT_POOL_SIZE = cpu_count()


def workers_distribution(
    workers_num: Optional[int] = None,
    default: int = DEFAULT_POOL_SIZE,
) -> int:
    """Distribute the workers number.

    Args:
        workers_num (Optional[int], optional): Desired workers number. Defaults to None.
        default (int, optional): Default workers number. Defaults to DEFAULT_POOL_SIZE.

    Returns:
        int: Workers number.
    """

    if default < 1:
        warnings.warn(
            f"| Available worker number {cpu_count()} is equal orsmaller than 2."
            + "This computer may not be able to run this program for "
            + "the program will allocate all available threads.",
            category=QurryWarning,
        )
        default = cpu_count()

    if workers_num is None:
        launch_worker = default
    else:
        if workers_num > cpu_count():
            warnings.warn(
                f"| Worker number {workers_num} is larger than cpu count {cpu_count()}.",
                category=QurryWarning,
            )
            launch_worker = default
        elif workers_num < 1:
            warnings.warn(
                f"| Worker number {workers_num} is smaller than 1. Use single worker.",
                category=QurryWarning,
            )
            launch_worker = 1
        else:
            launch_worker = workers_num

    return launch_worker


# pylint: disable=invalid-name
T_map = TypeVar("T_map")
T_tgt = TypeVar("T_tgt")
# pylint: enable=invalid-name


class ParallelManager:
    """Process manager for multiprocessing."""

    def __init__(
        self,
        workers_num: Optional[int] = DEFAULT_POOL_SIZE,
        **pool_kwargs,
    ):
        """Initialize the process manager.

        Args:
            workers_num (Optional[int], optional):
                Desired workers number. Defaults to DEFAULT_POOL_SIZE.
            **pool_kwargs: Other arguments for Pool.
        """

        if "processes" in pool_kwargs:
            warnings.warn(
                "| `processes` is given in `pool_kwargs`."
                + "It will be overwritten by `workers_num`."
            )
            pool_kwargs.pop("processes")

        self.pool_kwargs = pool_kwargs
        self.workers_num = workers_distribution(workers_num)

    def starmap(
        self,
        func: Callable[..., T_map],
        args_list: Iterable,
    ) -> list[T_map]:
        """Multiprocessing starmap.

        Args:
            func (Callable[[Iterable[T_tgt]], T_map]): Function to be mapped.
            args_list (Iterable[Iterable[T_tgt]]): Arguments to be mapped.

        Returns:
            list[T_map]: Results.
        """

        if self.workers_num == 1:
            return list(map(func, *zip(*args_list)))

        with Pool(processes=self.workers_num, **self.pool_kwargs) as pool:
            return pool.starmap(func, args_list)

    def map(
        self,
        func: Callable[[T_tgt], T_map],
        arg_list: Iterable[T_tgt],
    ) -> list[T_map]:
        """Multiprocessing starmap.

        Args:
            func (Callable[[Iterable[T_tgt]], T_map]): Function to be mapped.
            arg_list (Iterable[Iterable[T_tgt]]): Arguments to be mapped.

        Returns:
            list[T_map]: Results.
        """

        if self.workers_num == 1:
            return list(map(func, arg_list))

        with Pool(processes=self.workers_num, **self.pool_kwargs) as pool:
            return pool.map(func, arg_list)

    def process_map(
        self,
        func: Callable[..., T_map],
        args_list: Iterable[Iterable[Any]],
        bar_format: str = "qurry-full",
        bar_ascii: str = "4squares",
        **kwargs,
    ) -> list[T_map]:
        """Multiprocessing process_map.

        Args:
            func (Callable[[Any], T_map]): Function to be mapped.
            args (Iterable[Any]): Arguments to be mapped.
            bar_format (str, optional): Progress bar format. Defaults to "qurry-full".
            bar_ascii (str, optional): Progress bar ascii. Defaults to "4squares".
            **kwargs: Other arguments.

        Returns:
            list[T_map]: Results.
        """

        result_setup = default_setup(bar_format, bar_ascii)
        actual_bar_format = result_setup["bar_format"]
        actual_ascii = result_setup["ascii"]

        return process_map(
            func,
            *zip(*args_list),
            **kwargs,
            ascii=actual_ascii,
            bar_format=actual_bar_format,
            max_workers=self.workers_num,
        )
