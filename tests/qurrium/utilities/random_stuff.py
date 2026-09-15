"""The random utilities for testing (:mod:`utilities.random_stuff`)."""

from typing import Literal, Any
import os
import json

SEED_FILE_LOCATION = os.path.join(os.path.dirname(__file__), "random_unitary_seeds.json")
BASIS_FILE_LOCATION = os.path.join(os.path.dirname(__file__), "random_basis.json")


def quick_json_read(file_path: str) -> Any:
    """Quickly read a JSON file and return its content.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        Any: The content of the JSON file.
    """

    with open(file_path, "r") as f:
        data = json.load(f)
    return data


def prepare_random_unitary_seeds(
    filename: str = SEED_FILE_LOCATION,
) -> dict[int, dict[int, dict[int, Literal[0, 1, 2] | int]]]:
    """Prepare random unitary seeds from a file.

    Args:
        filename (str): The filename containing the random unitary seeds.

    Returns:
        dict[str, dict[str, dict[str, int]]]: The random unitary seeds.
    """

    random_unitary_seeds_raw: dict[str, dict[str, dict[str, int]]] = quick_json_read(filename)
    return {
        int(k): {int(k2): {int(k3): v3 for k3, v3 in v2.items()} for k2, v2 in v.items()}
        for k, v in random_unitary_seeds_raw.items()
    }


def prepare_random_basis(
    filename: str = BASIS_FILE_LOCATION,
) -> dict[int, dict[int, dict[int, int]]]:
    """Prepare random basis from a file.

    Args:
        filename (str): The filename containing the random basis.

    Returns:
        dict[int, dict[int, dict[int, int]]]: The random basis.
    """

    random_basis_raw: dict[str, dict[str, dict[str, int]]] = quick_json_read(filename)
    return {
        int(k): {int(k2): {int(k3): v3 for k3, v3 in v2.items()} for k2, v2 in v.items()}
        for k, v in random_basis_raw.items()
    }
