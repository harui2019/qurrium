
from qiskit.tools import *
from qiskit.visualization import *
from qiskit import execute, QuantumRegister, ClassicalRegister, QuantumCircuit

# diQubits
class diQubits:
    def __init__(self, input) -> None:
        if type(input) != str:
            raise TypeError("Bits distribution of qubits must denote as 'str', like '000100' in 6 qubits .")
        numQubits = len(input)
        if numQubits%2:
            raise ValueError('Numbers of qubits is not even number.')
        
        self.numQubits = numQubits
        self.numPairs = int(numQubits/2)
        self.indexPairs = [ self.numPairs-i-1 for i in range(self.numPairs) ]
        self.listQubits = [ e for e in input ]
        self.listPairs = [ self.listQubits[2*e2]+self.listQubits[2*e2+1] for e2 in range(int(self.numPairs)) ]
        self.listPairsInt = [ 2*int(self.listQubits[2*e2])+int(self.listQubits[2*e2+1]) for e2 in range(int(self.numPairs)) ]
        self.Pairs = { (self.numPairs-i-1): (self.listQubits[i], self.listPairs[i]) for i in range(self.numPairs) }
        
    def __getattr__(self, __name: str) -> Exception:
        raise AttributeError("No such attribute, print it to check attributes.")

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
    
## 
def parse2siteSOCBase(qubitMeasure: str):
    if type(qubitMeasure) != str:
        raise TypeError("Bits distribution of qubits must denote as 'str', like '000100' in 6 qubits .")
    numQubits = len(qubitMeasure)
    if numQubits%2:
        raise ValueError('Numbers of qubits is not even number.')
    listQubits = [ e for e in qubitMeasure ]
    listPairs = [ listQubits[2*e2]+listQubits[2*e2+1] for e2 in range(int(numQubits/2)) ]
    return listPairs, listQubits

# probDiQubits
class probDiQubits:
    def __init__(self, resultQiskit):
        shotsNum = resultQiskit.results[0].shots
        # 0b10 = 2, 0b01 = 1
        tmpDictDummy2 = [ [v, diQubits(k)] for k, v in resultQiskit.get_counts().items() ]
        numPairs = tmpDictDummy2[0][1].numPairs
        positionDiqubits = {
            i: { '00': 0, '01': 0, '10': 0, '11': 0 }
        for i in range(numPairs) }

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

    def chiralOperator(self, indexBeginAt=0):
        kFactor = (lambda k: 0)
        if indexBeginAt==0:
            kFactor = (lambda k: k)
        elif indexBeginAt==1:
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
        raise AttributeError("No such attribute, print it to check attributes.")
    
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
    tmpDictDummy2 = [ [v, diQubits(k)] for k, v in tmpDictDummy1.items() ]
    numPairs = tmpDictDummy2[0][1].numPairs
    positionDiqubits = {
        i: { '00': 0, '01': 0, '10': 0, '11': 0 }
    for i in range(numPairs) }
    
    for i in range(numPairs):
        for item in tmpDictDummy2:
            positionDiqubits[numPairs-i-1][item[1].listPairs[i]] += item[0]
            # print(item[1].listPairs[i], item[0])
        # print(i)
    
    return positionDiqubits

# hadamardTest
class hadamardTest:
    def __init__(self, waveCircuit: QuantumCircuit):
        self.waveCircuit = waveCircuit
        self.numQubits = waveCircuit.num_qubits
        self.waveCircuitGated = waveCircuit.to_gate()
        self.base = { i: dict() for i in range(self.numQubits) }
        
    def drawOfWave(self, figType='mpl', composeMethod="none"):
        qDummy = QuantumRegister(self.numQubits, 'q')
        qcDummy = QuantumCircuit(qDummy)
        
        qcDummy.append(self.waveCircuitGated, [qDummy[i] for i in range(self.numQubits)])
        fig = qcDummy.decompose().draw(figType) if composeMethod=="decompose" else qcDummy.draw(figType)
        self.figOfWave = fig
        
        return fig
    
    def waveOperator(self):
        self.waveCircuitOperator = Operator(self.waveCircuit)
        return self.waveCircuitOperator
    
    def waveGate(self):
        return self.waveCircuitGated
    
    def circuitOnly(self, a:int, runBy="gate", figType='mpl', composeMethod="none"):
        if runBy!="gate":
            self.waveOperator()
        
        if a>self.numQubits:
            raise IndexError(f"The subsystem A includes {a} qubits beyond the wave function has.")
        elif a<0:
            raise ValueError(f"The number of qubits og subsystem A has to be natural number.")
        qAnc = QuantumRegister(1, 'ancilla')
        qFunc1 = QuantumRegister(self.numQubits, 'q1')
        qFunc2 = QuantumRegister(self.numQubits, 'q2')
        cMeas = ClassicalRegister(1, 'c')
        qcHTest = QuantumCircuit(qAnc, qFunc1, qFunc2, cMeas)
        
        runByResult = self.waveCircuitGated if runBy=="gate" else self.waveCircuitOperator
        qcHTest.append(runByResult, [ qFunc1[i] for i in range(self.numQubits) ])
        qcHTest.append(runByResult, [ qFunc2[i] for i in range(self.numQubits) ])
        
        qcHTest.barrier()
        qcHTest.h(qAnc)
        if a>0:
            [ qcHTest.cswap(qAnc[0], qFunc1[i], qFunc2[i]) for i in range(a) ]
        qcHTest.h(qAnc)
        qcHTest.measure(qAnc, cMeas)
        
        fig = qcHTest.decompose().draw(figType) if composeMethod=="decompose" else qcHTest.draw(figType)
        
        self.base[a]['circuit'] = qcHTest
        self.base[a]['fig'] = fig
        self.base[a]['testResult'] = None
        self.base[a]['counts'] = None
        self.base[a]['entropy'] = None
        
        return qcHTest
        
    def runOnly(self, a:int, runBy="gate", figType='mpl', composeMethod="none", shots=1024):
        self.circuitOnly(a, runBy, figType, composeMethod)
        job = execute(self.base[a]['circuit'], backend, shots=shots)
        testResult = job.result()
        print(self.base[a]['circuit'])

        self.base[a]['testResult'] = testResult
        self.base[a]['counts'] = None
        self.base[a]['entropy'] = None
        
        return testResult
    
    def entropyOnly(self, a:int, runBy="gate", figType='mpl', composeMethod="none", shots=1024):
        self.runOnly(a, runBy, figType, composeMethod, shots)
        AncMeas = self.base[a]['testResult'].get_counts()
        indexOfCounts = list(AncMeas.keys())
        isZeroInclude = '0' in indexOfCounts
        isOneInclude = '1' in indexOfCounts
        shots = sum(AncMeas.values())
        entropy = 0 # purity
        if isZeroInclude and isOneInclude:
            entropy = (AncMeas['0'] - AncMeas['1'])/shots
        elif isZeroInclude:
            entropy = AncMeas['0']/shots
        elif isOneInclude:
            entropy = AncMeas['1']/shots
        else:
            entropy = None
            raise Warning("Expected '0' and '1', but there is no such keys")
        
        self.base[a]['counts'] = AncMeas
        self.base[a]['entropy'] = entropy
        
        return entropy
    
    def go(self, a:int, runBy="gate", figType='mpl', composeMethod="none", shots=1024):
        self.entropyOnly(a, runBy, figType, composeMethod, shots)
        return self.base[a]
            
    def __getattr__(self, __name: str) -> Exception:
        raise AttributeError("No such attribute, print it to check attributes.")
    
    def __repr__(self):
        return f'hadamardTest({self.__dict__})'
    
    def to_dict(self):
        return self.__dict__

##
def isHermitian(tgtOperator):
    try:
        return (tgtOperator.transpose().conjugate() == tgtOperator)
    except NameError:
        raise ModuleNotFoundError("You need to import 'Operator' from 'qiskit.quantum_info'.")
    except AttributeError as e:
        raise NameError(f"{str(e)} is triggered, check whether is 'Operator' defined by the import from 'qiskit.quantum_info'")
