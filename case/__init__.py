from .paramagnet import *

caseSet = {
    "trivialParamagnet": trivialParamagnet,
    "cat": cat,
    "topParamagnet": topParamagnet,
}


def get_case(
    name: str,
) -> QuantumCircuit:
    """_summary_

    Args:
        name (str): _description_

    Returns:
        QuantumCircuit: _description_
    """
    return caseSet[name]