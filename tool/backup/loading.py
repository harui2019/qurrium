import threading
import time
from typing import (
    Union,
    Callable,
    Generator,
    Iterable,
)

_lock = threading.Lock()

class Gajima():
    """Another after another loading bar in Python, 
    are there any other Squidwards(X) python progressbar(O) ?

    - Why this name ?
        It's meaning "Don't leave" in Korean.
        Select this name because when I tested its main function,
        I was listening "TVXQ - Catch Me (Korean ver.)", and "Gajima" is its lyrics.
        So there is it.

    """

    def __init__(
        self,
        iterable: Iterable = range(1),
        prefix: str = '| ',
        desc: str = "Loading",
        finish_desc: str = "Completed",
        delay: Union[int, float] = 0.1,
        carousel: Union[tuple[str, any],
                        list[tuple[str, any]]] = ('dots', 15, 6),
        ANSIDecorator: str = "\u001b[1m",
        leave: bool = True,

    ):
        self.delay = delay
        self.prefix = prefix
        self.desc = desc
        self.finish_desc = finish_desc
        self.ANSIDecorator = ANSIDecorator
        self.leave = leave

        self.running = False
        self.end = False
        self.threadLoading = None
        self.all_placeholder_len = 100

        # Preparing iterable objects
        if not isinstance(iterable, Iterable):
            raise ValueError("Getting a not iterable object.")
        self.iterable = [v for v in iterable]
        self._cur_index = 0
        self._iter_len = len(self.iterable)

        if not isinstance(carousel, list):
            carousel = [carousel]

        # Preparing loading and progress carousel
        self.carousels = []
        self.loading_carousel_dict = {
            'spinner': self.spinning_cursor,
            'dots': self.moving_dots,
        }
        self.progress_carousel_dict = {
            'basic': self.basic_progress_show,
        }

        is_progress_call = False
        for params in carousel:
            if not isinstance(params, tuple):
                params = (params, )

            if params[0] in self.loading_carousel_dict:
                self.carousels.append(
                    self.loading_carousel_dict[params[0]](*params[1:]))
            elif params[0] in self.progress_carousel_dict:
                is_progress_call = True
                self.carousels.append(
                    self.progress_carousel_dict[params[0]](*params[1:]))

        if not is_progress_call and self._iter_len > 1:
            self.carousels.append(
                self.progress_carousel_dict['basic']())

    def add_loading_carousel(
        self,
        key: str,
        loading_carousel: callable,
    ) -> list[str]:
        self.loading_carousel_dict[key] = loading_carousel
        return list(self.loading_carousel_dict.keys())

    def add_progress_carousel(
        self,
        key: str,
        progress_carousel: callable,
    ) -> list[str]:
        self.progress_carousel_dict[key] = progress_carousel
        return list(self.progress_carousel_dict.keys())

    @staticmethod
    def spinning_cursor() -> Generator[str, None, None]:
        while 1:
            for cursor in '|/-\\':
                yield cursor

    @staticmethod
    def moving_dots(
        length: int = 10,
        dots: int = 4
    ) -> Generator[str, None, None]:
        while 1:
            for i in range(length):
                dots_str_raw = ('.'*dots+' '*(length-dots))*2
                dots_str = dots_str_raw[length-i:2*length-i]
                yield dots_str

    @staticmethod
    def basic_progress_show() -> Callable[[int, int], Generator[str, None, None]]:
        def main(
            _index: int = 0,
            _total: int = 1,
        ) -> Generator[str, None, None]:
            while 1:
                _total_str = str(_total)
                progress_str_raw = f" - {str(_index).rjust(len(_total_str), ' ')}/{_total_str}"
                yield progress_str_raw
        return main

    def loading(self):
        """
        If want to nest, print text need to be independent
        """
        cur = time.time()
        carousel_str = ''
        finished_desc = self.ANSIDecorator + self.finish_desc + "\u001b[0m"
        while not self.end:
            decorated_desc = self.ANSIDecorator + self.desc
            carousel_str = ' '
            for carousel in self.carousels:
                if isinstance(carousel, Generator):
                    carousel_str += next(carousel)
                elif isinstance(carousel, Callable):
                    carousel_str += next(carousel(
                        _index=self._cur_index,
                        _total=self._iter_len,
                    ))
                else:
                    ...

            time.sleep(self.delay)
            print(
                self.prefix+decorated_desc +
                carousel_str+"\u001b[0m"+f' - {round(time.time() - cur, 2)}s',
                end="\r")
            if self.end:
                break

        # Preparing ending title
        end_progress = ''
        for carousel in self.carousels:
            if isinstance(carousel, Callable):
                end_progress += next(carousel(
                    _index=self._iter_len,
                    _total=self._iter_len,
                ))
        end_time_str = f' - {round(time.time() - cur, 2)}s'

        # Placeholder
        carousal_placeholder_len = len(
            decorated_desc+carousel_str+"\u001b[0m") - len(finished_desc)
        progress_placeholder_len = len(end_progress)
        self.all_placeholder_len = len(
            self.prefix+end_time_str) + carousal_placeholder_len + 10

        print(" "*self.all_placeholder_len, end="\r")
        if self.leave:
            print(
                self.prefix + finished_desc + end_progress +
                " "*(carousal_placeholder_len - progress_placeholder_len) +
                end_time_str)
        else:
            print(" "*self.all_placeholder_len, end="\r")

    def gprint(self, *args, **kwargs) -> None:
        print(" "*self.all_placeholder_len, end="\r")
        print(*args, **kwargs)

    def run(self):
        if self.running:
            return
        self.running = True
        self.end = False
        self.threadLoading = threading.Thread(target=self.loading)
        self.threadLoading.start()

    def stop(self):
        if isinstance(self.threadLoading, threading.Thread):
            self.end = True
            self.threadLoading.join()
        else:
            print("Loading is not active.")

    def __iter__(self):
        if self._cur_index == 0:
            self.run()
        while self._cur_index < self._iter_len:
            yield self.iterable[self._cur_index]
            self._cur_index += 1
            if self._cur_index >= self._iter_len:
                self.stop()

    def __enter__(self):
        self.run()
        return self

    def __exit__(self, exception, exc_val, exc_tb):
        self.stop()
        if exception is not None:
            return False


def grange(*args, **kwargs) -> Gajima:
    """
    A shortcut like :func:`trange` from :module:`tqdm`
    """
    return Gajima(range(*args), **kwargs)
