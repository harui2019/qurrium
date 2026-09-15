"""Post Processing - Classical Shadow - Utilities (:mod:`qurry.process.classical_shadow.utils`)

There is a more memory efficient way to store the random basis,
which is :class:`list[list[int]]` instead of :class:`dict[int, dict[int, int]]`.
But we use :class:`dict[int, dict[int, int]]`, it's because the annoying
mapping between qubit index and classical bit index for quantum
circuit realizations and which circuit actually used which random basis.

For the format of :class:`dict[int, dict[int, int]]`: we will call `random_basis`.
For the format of :class:`list[list[int]]`: we will call `pauli_basis`.

## Data storage format

- Single shots basis-spin Output format (for PQP)

.. code-block:: text

    [system size]
    [X/Y/Z for qubit 1] [-1/1 for qubit 1] [X/Y/Z for qubit 2] [-1/1 for qubit 2] ...
    [X/Y/Z for qubit 1] [-1/1 for qubit 1] [X/Y/Z for qubit 2] [-1/1 for qubit 2] ...
    ...


- Single (single-shots) basis-spin storage format

.. code-block:: text

    For X/Y/Z mapping to 0/1/2, and bit 0/1 mapping to spin -1/1:

    `pauli_basis`         `spin_list`
    [0, 1, 2, 0, 1, ...]  [-1, 1, -1, -1, 1, ...]
    [2, 2, 0, 1, 0, ...]  [1, 1, -1, 1, -1, ...]
    ...


- Weighted (multi-shots) basis-spin storage format (Proposal)

.. code-block:: text

    For X/Y/Z mapping to 0/1/2, and bit 0/1 mapping to spin -1/1:

    `all_counts_result`
    [
        (result information for snapshot 0),
        (result information for snapshot 1),
        ...
    ]

    - result information of single snapshot:

        pauli_basis           spin_list               counts_num
        [0, 1, 2, 0, 1, ...]  [-1, 1, -1, -1, 1, ...]  23
        [2, 2, 0, 1, 0, ...]  [1, 1, -1, 1, -1, ...]   30
        ...

        shots
        1024

    result information of single snapshot = (
        [list of pauli_basis], [list of spin_list], [list of counts_num], shots
    )

"""

from .random_basis import (
    generate_random_basis,
    generate_all_possible_basis_array,
    make_evenly_basis_array,
    make_evenly_basis,
    validate_random_basis,
    check_random_basis,
    check_random_basis_array,
)
from .spreadout import spreadout
from .basis_spin_fmt import convert_to_basis_spin, measurements_export, measurements_read
