""" "Pytest configuration file."""

import os
from pathlib import Path
from datetime import datetime
import logging
import fcntl
import pytest


class FileLockHandler(logging.FileHandler):
    """A file handler that uses file locking for thread-safe writes."""

    def emit(self, record):
        """Emit a record with file locking."""
        if self.stream is None:
            self.stream = self._open()

        try:
            fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX)
            try:
                super().emit(record)
                self.flush()
            finally:
                fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN)
        except Exception:
            self.handleError(record)


def pytest_configure(config: pytest.Config) -> None:
    """Configure logging for pytest.

    Args:
        config (pytest.Config): The pytest configuration object.
    """

    tests_folder = Path(__file__).parent
    if tests_folder.name != "tests":
        raise RuntimeError("The conftest.py file must be located in the 'tests' directory.")

    log_dir = tests_folder / "logs"
    log_dir.mkdir(exist_ok=True)

    if "PYTEST_XDIST_WORKER" not in os.environ:
        # Master process
        current_test_folder = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.environ["PYTEST_LOG_FOLDER"] = current_test_folder
    else:
        # Worker process
        current_test_folder = os.environ.get(
            "PYTEST_LOG_FOLDER", datetime.now().strftime("%Y%m%d_%H%M%S")
        )

    log_path = log_dir / current_test_folder / "pytest_combined.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format=("%(asctime)s | %(levelname)-7s | %(process)d | %(name)s | %(message)s"),
        datefmt="%H:%M:%S",
        handlers=[FileLockHandler(log_path), logging.StreamHandler()],
        force=True,
    )

    logging.getLogger("qiskit").setLevel(logging.WARNING)
