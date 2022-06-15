#!/usr/bin/env python
# coding: utf-8
import os.path
import sys
import warnings
import json
import argparse, time
import numpy as np
import matplotlib.pyplot as plt
import qiskit
from qiskit import *
from qiskit import IBMQ, QuantumCircuit, execute,  Aer
from qiskit.result import marginal_counts
from qiskit.providers.ibmq.job import job_monitor
from qiskit.tools.visualization import plot_histogram
from math import pi
from qiskit.circuit import Parameter
import qiskit.quantum_info as qi
from qiskit import transpile
from qiskit.providers.ibmq.managed import IBMQJobManager
# Use Aer's statevector simulator
from qiskit import Aer
font = {'family': 'sans',
        'color': 'black',
        'weight': 'normal',
        'size': 18,
        }
params = {'legend.fontsize': 16,
          'legend.handlelength': 1,
          'xtick.labelsize': 'large',
          'font.size': 18,}
plt.rcParams.update(params)


machine_name='ibmq_guadalupe'
IBMQ.load_account()
provider=IBMQ.get_provider(hub='ibm-q-hub-ntu', group='ntu-internal', project='default')
backend_sim = Aer.get_backend('qasm_simulator')
vectorsim=BasicAer.get_backend('statevector_simulator')
device=provider.get_backend(machine_name)
dt = Parameter('dt')
num_qubits = 5
J=1
Jp=2



def ZZbase(J=1):
    ZZ_qr = QuantumRegister(2)
    ZZ_qc = QuantumCircuit(ZZ_qr, name='ZZ')

    ZZ_qc.cnot(0,1)
    ZZ_qc.rz( 2*J*dt, 1)
    ZZ_qc.cnot(0,1)
    ZZ = ZZ_qc.to_instruction()
    return ZZ


def YYbase(ZZ):
    YY_qr = QuantumRegister(2)
    YY_qc = QuantumCircuit(YY_qr, name='YY')
    YY_qc.s(YY_qr)
    YY_qc.h(YY_qr)
    YY_qc.append(ZZ, [0,1])
    YY_qc.h(YY_qr)
    YY_qc.sdg(YY_qr)
    YY = YY_qc.to_instruction()
    return YY


def XXbase(ZZ):
    XX_qr = QuantumRegister(2)
    XX_qc = QuantumCircuit(XX_qr, name='XX')
    XX_qc.h(XX_qr)
    XX_qc.append(ZZ, [0,1])
    XX_qc.h(XX_qr)
    XX = XX_qc.to_instruction()
    return XX




def createeven(J=1, tfactor=1):
    ZZ=ZZbase(J=J*tfactor)

    XX = XXbase(ZZ)
    YY=YYbase(ZZ)
    even_qr = QuantumRegister(num_qubits)
    even_qc = QuantumCircuit(even_qr, name='even')
    for i in range(0,num_qubits-1,2):
        even_qc.append(YY,[i,i+1])
        even_qc.append(XX,[i,i+1])
    even_gate = even_qc.to_instruction()
    return even_gate


def createodd(Jp=1):
    ZZo=ZZbase(J=Jp)
    XXo = XXbase(ZZo)
    YYo=YYbase(ZZo)
    odd_qr = QuantumRegister(num_qubits)
    odd_qc = QuantumCircuit(odd_qr, name='odd')
    for i in range(1,num_qubits-1,2):
        odd_qc.append(YYo,[i,i+1])
        odd_qc.append(XXo,[i,i+1])
    odd_gate = odd_qc.to_instruction()
    return odd_gate

def onetrotstep(J,Jp):
    tfactor=1
    if args.order==2: tfactor=1/2
    even_gate=createeven(J=J, tfactor=tfactor)
    odd_gate=createodd(Jp=Jp)

    Trot_tb_qr = QuantumRegister(num_qubits)
    Trot_tb_qc = QuantumCircuit(Trot_tb_qr, name='Trot')

    Trot_tb_qc.append(even_gate,[i for i in range(num_qubits)])
    Trot_tb_qc.append(odd_gate,[i for i in range(num_qubits)])
    if args.order==2:
        Trot_tb_qc.append(even_gate,[i for i in range(num_qubits)])
    #Trot_tb_qc.draw()
    Trot_tb_gate = Trot_tb_qc.to_instruction()
    return Trot_tb_gate

def create_circls(exls=[0],Jp=1,delta_t=0.1,time_steps=np.arange(1,40,1)):
    circuits=[]
    Trot_tb_gate=onetrotstep(J=1,Jp=Jp)
    for n_steps in time_steps:
        qr = QuantumRegister(num_qubits)
        cr = ClassicalRegister(num_qubits)
        qc = QuantumCircuit(qr,cr)
        qc.x(exls)
        for _ in range(n_steps):
            qc.append(Trot_tb_gate, [i for i in range(num_qubits)])
        qc.measure(qr,cr)
        qc = qc.bind_parameters({dt: delta_t})
        circuits.append(qc)
    return circuits

def getprob(num_qubits,counts,shots=1024):
    tmp=np.zeros([num_qubits,])
    for i, item in enumerate(counts.items()):
        ts=0
        for si,s in enumerate(item[0]):
            ts+=int(s)
        if ts==0: continue
        for si,s in enumerate(item[0]):
            tmp[si]+=abs(int(s))*item[1]/shots/ts
    return tmp
def probden(exls=[0],subdate='06092022'):
    # Run the quantum circuit on a statevector simulator backend
    subd='./data/simulator/'+subdate+'/'
    if not os.path.isdir(subd):os.mkdir(subd)
    delta_t=0.1
    time_steps=np.arange(1,T+1,1)
    circuits=create_circls(exls,args.Jp,delta_t, time_steps)
    probability_density=[]
    allcounts={}
    for i,circ in enumerate(circuits):
        transpiled_circ=transpile(circ, backend_sim, optimization_level=3)
        job_sim = backend_sim.run(transpiled_circ)
        # Grab the results from the job.
        result_sim = job_sim.result()
        counts = result_sim.get_counts()
        allcounts[i]=counts
        tmp=getprob(num_qubits, counts)
        probability_density.append(tmp)
    with open(subd+'/N_{}_ex_{}_Jp_{:.1f}.json'.format(num_qubits,exls,args.Jp),'w') as f:
        json.dump(allcounts, f, ensure_ascii=True, indent=2)
        #f.write(',\n')
    probability_density=np.flip(np.array(probability_density),axis=1)
    fig=plt.figure(figsize=(4,5), facecolor='white')
    delta_t=0.1;
    time_steps=np.arange(1,T+1,1)
    plt.pcolormesh(np.arange(0,num_qubits,1), time_steps*delta_t, probability_density,vmin=0,vmax=np.max(probability_density))
    plt.xticks([x for x in range(args.N)],[x for x in range(args.N)])
    cb=plt.colorbar()
    #cb.set_ticks([0,0.5,1])
    #cb.set_ticklabels([0,0.5,1])
    #cb.set_ticks
    plt.xlabel('Qubit index', fontdict=font)
    plt.ylabel('Time (1/J)',fontdict=font)
    plt.tight_layout()
    fig.savefig(subd+'/N_{}_ex_{}_Jp_{:.1f}.png'.format(num_qubits,exls,args.Jp))


if __name__=='__main__':
    ## To run,
    ## command line
    ## python xyssh_sim.py 8 4 07 1
    global T
    T=20
    t1=time.time()
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('N', type=int,help='num_qubits')
    parser.add_argument('Jp', type=float,help='bond strength')
    parser.add_argument('exls', type=list,help='excitation, which qubits set to |1>')
    parser.add_argument('order', type=list,help='Trotter order')
    args=parser.parse_args()
    num_qubits=args.N
    print(args.exls)
    subddate='{:02.0f}{:02.0f}{}'.format(time.localtime().tm_mon, time.localtime().tm_mday, time.localtime().tm_year)
    probden(exls=[int(i) for i in args.exls],subdate=subddate)

