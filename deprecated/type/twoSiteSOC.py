from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit.quantum_info import Operator
from qiskit.circuit.gate import Gate
from math import pi
from typing import Union, Optional, List, Callable, Any, Iterable


def unitTwoSiteSOC(
    theta: float,
    runBy: str = "gate"
) -> Union[Gate, Operator]:
    """custom gate or operator of single unitTwoSiteSOC

    Args:
        Operator ([type]): [description]
        theta (float, runBy, optional): [description]. Defaults to "gate" )->Union(Gate.

    Returns:
        [type]: [description]
    """

    qcDummy = QuantumCircuit(2)
    qcDummy.cx(0, 1)  # ----------- CNOT(2x, 2x+1)
    qcDummy.rz((3/2)*pi, 0)  # ---- Z^+(2x)
    qcDummy.ry(-theta, 0)  # ------ Y^-(2x)(theta)
    qcDummy.cx(1, 0)  # ----------- CNOT(2x+1, 2x)
    qcDummy.ry(theta, 0)  # ------- Y^+(2x)(theta)
    qcDummy.cx(1, 0)  # ----------- CNOT(2x+1, 2x)
    qcDummy.rz((-3/2)*pi, 0)  # --- Z^-(2x)
    qcDummy.cx(0, 1)  # ----------- CNOT(2x, 2x+1)

    customGate = qcDummy.to_gate()
    customGate.params = [theta]
    customGate.name = f"U"

    return (customGate if runBy == "gate" else Operator(qcDummy))


def rawCircuitTwoSiteSOC(
    qPairNum: int,
    boundaryCond: str,
    hamiltonianNum: int,
    alpha: float,
    beta: float,
    runBy: str = "gate",
    initSet: str = "allSpinUp",
    hamiltonianIndex: int = 0,
    printConfig: bool = True
) -> QuantumCircuit:
    """circuit construction of the evolution of 2siteSOC

    Args:
        qPairNum (int): [description]
        boundaryCond (str): [description]
        hamiltonianNum (int): [description]
        alpha (float): [description]
        beta (float): [description]
        runBy (str, optional): [description]. Defaults to "gate".
        initSet (str, optional): [description]. Defaults to "allSpinUp".
        hamiltonianIndex (int, optional): [description]. Defaults to 0.
        printConfig (bool, optional): [description]. Defaults to True.

    Returns:
        QuantumCircuit: [description]
    """
    q = QuantumRegister(2*qPairNum)
    qc = QuantumCircuit(q)

    if printConfig:
        print(
            "-"*30+"\n" +
            f"qPairNum: {qPairNum}\n" +
            f"boundaryCond: {boundaryCond}\n" +
            f"hamiltonianNum: {hamiltonianNum}\n" +
            f"alpha: {alpha}\n" +
            f"beta: {beta}\n" +
            f"runBy: {runBy}\n" +
            f"hamiltonianIndex: {hamiltonianIndex}\n" +
            f"printConig: {printConfig}\n" +
            "-"*30+"\n" +
            "Close this message, set 'printConfig' as 'False'.\n" +
            "#"*30+"\n"
        )

    if initSet == "allSpinUp":
        [qc.x([2*i]) for i in range(qPairNum)]
    elif initSet == "alongXAxis":
        for i in range(qPairNum):
            qc.h(q[2*i])
            qc.cx(q[2*i], q[2*i+1])
            qc.x(q[2*i+1])
    elif initSet == "singleX":
        qc.x(q[0])
    else:  # initSingleX
        print(f"No initSet is chosen.")

    if hamiltonianIndex == 1:
        for i in range(hamiltonianNum):
            [qc.append(unitTwoSiteSOC(alpha/2, runBy), [q[2*j], q[2*j+1]])
             for j in range(qPairNum)]
            [qc.append(unitTwoSiteSOC(beta, runBy), [q[(2*j+1)], q[(2*j+2) % (2*qPairNum)]]) for j in range(
                qPairNum if boundaryCond == 'period' else qPairNum-1
            )]
            [qc.append(unitTwoSiteSOC(alpha/2, runBy), [q[2*j], q[2*j+1]])
             for j in range(qPairNum)]
    elif hamiltonianIndex == 2:
        for i in range(hamiltonianNum):
            [qc.append(unitTwoSiteSOC(beta, runBy), [q[(2*j+1)], q[(2*j+2) % (2*qPairNum)]]) for j in range(
                qPairNum if boundaryCond == 'period' else qPairNum-1
            )]
    else:
        print(f"No hamiltonian is chosen, current index: {hamiltonianIndex}.")

    return qc
