"""The Parallel Tools and Chunk Distribution (:mod:`qurry.tools.parallelmanager`)

This module provides the ParallelManager class for multiprocessing
and functions for chunk size calculation and distribution.
"""

from typing import TypeVar, Any, Literal
from collections.abc import Iterable, Callable
import warnings
from multiprocessing import cpu_count, get_context

from .exceptions import WrongWorkerNumReplaced, ParallelManagerRuntimeError


CPU_COUNT_UNSAFE = cpu_count()
"""The number of CPUs available for multiprocessing.
But this number may be None in some cases.
"""

CPU_COUNT = CPU_COUNT_UNSAFE if CPU_COUNT_UNSAFE else 1
"""The number of CPUs available for multiprocessing.
This number is guaranteed to be at least 1.
"""

DEFAULT_POOL_SIZE = CPU_COUNT
"""The default number of workers for multiprocessing.
This number is guaranteed to be at least 1.
"""

DEFAULT_START_METHOD = "spawn"
"""The default start method for multiprocessing. """


def workers_distribution(workers_num: int | None = None, default: int = DEFAULT_POOL_SIZE) -> int:
    """Distribute the workers number.

    Args:
        workers_num (int | None, optional): Desired workers number. Defaults to None.
        default (int, optional): Default workers number. Defaults to DEFAULT_POOL_SIZE.

    Returns:
        int: Workers number.
    """

    if default < 1:
        warnings.warn(
            f"| Available worker number {CPU_COUNT} is equal or smaller than 1."
            + "This computer may not be able to run this program for "
            + "the program will allocate all available threads.",
            category=WrongWorkerNumReplaced,
        )
        default = DEFAULT_POOL_SIZE if DEFAULT_POOL_SIZE > 0 else 1

    if workers_num is None:
        return default

    if workers_num > CPU_COUNT:
        warnings.warn(
            f"| Worker number {workers_num} is larger than cpu count {CPU_COUNT}.",
            category=WrongWorkerNumReplaced,
        )
        return default

    if workers_num < 1:
        warnings.warn(
            f"| Worker number {workers_num} is smaller than 1. Use single worker.",
            category=WrongWorkerNumReplaced,
        )
        return 1

    return workers_num


def make_multiprocess_pool(
    workers_num: int | None = DEFAULT_POOL_SIZE,
    start_method: Literal["spawn", "fork", "forkserver"] = DEFAULT_START_METHOD,
    initializer: Callable[..., object] | None = None,
    initargs: Iterable[Any] = (),
    maxtasksperchild: int | None = None,
):
    """Create a multiprocessing Pool.

    Args:
        workers_num (int | None, optional):
            Desired workers number. Defaults to DEFAULT_POOL_SIZE.
        start_method (Literal["spawn", "fork", "forkserver"], optional):
            Start method for multiprocessing. Defaults to DEFAULT_START_METHOD.
        initializer (Callable[..., object] | None, optional):
            Initializer for the Pool. Defaults to None.
        initargs (Iterable[Any], optional):
            Arguments for the initializer. Defaults to ().
        maxtasksperchild (int | None, optional):
            The maximum number of tasks per child process. Defaults to None.

    Returns:
        The created Pool with the given parameters by specified start method.
    """

    return get_context(start_method).Pool(
        processes=workers_distribution(workers_num),
        initializer=initializer,
        initargs=initargs,
        maxtasksperchild=maxtasksperchild,
    )


Tmap = TypeVar("Tmap")
Ttgt = TypeVar("Ttgt")


class ParallelManager:
    """A wrapper class for multiprocessing Pool."""

    def __init__(
        self,
        workers_num: int | None = DEFAULT_POOL_SIZE,
        start_method: Literal["spawn", "fork", "forkserver"] = DEFAULT_START_METHOD,
        initializer: Callable[..., object] | None = None,
        initargs: Iterable[Any] = (),
        maxtasksperchild: int | None = None,
    ):
        """Initialize the ParallelManager.

        Args:
            workers_num (int | None, optional):
                Desired workers number. Defaults to DEFAULT_POOL_SIZE.
                If workers_num is 1, then disable multiprocessing.
                If None, use DEFAULT_POOL_SIZE.

            start_method (Literal["spawn", "fork", "forkserver"], optional):
                Start method for multiprocessing. Defaults to DEFAULT_START_METHOD.
            initializer (Callable[..., object] | None, optional):
                Initializer for the Pool. Defaults to None.
            initargs (Iterable[Any], optional):
                Arguments for the initializer. Defaults to ().
            maxtasksperchild (int | None, optional):
                The maximum number of tasks per child process. Defaults to None.
        """

        self.workers_num = workers_distribution(workers_num)
        self.start_method: Literal["spawn", "fork", "forkserver"] = start_method
        self.pool_kwargs = {
            "initializer": initializer,
            "initargs": initargs,
            "maxtasksperchild": maxtasksperchild,
        }

    def starmap(self, func: Callable[..., Tmap], args_list: Iterable) -> list[Tmap]:
        """This function is a wrapper for starmap from multiprocessing.

        Args:
            func (Callable[[Iterable[T_tgt]], T_map]): Function to be mapped.
            args_list (Iterable[Iterable[T_tgt]]): Arguments to be mapped.

        Returns:
            list[T_map]: Results.
        """

        if self.workers_num == 1:
            return list(map(func, *zip(*args_list)))

        try:
            pool = make_multiprocess_pool(
                workers_num=self.workers_num,
                start_method=self.start_method,
                initializer=self.pool_kwargs["initializer"],
                initargs=self.pool_kwargs["initargs"],
                maxtasksperchild=self.pool_kwargs["maxtasksperchild"],
            )
            with pool as p:
                return p.starmap(func, args_list)
        except RuntimeError as e:
            raise ParallelManagerRuntimeError(
                "Failed to use multiprocessing with the given start method. "
                f"Please check the start method: {self.start_method}. "
                "And refer to the above error message for more details."
            ) from e

    def map(self, func: Callable[[Ttgt], Tmap], arg_list: Iterable[Ttgt]) -> list[Tmap]:
        """This function is a wrapper for map from multiprocessing.

        Args:
            func (Callable[[Iterable[T_tgt]], T_map]): Function to be mapped.
            arg_list (Iterable[T_tgt]): Arguments to be mapped.

        Returns:
            list[T_map]: Results.
        """

        if self.workers_num == 1:
            return list(map(func, arg_list))

        try:
            pool = make_multiprocess_pool(
                workers_num=self.workers_num,
                start_method=self.start_method,
                initializer=self.pool_kwargs["initializer"],
                initargs=self.pool_kwargs["initargs"],
                maxtasksperchild=self.pool_kwargs["maxtasksperchild"],
            )
            with pool as p:
                return p.map(func, arg_list)
        except RuntimeError as e:
            raise ParallelManagerRuntimeError(
                "Failed to use multiprocessing with the given start method. "
                f"Please check the start method: {self.start_method}. "
                "And refer to the above error message for more details."
            ) from e


def very_easy_chunk_size(
    tasks_num: int,
    num_process: int = DEFAULT_POOL_SIZE,
    max_chunk_size: int = CPU_COUNT * 4,
) -> int:
    """Calculate the chunk size for multiprocess.

    Args:
        tasks_num (int): The number of tasks.
        num_process (int, optional):
            The number of processes. Defaults to DEFAULT_POOL_SIZE.
        max_chunk_size (int, optional):
            The maximum chunk size. Defaults to CPU_COUNT * 4.

    Returns:
        int: The chunk size.
    """
    if max_chunk_size < 1:
        raise ValueError("max_chunk_size must be greater than 0")
    if max_chunk_size == 1:
        return 1

    chunks_num = tasks_num // num_process + 1
    while chunks_num > max_chunk_size:
        num_process *= 2
        chunks_num = tasks_num // num_process + 1
    return chunks_num


def very_easy_chunk_distribution(
    respect_memory_array: list[tuple[str, int]],
    num_process: int = DEFAULT_POOL_SIZE,
    max_chunk_size: int = CPU_COUNT * 4,
) -> tuple[int, list[tuple[str, int]], list[list[str]]]:
    """Distribute the chunk for multiprocess.
    The chunk distribution is based on the number of CPU cores.

    Args:
        respect_memory_array (list[tuple[str, int]]):
            The array of respect memory.
            Each element is a tuple of (id, memory).
            The id is the ID of the experiment, and the memory is the memory usage.
            The array is sorted by the memory usage.
        num_process (int, optional):
            The number of processes. Defaults to DEFAULT_POOL_SIZE.
        max_chunk_size (int, optional):
            The maximum chunk size. Defaults to CPU_COUNT * 4.

    Returns:
        tuple[int, list[tuple[str, int]], list[list[str]]]:
            The chunk distribution is a list of tuples of (id, memory).
    """
    if max_chunk_size < 1:
        raise ValueError("max_chunk_size must be greater than 0")

    chunks_num = len(respect_memory_array) // num_process + 1
    while chunks_num > max_chunk_size:
        num_process *= 2
        chunks_num = len(respect_memory_array) // num_process + 1
    chunks_sorted_list = []
    distributions = [[] for _ in range(num_process)]

    for i in range(num_process):
        for j in range(chunks_num):
            # Distribute the chunks in a round-robin fashion
            idx = j * num_process + i if j % 2 == 0 else (j + 1) * num_process - i - 1
            if idx < len(respect_memory_array):
                chunks_sorted_list.append(respect_memory_array[idx])
                distributions[i].append(idx)

    return chunks_num, chunks_sorted_list, distributions
