"""Post Processing - Utils - Other (:mod:`qurry.process.utils.other`)"""

import numpy as np

NUMERICAL_ERROR_TOLERANCE = 1e-14
"""Tolerance for numerical errors in calculations.
This is used to determine if two floating-point numbers are close enough to be considered equal.

The default value is set to `1e-14`.
"""

FloatType = np.float64 | float
"""A type alias for floating-point numbers. 

This can be either a :class:`~numpy.float64` or a built-in `float`.
"""
