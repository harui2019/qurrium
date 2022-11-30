
isQurecipe = False
try:
    isQurecipe = True
    from ..qurecipe import *
except ImportError as e:
    isQurecipe = False
    from .paramagnet import *

    CASE_SET: dict[Case] = {
        "trivialParamagnet": trivialParamagnet,
        "cat": cat,
        "topParamagnet": topParamagnet,
    } 
    
    def get_case(
        name: str,
    ) -> Case:
        """_summary_

        Args:
            name (str): _description_

        Returns:
            QuantumCircuit: _description_
        """
        return CASE_SET[name]