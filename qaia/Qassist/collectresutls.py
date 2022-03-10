import os
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
import json
import argparse
from qiskit.providers.ibmq.managed import IBMQJobManager
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
sample_shots = 8192
global KK, T


def plot(J0=0, subd='./data'):
    PLOT = True

    for a, b, fls in os.walk(subd):
        phasels = []
        tls = []
        for f in sorted(fls):
            if f.endswith(('png', 'txt', 'DS_Store')):
                continue
            fn = subd+f
            t = f[:-4].split('_')[-1]
            tls.append(float(t))
            data = np.loadtxt(fn)
            Xls = data[1, :]
            Yls = data[2, :]
            data = zip(Xls, Yls)
            P = 1  # + 0.j
            for x in list(data):
                zz = x[0] + 1.j * x[1]
                #zz = zz / abs(zz)

                P *= zz
            phasels.append(np.log(P).imag)
        if PLOT:
            T = len(phasels)
            plt.scatter(tls, np.array(phasels), color='b')
            plt.plot(tls, phasels, color='b')
            #plt.ylim([-1, 1])

            plt.xticks([0, pi/4, pi/2], ['0', '1/4', '1/2'],
                       fontsize=18, fontweight='bold')
            plt.yticks([-pi, -pi/2, 0, pi/2, pi], ['-1', '-1/2',
                       '0', '1/2', '1'], fontsize=18, fontweight='bold')
            plt.xlabel(r'$t / \pi$', fontdict=font)
            plt.ylabel(r'$\gamma/ \pi$', fontdict=font)
            plt.tight_layout()

    plt.savefig(subd + 'J0_{:.2f}.png'.format(J0))
    plt.show()


def compute(results, subd, J0):
    dt = pi / T
    trange = np.arange(0, T)

    for t in trange:
        Xls = []
        Yls = []
        fn = subd + 'J0_{:.2f}_t_{:.2f}.dat'.format(J0, (t+1)*dt/2)
        for k in range(KK):
            i = int(t*KK+k)
            count = results.get_counts(i)
            xcount, ycount = trace_count(count)
            xval = expval(xcount)
            yval = expval(ycount)
            Xls.append(xval)
            Yls.append(yval)
        data = zip(Xls, Yls)
        P = 1 + 0.j
        for x in list(data):
            zz = x[0]+1.j*x[1]
            # zz=zz/abs(zz)
            P *= zz
        Xls = np.array(Xls)
        Yls = np.array(Yls)
        np.savetxt(fn, np.vstack((np.linspace(0, KK - 1, KK), Xls, Yls)))
    return


def trace_count(count):
    xcount = {}
    ycount = {}
    xcount['0'] = count.get('00', 0) + count.get('10', 0)
    xcount['1'] = count.get('01', 0) + count.get('11', 0)
    ycount['0'] = count.get('00', 0) + count.get('01', 0)
    ycount['1'] = count.get('10', 0) + count.get('11', 0)
    return xcount, ycount


def expval(result_sim):
    P_0 = result_sim.get('0', 0)/sample_shots
    P_1 = result_sim.get('1', 0)/sample_shots
    ans = P_0-P_1
    return ans


def run(job_set_id='b9220e9731c6412083d3a1e805fa1f92-162593189864047', device='ibmq_jakarta', J0=2):
    DATE = True
    phasels = []
    t1 = time.time()
    subd = './data/KK_{:.0f}_shots_{:.0f}/'.format(KK, sample_shots)
    if not os.path.exists(subd):
        os.mkdir(subd)
    subd += str(device)
    if not os.path.exists(subd):
        os.mkdir(subd)
    subd += '/J0_{:.2f}/'.format(J0)
    if not os.path.exists(subd):
        os.mkdir(subd)
    subddate = '{:02.0f}{:02.0f}{}/'.format(
        time.localtime().tm_mon, time.localtime().tm_mday, time.localtime().tm_year)
    if DATE:
        subd += subddate
    if not os.path.exists(subd):
        os.mkdir(subd)
    subd += job_set_id.split('-')[-1]+'/'
    if not os.path.exists(subd):
        os.mkdir(subd)
    print(subd)
    retrieved_foo = IBMQJobManager().retrieve_job_set(
        job_set_id=job_set_id, provider=ntuprovider, refresh=True)
    results = retrieved_foo.results()
    print(retrieved_foo.report())
    compute(results, subd, J0)
    plot(J0=J0, subd=subd)


def get_from_json(fn='job_07142021_toronto.log'):
    with open(fn, 'r') as f:
        datainfo = json.load(f)
    print(len(datainfo), datainfo[0])
    N = len(datainfo)
    global KK, T
    for i in range(N):
        onejob = datainfo[i]
        print('running job {}'.format(i))

        KK = onejob['KK']
        T = onejob['T']
        run(job_set_id=onejob['jobsets_id'],
            device=onejob['device'], J0=onejob['J0'])
    #tweets = []
    # for line in open(fn, 'r'):
    #    tweets.append(json.loads(line))


if __name__ == '__main__':
    #retrieved_foo = IBMQJobManager().retrieve_job_set(job_set_id='4ab1619fb807408493abce1e80db2446-1625931164415933', provider=ntuprovider, refresh=True)
    # results=retrieved_foo.results()
    # KK=20;T=10
    #run(job_set_id="59f09fbccd4d4bdca68198dd931848e4-1625990148041992", device='ibmq_toronto', J0=2)
    get_from_json()
