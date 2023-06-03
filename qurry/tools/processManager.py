import time
import tqdm
import numpy as np
from tqdm.contrib.concurrent import process_map
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Union, Optional, NamedTuple, Hashable, Iterable, Callable



# Ready for issue #75 https://github.com/harui2019/qurry/issues/75

DEFAULT_POOL_SIZE = cpu_count() - 2
    

class ProcessManager:
    ...