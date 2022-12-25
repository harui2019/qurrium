import psutil
import warnings
from typing import NamedTuple, Union
from collections import namedtuple

from ..exceptions import (
    QurryMemoryOverAllocationWarning,
    QurryInheritionNoEffect,
)


class ResoureWatch:
    __version__ = (0, 0, 2)
    """Preventing some experiments have very large allocating of memory
    making computer crashing.
    """
    class RESOURCE_LIMIT(NamedTuple):
        max_ram_percentage: float = 0.95
        min_ram_remain: int = 2**31

    save_lock_proto = namedtuple(
        'SAVE_LOCK',
        field_names=RESOURCE_LIMIT._fields,
        defaults=[True for k in RESOURCE_LIMIT._fields],
    )
    SAVE_LOCK = save_lock_proto(**{k: True for k in RESOURCE_LIMIT._fields})

    def __init__(
        self,
        *arg,
        max_ram_percentage: float = 0.95,
        min_ram_remain: int = 2**31,
        **kwargs,
    ) -> None:
        if len(arg) > 0:
            warnings.warn(
                "Please specify at least arguments to configure.",
                QurryInheritionNoEffect
            )

        self.ALLOW_LIMIT = self.RESOURCE_LIMIT(
            max_ram_percentage=max_ram_percentage,
            min_ram_remain=min_ram_remain,
        )
        self.judgement = None
        self.message = ''

    def disable(
        self, lock: str,
    ) -> None:
        if lock in self.RESOURCE_LIMIT._fields:
            self.SAVE_LOCK._replace(**{lock: False})
        else:
            print(f"| Lock '{lock}' does not exist.")

    def enable(
        self, lock: str,
    ) -> None:
        if lock in self.RESOURCE_LIMIT._fields:
            self.SAVE_LOCK._replace(**{lock: True})
        else:
            print(f"| Lock '{lock}' does not exist.")
            
    @staticmethod
    def virtual_memory() -> any:
        return psutil.virtual_memory()

    @property
    def judge(self) -> property:
        class Judge:
            class Check(NamedTuple):
                judge: bool = False
                lock: bool = False

            judge_proto = namedtuple(
                'Judge',
                field_names=self.RESOURCE_LIMIT._fields,
            )

            def max_ram_percentage(inner_self) -> bool:
                return self.virtual_memory().percent >= self.ALLOW_LIMIT.max_ram_percentage

            def min_ram_remain(inner_self) -> bool:
                return self.virtual_memory().available <= self.ALLOW_LIMIT.min_ram_remain

            def __call__(inner_self) -> bool:
                self.judgement = inner_self.judge_proto(**{
                    k: inner_self.Check(
                        inner_self.__getattribute__(k)(),
                        self.SAVE_LOCK.__getattribute__(k)
                    ) for k in self.RESOURCE_LIMIT._fields})

                return all([j and l for j, l in self.judgement])

        return Judge()

    def check(self, *message, return_stop_sign: bool = False) -> Union[Exception, bool]:
        if self.judge():
            self.message = " ".join(message)
            if return_stop_sign:
                raise QurryMemoryOverAllocationWarning(
                    "Resource usage breaks limit.",
                    self.message,
                    self.__repr__()
                )
            else:
                return False
        else:
            return True

    def __repr__(self) -> str:
        repr_items = {
            'ALLOW_LIMIT': self.ALLOW_LIMIT,
            'SAVE_LOCK': self.SAVE_LOCK,
            'current': psutil.virtual_memory()
        }
        repr_tmp = namedtuple('ResoureWatch', repr_items)
        return repr_tmp(**repr_items).__repr__()

    def __call__(self, *message: str, return_stop_sign: bool = False) -> Union[Exception, bool]:
        return self.check(message, return_stop_sign=return_stop_sign)

    @staticmethod
    def report() -> None:
        print(f"| Memory allocated: {psutil.virtual_memory().percent}/100")