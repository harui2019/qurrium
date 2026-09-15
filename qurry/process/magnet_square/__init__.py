"""Post Processing - Magnetization Square (:mod:`qurry.process.magnet_square`)"""

from .magsq_core import BACKEND_AVAILABLE as magnet_square_availability, DEFAULT_PROCESS_BACKEND
from .magnet_square import magnetization_square, z_dir_magnetization_square, MagnetSquareResult
