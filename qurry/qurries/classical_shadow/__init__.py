r"""ShadowUnveil - Classical Shadow with The Results of Second Order Renyi Entropy
(:mod:`qurry.qurries.classical_shadow`)

Reference:
    -   Predicting many properties of a quantum system from very few measurements -
        Huang, Hsin-Yuan and Kueng, Richard and Preskill, John
        `doi:10.1038/s41567-020-0932-7 <https://doi.org/10.1038/s41567-020-0932-7>`_

    -   The randomized measurement toolbox -
        Elben, Andreas and Flammia, Steven T. and Huang, Hsin-Yuan and Kueng,
        Richard and Preskill, John and Vermersch, Benoît and Zoller, Peter
        `doi:10.1038/s42254-022-00535-2 <https://doi.org/10.1038/s42254-022-00535-2>`_

    .. code-block:: bibtex

        @article{cite-key,
            abstract = {
                Predicting the properties of complex,
                large-scale quantum systems is essential for developing quantum technologies.
                We present an efficient method for constructing an approximate classical
                description of a quantum state using very few measurements of the state.
                different properties; order
                {\$}{\$}{\{}{$\backslash$}mathrm{\{}log{\}}{\}}{$\backslash$},(M){\$}{\$}
                measurements suffice to accurately predict M different functions of the state
                with high success probability. The number of measurements is independent of
                the system size and saturates information-theoretic lower bounds. Moreover,
                target properties to predict can be selected after the measurements are completed.
                We support our theoretical findings with extensive numerical experiments.
                We apply classical shadows to predict quantum fidelities,
                entanglement entropies, two-point correlation functions,
                expectation values of local observables and the energy variance of
                many-body local Hamiltonians.
                The numerical results highlight the advantages of classical shadows relative to
                previously known methods.},
            author = {Huang, Hsin-Yuan and Kueng, Richard and Preskill, John},
            date = {2020/10/01},
            date-added = {2024-12-03 15:00:55 +0800},
            date-modified = {2024-12-03 15:00:55 +0800},
            doi = {10.1038/s41567-020-0932-7},
            id = {Huang2020},
            isbn = {1745-2481},
            journal = {Nature Physics},
            number = {10},
            pages = {1050--1057},
            title = {Predicting many properties of a quantum system from very few measurements},
            url = {https://doi.org/10.1038/s41567-020-0932-7},
            volume = {16},
            year = {2020},
            bdsk-url-1 = {https://doi.org/10.1038/s41567-020-0932-7}
        }

        @article{cite-key,
            abstract = {
                Programmable quantum simulators and quantum computers are opening unprecedented
                opportunities for exploring and exploiting the properties of highly entangled
                complex quantum systems. The complexity of large quantum systems is the source
                of computational power but also makes them difficult to control precisely or
                characterize accurately using measured classical data. We review protocols
                for probing the properties of complex many-qubit systems using measurement
                schemes that are practical using today's quantum platforms. In these protocols,
                a quantum state is repeatedly prepared and measured in a randomly chosen basis;
                then a classical computer processes the measurement outcomes to estimate the
                desired property. The randomization of the measurement procedure has distinct
                advantages. For example, a single data set can be used multiple times to pursue
                a variety of applications, and imperfections in the measurements are mapped to
                a simplified noise model that can more easily be mitigated. We discuss a range of
                cases that have already been realized in quantum devices, including Hamiltonian
                simulation tasks, probes of quantum chaos, measurements of non-local order
                parameters, and comparison of quantum states produced in distantly separated
                laboratories. By providing a workable method for translating a complex quantum
                state into a succinct classical representation that preserves a rich variety of
                relevant physical properties, the randomized measurement toolbox strengthens our
                ability to grasp and control the quantum world.},
            author = {
                Elben, Andreas and Flammia, Steven T. and Huang, Hsin-Yuan and Kueng,
                Richard and Preskill, John and Vermersch, Beno{\^\i}t and Zoller, Peter},
            date = {2023/01/01},
            date-added = {2024-12-03 15:06:15 +0800},
            date-modified = {2024-12-03 15:06:15 +0800},
            doi = {10.1038/s42254-022-00535-2},
            id = {Elben2023},
            isbn = {2522-5820},
            journal = {Nature Reviews Physics},
            number = {1},
            pages = {9--24},
            title = {The randomized measurement toolbox},
            url = {https://doi.org/10.1038/s42254-022-00535-2},
            volume = {5},
            year = {2023},
            bdsk-url-1 = {https://doi.org/10.1038/s42254-022-00535-2}
        }

- Short name: `classical_shadow`
- Acronym: `SU`

"""

from .analysis import SUAnalysis
from .arguments import SUMeasureArgs, SHORT_NAME, ACRONYM
from .experiment import SUExperiment
from .qurry import ShadowUnveil
