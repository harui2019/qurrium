#!/usr/bin/env python
# coding: utf-8


from qiskit import *
from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit import IBMQ, Aer, execute
from qiskit.tools.monitor import job_monitor, backend_monitor, backend_overview
from qiskit.providers.ibmq import least_busy
from qiskit.tools.visualization import plot_histogram
from math import exp, sin, cos, sqrt, acos, asin, pi
import numpy as np
import matplotlib.pyplot as plt
import time
import argparse
from qiskit.providers.ibmq.managed import IBMQJobManager
import json
import collectresutls as R
font = {'family': 'sans',
        'color': 'black',
        'weight': 'bold',
        'size': 20,
        }
params = {'legend.fontsize': 16,
          'legend.handlelength': 1}
plt.rcParams.update(params)
IBMQ.load_account()
ntuprovider = IBMQ.get_provider(
    hub='ibm-q-hub-ntu', group='ntu-internal', project='default')


def setup(machine_name):

    #ntuprovider=IBMQ.get_provider(hub='ibm-q-hub-ntu', group='ntu-internal', project='default')
    # print(ntuprovider.backends())

    #openprovider=IBMQ.get_provider(hub='ibm-q', group='open', project='main')
    # print(openprovider.backends())

    simulator = BasicAer.get_backend('qasm_simulator')
    vectorsim = BasicAer.get_backend('statevector_simulator')
    if machine_name is not '':
        qdevice = ntuprovider.get_backend(machine_name)

        return simulator, vectorsim, qdevice
    else:
        return simulator, vectorsim, None


global J0
global KK
global dk
global device
global T
J1 = 1
sample_shots = 8192


def time_evol(circ, q, a, k, t):
    hx = J0-J1*cos(k*dk)
    hy = J1*sin(k*dk)
    phi = np.log(hx+1.j*hy).imag-pi/2
    lamb = -1*phi
    theta = 2*t
    #circ.cu3(theta, phi, lamb, control_qubit=a[0], target_qubit=q[0])
    #circ.cu3(theta, phi, lamb, control_qubit=a[1], target_qubit=q[1])
    circ.u3(theta, phi, lamb, q[0])
    circ.u3(theta, phi, lamb, q[1])


def overlap(circ, q, a, k, t):
    hx = J0 - J1 * cos(k * dk)
    hy = J1 * sin(k * dk)
    phi = np.log(hx + 1.j * hy).imag + pi / 2
    lamb = -1 * phi
    theta = 2 * t
    circ.cu(theta, phi, lamb, 0, control_qubit=a[0], target_qubit=q[0])
    circ.cu(theta, phi, lamb, 0, control_qubit=a[1], target_qubit=q[1])
    k = (k+1) % KK
    hx = J0-J1*cos(k*dk)
    hy = J1*sin(k*dk)
    phi = np.log(hx + 1.j * hy).imag - pi / 2
    lamb = -1*phi
    theta = 2*t
    circ.cu(theta, phi, lamb, 0, control_qubit=a[0], target_qubit=q[0])
    circ.cu(theta, phi, lamb, 0, control_qubit=a[1], target_qubit=q[1])


def circuit(k, t=pi / 4):
    q = QuantumRegister(2, name='state')
    a = QuantumRegister(2, name='ancilla')
    c = ClassicalRegister(2, name='real')
    circ = QuantumCircuit(a, q, c)
    circ.h(a)
    time_evol(circ, q, a, k, t)
    overlap(circ, q, a, k, t)
    circ.ry(-pi / 2, a[0])
    circ.measure(a[0], c[0])
    circ.rx(pi / 2, a[1])
    circ.measure(a[1], c[1])
    return circ


def sub_manager():
    dt = pi / T
    trange = np.arange(1, T+1)
    circls = []
    for t in trange:
        for k in range(KK):
            circ = circuit(k, t*dt/2)
            circls.append(circ)

    circs = transpile(circls, backend=device)
    job_manager = IBMQJobManager()
    job_set_foo = job_manager.run(
        circs, backend=device, name='foo', shots=8192)
    print('status={},circuit={}'.format(job_set_foo.statuses(), len(circls)))
    job_set_id = job_set_foo.job_set_id()
    print(job_set_id)
    print('J0={}, KK={}, dk={}'.format(J0, KK, dk))
    return job_set_foo


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='J0')
    parser.add_argument('J0', type=float, help='J0')
    parser.add_argument('KK', type=int, help='KK')
    parser.add_argument('T', type=int, help='T')
    parser.add_argument('machine', type=str,
                        help='assign machine', default=None)
    args = parser.parse_args()

    J0 = args.J0
    KK = args.KK

    T = args.T
    machine_name = args.machine
    dk = 2*pi/KK
    if machine_name == '':
        print('simulator')
    simulator, vectorsim, qdevice = setup(machine_name=machine_name)
    if machine_name is '':
        device = simulator  # choose machine
    else:
        device = qdevice

    jobsets = sub_manager()
    job_set_id = jobsets.job_set_id()
    print(job_set_id)
    print('J0={}, KK={}, dk={}'.format(J0, KK, dk))
    print(device)
    subddate = '{:02.0f}{:02.0f}{}'.format(
        time.localtime().tm_mon, time.localtime().tm_mday, time.localtime().tm_year)
    joblog = {}
    joblog['device'] = machine_name
    joblog['jobsets_id'] = job_set_id
    joblog['J0'] = J0
    joblog['KK'] = KK
    joblog['T'] = T

    joblog['date'] = subddate
    joblog['time'] = '{}:{}'.format(
        time.localtime().tm_hour, time.localtime().tm_min)
    fn = 'job_{}_{}.log'.format(subddate, machine_name.split('_')[-1])
    with open(fn, 'a') as f:
        json.dump(joblog, f, ensure_ascii=False, indent=2)
        f.write(',\n')
    stat = jobsets.statuses()
    print(stat)
    #R.run(job_set_id=job_set_id, device=machine_name, J0=J0)
