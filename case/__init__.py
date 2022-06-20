
_isQurecipe = False
try:
    from .qurecipe import *
    _isQurecipe = True
except ImportError as e:
    _isQurecipe = False
    from .paramagnet import *

    case_set: dict[Case] = {
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
        return case_set[name]
    
def isQurecipe(): return _isQurecipe