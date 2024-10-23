"""
================================================================
OpenQASM Processor 
(:mod:`qurry.qurrium.utils.qasm`)
================================================================

"""

from typing import Literal, Optional

from qiskit import QuantumCircuit
from qiskit.qasm3 import dumps as dumps_qasm3, QASM3Error, loads as loads_qasm3
from qiskit.qasm2 import dumps as dumps_qasm2, QASM2Error, loads as loads_qasm2


def qasm_dumps(
    qc: QuantumCircuit,
    qasm_version: Literal["qasm2", "qasm3"] = "qasm2",
) -> str:
    """Draw the circuits in OpenQASM string.

    Args:
        qc (QuantumCircuit):
            The circuit wanted to be drawn.
        qasm_version (Literal["qasm2", "qasm3"], optional):
            The export version of OpenQASM. Defaults to 'qasm2'.

    Raises:
        ValueError: If the OpenQASM version is invalid.

    Returns:
        str: The drawing of circuit in OpenQASM string.
    """
    if qasm_version == "qasm2":
        try:
            txt = dumps_qasm2(qc)
        except QASM2Error as err:
            txt = f"| Skip dumps into OpenQASM2, due to QASM2Error: {err}"
            # pylint: disable=broad-except
        except Exception as err:
            # pylint: enable=broad-except
            txt = (
                "| Critical errors in qiskit.qasm2.dumps, "
                + f"due to Exception: {err}, give up to export."
            )
    elif qasm_version == "qasm3":
        try:
            txt = dumps_qasm3(qc)
        except QASM3Error as err:
            txt = f"| Skip dumps into OpenQASM3, due to QASM3Error: {err}"
            # pylint: disable=broad-except

        except Exception as err:
            # pylint: enable=broad-except
            # See: https://github.com/Qiskit/qiskit/issues/13362
            # And: https://github.com/harui2019/qurry/issues/205
            txt = (
                "| Critical errors in qiskit.qasm3.dumps, "
                + f"due to Exception: {err}, give up to export."
            )
    else:
        raise ValueError(f"Invalid qaasm version: {qasm_version}")
    assert isinstance(txt, str), "The drawing of circuit does not export."
    return txt


def qasm_version_detect(qam_str: str) -> Literal["qasm2", "qasm3"]:
    """Detect the OpenQASM version from the string.

    Args:
        qam_str (str):
            The OpenQASM string wanted to be detected.

    Returns:
        Literal["qasm2", "qasm3"]: The detected OpenQASM version.
    """
    if "OPENQASM 2.0" in qam_str:
        return "qasm2"
    if "OPENQASM 3.0" in qam_str:
        return "qasm3"
    raise ValueError("Invalid OpenQASM version.")


# See: https://github.com/harui2019/qurry/issues/205
# qasm_loads will be not used anywhere in the project.
# Until any update for the issue, this function will be kept.


def qasm_loads(
    qasm_str: str,
    qasm_version: Optional[Literal["qasm2", "qasm3"]] = None,
) -> Optional[QuantumCircuit]:
    """Load the circuits from OpenQASM string.

    Args:
        qasm_str (str):
            The OpenQASM string wanted to be loaded.
        qasm_version (Literal["qasm2", "qasm3"], optional):
            The export version of OpenQASM. Defaults to 'qasm3'.

    Raises:
        ValueError: If the OpenQASM version is invalid.

    Returns:
        QuantumCircuit: The loaded circuit.
    """
    if qasm_version is None:
        qasm_version = qasm_version_detect(qasm_str)

    if qasm_version == "qasm2":
        try:
            return loads_qasm2(qasm_str)
        except QASM2Error as err:
            print(f"| Skip loads from OpenQASM2, due to QASM2Error: {err}")
            return None
    elif qasm_version == "qasm3":
        try:
            return loads_qasm3(qasm_str)
        except QASM3Error as err:
            print(f"| Skip loads from OpenQASM3, due to QASM3Error: {err}")
            return None
    else:
        raise ValueError(f"Invalid qasm version: {qasm_version}")
