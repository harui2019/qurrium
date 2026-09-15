"""Utilities for file structure handling. (:mod:`qurry.qurrium.utils.file_structure`)"""

from typing import Any


FOLDER_NAME_ARGS = "args"
"""Folder name for arguments and common parameters export."""
FOLDER_NAME_BEFOREWARDS = "advent"
"""Folder name for beforewards export."""
FOLDER_NAME_AFTERWARDS = "legacy"
"""Folder name for afterwards export."""
FOLDER_NAME_SIDE_PRODUCTS = "tales"
"""Folder name for side products export."""
FOLDER_NAME_ANALYSES = "myths"
"""Folder name for analyses export."""


REQUIRED_KEYS = {
    "folder",
    "qurryinfo",
    FOLDER_NAME_ARGS,
    FOLDER_NAME_BEFOREWARDS,
    FOLDER_NAME_AFTERWARDS,
    FOLDER_NAME_SIDE_PRODUCTS,
    FOLDER_NAME_ANALYSES,
}
"""The required keys for the exported experiment file."""


def is_old_v7_file_structure(file_index: dict[str, Any]) -> bool:
    """Check if the file structure is v7.

    Args:
        file_index (dict[str, Any]): The file index.

    Returns:
        bool: True if the file structure is v7, False otherwise.
    """
    return FOLDER_NAME_SIDE_PRODUCTS not in file_index and FOLDER_NAME_ANALYSES not in file_index


def is_old_v7_multimanager_file_structure(
    file_index: dict[str, Any],
) -> bool:
    """Check if the MultiManager file structure is v7.

    Args:
        file_index (dict[str, Any]): The file index.

    Returns:
        bool: True if the MultiManager file structure is v7, False otherwise.
    """
    return FOLDER_NAME_SIDE_PRODUCTS not in file_index and FOLDER_NAME_ANALYSES not in file_index
