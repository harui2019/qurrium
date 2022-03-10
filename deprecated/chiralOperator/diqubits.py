from qiskit.tools import *
from qiskit.visualization import *
from qiskit import execute, QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit.quantum_info import Operator

# diQubits


class diQubits:
    def __init__(
        self,
        qubitsNota: str
    ) -> None:
        """Parse qubits distribution notation into diQubits notation.

        Args:
            qubitsNota (str): Qubits distribution

        Raises:
            TypeError: When qubitsNota got value which is not a string.
            ValueError: When numbers of qubits is not even number.
        """

        if type(qubitsNota) != str:
            raise TypeError(
                "Bits distribution of qubits must denote as 'str', like '000100' in 6 qubits .")

        numQubits = len(qubitsNota)
        if numQubits % 2:
            raise ValueError('Numbers of qubits is not even number.')

        self.numQubits = numQubits
        self.numPairs = int(numQubits/2)
        self.indexPairs = [self.numPairs-i-1 for i in range(self.numPairs)]
        self.listQubits = [e for e in qubitsNota]
        self.listPairs = [
            self.listQubits[2*e2]+self.listQubits[2*e2+1] for e2 in range(int(self.numPairs))]
        self.listPairsInt = [
            2*int(self.listQubits[2*e2])+int(self.listQubits[2*e2+1]) for e2 in range(int(self.numPairs))]
        self.Pairs = {
            (self.numPairs-i-1): (self.listQubits[i], self.listPairs[i]) for i in range(self.numPairs)}

    def __getattr__(self, __name: str) -> Exception:
        raise AttributeError(
            "No such attribute, print it to check attributes.")

    def __iter__(self):
        return iter(self.listPairs)

    def __repr__(self):
        return f'diQubits({self.__dict__})'

    def __len__(self):
        return self.numPairs

    def __list__(self):
        return self.listQubits

    def to_dict(self):
        return self.__dict__

    def result(self):
        return self.Pairs

## class prototype


def parse2siteSOCBase(
    qubitNota: str
) -> tuple[list, list]:
    
    if type(qubitNota) != str:
        raise TypeError(
            "Bits distribution of qubits must denote as 'str', like '000100' in 6 qubits .")
    numQubits = len(qubitNota)
    if numQubits % 2:
        raise ValueError('Numbers of qubits is not even number.')
    listQubits = [e for e in qubitNota]
    listPairs = [listQubits[2*e2]+listQubits[2*e2+1]
                 for e2 in range(int(numQubits/2))]
    return listPairs, listQubits

# probDiQubits


class probDiQubits:
    def __init__(
        self,
        resultQiskit
    ) -> None:
        
        shotsNum = resultQiskit.results[0].shots
        # 0b10 = 2, 0b01 = 1
        tmpDictDummy2 = [[v, diQubits(k)]
                         for k, v in resultQiskit.get_counts().items()]
        numPairs = tmpDictDummy2[0][1].numPairs
        positionDiqubits = {
            i: {'00': 0, '01': 0, '10': 0, '11': 0}
            for i in range(numPairs)}

        for i in range(numPairs):
            for item in tmpDictDummy2:
                positionDiqubits[numPairs-i-1][item[1].listPairs[i]] += item[0]

        self.distribute = positionDiqubits
        self.shots = shotsNum
        self.origin = resultQiskit.get_counts()
        self.numPairs = numPairs

        self.chiralOperatorSource = {
            k: (v['10'] - v['01'])/shotsNum for k, v in positionDiqubits.items()
        }

        self.__dict__ = {
            'distribute': self.distribute,
            'shots': self.shots,
            'origin': self.origin,
            'numPairs': self.numPairs,
            'chiralOperatorSource': self.chiralOperatorSource,
            # 'windingNumber': self.windingNumber,
        }

    def chiralOperator(self, indexBeginAt=0):
        kFactor = (lambda k: 0)
        if indexBeginAt == 0:
            kFactor = (lambda k: k)
        elif indexBeginAt == 1:
            kFactor = (lambda k: k+1)
        elif indexBeginAt == "bin":
            kFactor = (lambda k: 2**k)
        elif indexBeginAt == "1-bin":
            kFactor = (lambda k: 2**(k+1))
        else:
            raise KeyError("Try 0, 1, 'bin', '1-bin'")
        self.windingNumber = sum([
            kFactor(k)*v for k, v in self.chiralOperatorSource.items()
        ])
        return self.windingNumber

    def __getattr__(self, __name: str) -> Exception:
        raise AttributeError(
            "No such attribute, print it to check attributes.")

    def __repr__(self):
        return f'probDiQubits({self.__dict__})'

    def to_dict(self):
        return self.__dict__

    def __len__(self):
        return self.numPairs

##


def positionDiqubits(resultQiskit):
    tmpDictDummy1 = resultQiskit.get_counts()
    shotsNum = resultQiskit.results[0].shots
    # 0b10 = 2, 0b01 = 1
    tmpDictDummy2 = [[v, diQubits(k)] for k, v in tmpDictDummy1.items()]
    numPairs = tmpDictDummy2[0][1].numPairs
    positionDiqubits = {
        i: {'00': 0, '01': 0, '10': 0, '11': 0}
        for i in range(numPairs)}

    for i in range(numPairs):
        for item in tmpDictDummy2:
            positionDiqubits[numPairs-i-1][item[1].listPairs[i]] += item[0]
            # print(item[1].listPairs[i], item[0])
        # print(i)

    return positionDiqubits
