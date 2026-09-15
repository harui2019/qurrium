"""CapSule - Qurrium Data Structure Complex and I/O Utilities (:mod:`qurry.capsule`)

## Why names CapSule?

- CapSule
    It's also not possible I named this for there is a song
    called `CapSule <https://youtu.be/M85xU-tbQ6c?si=Ysk7pJu1eKIMOCBv>`_
    by Mori Calliope and Hoshimachi Suisei.
    It must be a coincidence. :3

"""

import webbrowser
from random import random
import logging

from .mori import (
    key_tuple_loads,
    tuple_str_parse_ensured,
    tuple_str_parse,
    jsonablize,
    quickJSON,
    quick_json_write,
)
from .hoshi import repr_modifier, EasyReprModify, Hoshi
from .gitsync import GitSyncControl
from .custom_dict import CustomDict
from .utils import DEFAULT_ENCODING, DEFAULT_INDENT, DEFAULT_MODE


logger = logging.getLogger(__file__)


@repr_modifier("<MoriCalliope.SEEING_STARS>")
def feeling_sad_then_call_this_function():
    """Don't look back, look forward

    Find something you can move toward
    Don't look back, look forward
    Don't look back

    """
    webbrowser.open("https://www.youtube.com/watch?v=X_4pIzwShRw")

    logger.info("| Don't look back, look forward.")
    logger.info("| Find something you can move toward.")
    logger.info("| Don't look back, look forward.")
    logger.info("| Don't look back.")


@repr_modifier("<MoriCalliope.CapSule>")
def capsule():
    """Why there is a link to the song "CapSule" by Mori Calliope and Hoshimachi Suisei?
    This package is definitely not related to any Vtuber, right?
    It must be a coincidence. :3
    """
    webbrowser.open("https://www.youtube.com/watch?v=M85xU-tbQ6c")


@repr_modifier("<MoriCalliope.Guh>")
def guh():
    """Guh~"""
    webbrowser.open("https://www.youtube.com/watch?v=n8Q-smqaUgA")
    logger.info("Guh~")


@repr_modifier("<HoshimachiSuisei.Talalalala>")
def talalalala():
    """Talalalala~"""
    webbrowser.open("https://www.youtube.com/watch?v=_RPkBzv2jYc")
    logger.info("Talalalala~")


def dead_beats_lurking_now():
    """Dead Beats Lurking Now~
    Dead Beats Lurking Now~
    Dead Beats Lurking Now~

    This function makes no sense.
    """
    webbrowser.open("https://www.youtube.com/watch?v=6ydgEipkUEU")
    logger.info("| Dead Beats Lurking Now~")
    logger.info("| Dead Beats Lurking Now~")
    logger.info("| Dead Beats Lurking Now~")
    logger.info("| This function makes no sense.")


@repr_modifier("<INTERNET_YAMERO>")
def internet_is_fxxking_awesome():
    """Internet is Fxxking Awesome!

    Rushing through me is Ecstasy
    Lovely dreams brought through heavenly Myslee
    Yearn for your material touch
    Swim in cyber euphoria internet boy
    """
    if random() <= 0.2:
        webbrowser.open("https://www.youtube.com/watch?v=51GIxXFKbzk")
        logger.info("| Intaanetto saikou!!!")
        logger.info("| ")
        logger.info("| hotobashiru ekusutashii")
        logger.info("| amai yume o misete maisurii")
        logger.info("| yubisaki de kanjiru oyogu")
        logger.info("| denshi no umi intanetto booi")

    else:
        webbrowser.open("https://www.youtube.com/watch?v=Lp5n-YS22tY")
        logger.info("| Internet is Fxxking Awesome!!!")
        logger.info("| ")
        logger.info("| Rushing through me is Ecstasy")
        logger.info("| Lovely dreams brought through heavenly Myslee")
        logger.info("| Yearn for your material touch")
        logger.info("| Swim in cyber euphoria internet boy")
