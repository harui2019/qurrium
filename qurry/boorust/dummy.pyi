"""Boorust - Toolkits for Dummy Case (:mod:`qurry.boorust.dummy`)"""

# pylint:disable=unused-argument
def make_two_bit_str_32(bitlen: int, num: int | None = None) -> list[str]:
    """Make a list of bit strings with length of `num`.

    Args:
        bitlen (int): bit string length.
        num (int | None): The number of bit strings.

    Returns:
        list[str]: The list of bit strings.
    """

def make_two_bit_str_unlimit(bitlen: int) -> list[str]:
    """Make a list of bit strings with length of `num`.

    Args:
        bitlen (int): bit string length.

    Returns:
        list[str]: The list of bit strings.
    """

def make_dummy_case_32(
    n_a: int, shot_per_case: int, bitstring_num: int | None = None
) -> dict[str, int]:
    """Make a dummy case for the experiment.

    Args:
        n_a (int): Number of qubits in subsystem A.
        shot_per_case (int): Number of shots per case.
        bitstring_num (int | None): Maximum number of bits.

    Returns:
        dict[str, int]: The dummy case.
    """
