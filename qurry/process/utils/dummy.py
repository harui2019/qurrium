"""Post Processing - Utils - Toolkits for Dummy Case (:mod:`qurry.process.utils.dummy`)"""

from collections.abc import Callable
import random
import numpy as np

from ..availability import availability, default_postprocessing_backend, PostProcessingBackendLabel

# pylint: disable=import-error,no-name-in-module
from ...boorust.dummy import (  # type:ignore
    make_two_bit_str_32 as make_two_bit_str_32_rust,
    make_dummy_case_32 as make_dummy_case_32_rust,
    make_two_bit_str_unlimit as make_two_bit_str_unlimit_rust,
)


BACKEND_AVAILABLE = availability("utils.dummy", [("Rust", True, None)])
DEFAULT_PROCESS_BACKEND = default_postprocessing_backend(True, False)


def filler_h_or_e(ff: str, item: str) -> str:
    """Fill the bit string with `ff` at head or end randomly.

    Args:
        ff (str): The filler, should be '0' or '1'.
        item (str): The bit string to be filled.
    Returns:
        str: The filled bit string.
    """

    return ff + item if np.random.rand() > 0.5 else item + ff


def make_two_bit_str_32_py(bitlen: int, num: int | None = None) -> list[str]:
    """Make a list of bit strings with length of `num`.

    Args:
        bitlen (int): bit string length.
        num (int | None): The number of bit strings.

    Returns:
        list[str]: The list of bit strings.
    """
    ultmax = 31
    is_less_than_16 = False
    less_slice = 0

    if num is None:
        logged_num = ultmax
        real_num = 2**ultmax
    else:
        if num < 16:
            is_less_than_16 = True
            less_slice = num
            logged_num = 4
            real_num = 16
        else:
            logged_num = np.log2(num)
            real_num = num

    if logged_num > ultmax:
        raise ValueError(f"num should be less than {2**ultmax} for safety reason.")

    def generate_bits(num: int, bits: list[str] | None = None) -> list[str]:
        if not isinstance(num, int):
            raise ValueError("num should be an integer.")
        bits = [""] if bits is None else bits
        if num == 0:
            return bits
        recursive_bits = generate_bits(num - 1, bits)

        return ["0" + item for item in recursive_bits] + ["1" + item for item in recursive_bits]

    if bitlen <= logged_num:
        result = generate_bits(bitlen)
        if is_less_than_16:
            random.shuffle(result)
            return result[:less_slice]
        return result
    less_bitlen = bitlen - int(logged_num) - 1

    raw_content = generate_bits(int(logged_num))
    len_raw_content = len(raw_content)
    assert 2 ** int(logged_num) == len_raw_content, (
        f"2**int(logged_num) == len_raw_content: {2 ** int(logged_num)} == {len_raw_content}"
    )
    assert 2 * len_raw_content >= real_num >= len_raw_content, (
        "2*len_raw_content >= real_num >= len_raw_content: "
        + f"{2 * len_raw_content} >= {real_num} >= {len_raw_content}"
    )
    first_filler = ["0", "1"] if np.random.rand() > 0.5 else ["1", "0"]

    num_fulfill_content = [filler_h_or_e(first_filler[0], item) for item in raw_content] + [
        filler_h_or_e(first_filler[1], item)
        for item in raw_content[: (real_num - len(raw_content))]
    ]
    while less_bitlen >= int(logged_num):
        num_fulfill_content = [
            filler_h_or_e(raw_content[np.random.randint(0, len_raw_content)], item)
            for item in num_fulfill_content
        ]
        less_bitlen -= int(logged_num)
    if less_bitlen == 0:
        return num_fulfill_content

    remain_fillers = generate_bits(less_bitlen)
    len_remain_fillers = len(remain_fillers)

    result = [
        filler_h_or_e(remain_fillers[np.random.randint(0, len_remain_fillers)], item)
        for item in num_fulfill_content
    ]
    if is_less_than_16:
        random.shuffle(result)
        return result[:less_slice]
    return result


def make_two_bit_str_unlimit(
    bitlen: int,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> list[str]:
    """Make a list of bit strings with length of `num`.

    Args:
        bitlen (int): bit string length.
        backend (PostProcessingBackendLabel): The backend to use.

    Returns:
        list[str]: The list of bit strings.
    """
    if bitlen > 32:
        raise ValueError("bitlen should be less than 32 for safety reason.")
    if backend == "Rust":
        return make_two_bit_str_unlimit_rust(bitlen)

    return make_two_bit_str_32_py(bitlen)


# pylint: disable=unnecessary-direct-lambda-call,invalid-name
makeTwoBitStrOneLiner: Callable[[int, list[str]], list[str]] = lambda bitlen, bits=[""]: (
    (lambda bits: [*["0" + item for item in bits], *["1" + item for item in bits]])(
        makeTwoBitStrOneLiner(bitlen - 1, bits)
    )
    if bitlen > 0
    else bits
)
"""Make a list of bit strings with length of `num`. But it's an ONE LINE code.

    Args:
        bitlen (int): bit string length.
        bits (list[str], optional): The input for recurrsion. Defaults to [''].

    Returns:
        list[str]: The list of bit strings.
"""
# pylint: enable=unnecessary-direct-lambda-call,invalid-name


def make_two_bit_str(
    bitlen: int,
    num: int | None = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> list[str]:
    """Make a list of bit strings with length of `num`.

    Args:
        bitlen (int): bit string length.
        num (int | None): The number of bit strings.
        backend (PostProcessingBackendLabel): The backend to use.

    Returns:
        list[str]: The list of bit strings.
    """
    if backend == "Rust":
        return make_two_bit_str_32_rust(bitlen, num)
    return make_two_bit_str_32_py(bitlen, num)


def make_dummy_case(
    n_a: int,
    shot_per_case: int,
    bitstring_num: int | None = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> dict[str, int]:
    """Make a dummy case for the experiment.

    Args:
        n_a (int): Number of qubits in subsystem A.
        shot_per_case (int): Number of shots per case.
        bitstring_num (int | None): Maximum number of bits.
        backend (PostProcessingBackendLabel): The backend to use.

    Returns:
        dict[str, int]: The dummy case.
    """
    if backend == "Rust":
        return make_dummy_case_32_rust(n_a, shot_per_case, bitstring_num)

    bitstring_cases = make_two_bit_str(n_a, bitstring_num, backend)
    return dict.fromkeys(bitstring_cases, shot_per_case)
