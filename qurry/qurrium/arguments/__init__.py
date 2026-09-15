"""The Arguments of Qurrium Experiment (:mod:`qurry.qurrium.arguments`)

This module originally below :mod:`qurry.qurrium.experiment.arguments`.
But since :mod:`qurry.qurrium.arguments` is shared by both
:mod:`qurry.qurrium.analysis` and :mod:`qurry.qurrium.experiment`,
it is moved to :mod:`qurry.qurrium.arguments` as independent module.
"""

from .commonparams import Commonparams, CommonparamsDict
from .arguments import ArgumentsPrototype, _A, create_all_arguments
