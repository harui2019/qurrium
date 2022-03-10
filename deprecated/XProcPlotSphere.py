import numpy as np
import matplotlib.pyplot as plt

RXmatrix = np.array([[0, 1], [1, 0]])
RYmatrix = np.array([[0, -1j], [1j, 0]])
RZmatrix = np.array([[1, 0], [0, -1]])


def densityMatToBlochVector(rho):
    """
        Convert a density matrix to a Bloch vector.

        When transform a random unitary operator,
        det(Op.) has been normalized,
        but trace(Op.) doesn't., even so on trace(Op.).real
    """

    ax = np.trace(np.dot(rho, RXmatrix)).real
    ay = np.trace(np.dot(rho, RYmatrix)).real
    az = np.trace(np.dot(rho, RZmatrix)).real
    return [ax, ay, az]


def triQubitToCoor(result):
    countsGetcha = result.get_counts()
    shots = result.results[0].shots
    Counts = (lambda target: countsGetcha.get(target, 0)/shots)
    # expval_X
    px_0 = (Counts('000')+Counts('010')+Counts('110')+Counts('100'))
    px_1 = (Counts('001')+Counts('011')+Counts('111')+Counts('101'))
    # expval_Y
    py_0 = (Counts('000')+Counts('100')+Counts('101')+Counts('001'))
    py_1 = (Counts('010')+Counts('110')+Counts('111')+Counts('011'))
    # expval_Z
    pz_0 = (Counts('000')+Counts('010')+Counts('011')+Counts('001'))
    pz_1 = (Counts('100')+Counts('110')+Counts('111')+Counts('101'))

    cor = [(px_0 - px_1), (py_0 - py_1), (pz_0 - pz_1)]
    cora = cor / np.linalg.norm(cor)
    ncor = cora.tolist()
    return ncor


def plotBlochSphere(bloch_vectors):
    """ Helper function to plot vectors on a sphere."""
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection='3d')
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)

    ax.grid(False)
    ax.set_axis_off()
    ax.view_init(30, 45)
    ax.dist = 7

    # Draw the axes (source: https://github.com/matplotlib/matplotlib/issues/13575)
    x, y, z = np.array([[-1.5, 0, 0], [0, -1.5, 0], [0, 0, -1.5]])
    u, v, w = np.array([[3, 0, 0], [0, 3, 0], [0, 0, 3]])
    ax.quiver(x, y, z, u, v, w, arrow_length_ratio=0.05,
              color="black", linewidth=0.5)

    ax.text(0, 0, 1.7, r"|0⟩", color="black", fontsize=16)
    ax.text(0, 0, -1.9, r"|1⟩", color="black", fontsize=16)
    ax.text(1.9, 0, 0, r"|+⟩", color="black", fontsize=16)
    ax.text(-1.7, 0, 0, r"|–⟩", color="black", fontsize=16)
    ax.text(0, 1.7, 0, r"|i+⟩", color="black", fontsize=16)
    ax.text(0, -1.9, 0, r"|i–⟩", color="black", fontsize=16)

    ax.scatter(
        bloch_vectors[:, 0], bloch_vectors[:, 1], bloch_vectors[:, 2], c='#e29d9e', alpha=0.3
    )

    return fig


def purity(result):
    AncMeas = result.get_counts()
    indexOfCounts = list(AncMeas.keys())
    isZeroInclude = '0' in indexOfCounts
    isOneInclude = '1' in indexOfCounts
    shots = sum(AncMeas.values())
    purity = 0  # purity
    if isZeroInclude and isOneInclude:
        purity = (AncMeas['0'] - AncMeas['1'])/shots
    elif isZeroInclude:
        purity = AncMeas['0']/shots
    elif isOneInclude:
        purity = AncMeas['1']/shots
    else:
        purity = None
        raise Warning("Expected '0' and '1', but there is no such keys")

    return purity
