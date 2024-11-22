"""

================================================================
CapSule - Qurry Data Structure Complex 

## Why CapSule?

- Mori
    There are many dedicated data structures for Qurry 🍛 
    If we say one of them like a tree in forest, 
    then all data structures combine, 
    it makes a forest or '森' read as mori in Japanese. 
    Definitely NOT because I'm a DeadBeat, 
    the fan of Hololive VTuber Mori Calliope, 
    and I didn't want to name something after her for a not short time.

- Hoshi
    I made it when I was listening the songs made by Hoshimachi Suisei, 
    a VTuber in Hololive. I was inspired by her songs, and I made this tool. 
    I named it Hoshi, which means star in Japanese. 
    I hope this tool can help you to make your code more beautiful.

    (Hint: The last sentence is auto-complete by Github Copilot from 'Hoshimachi' to the end. 
    That's meaning that Github Copilot knows VTuber, Hololive, even Suisei, 
    who trains it with such content and how. 
    "Does Skynet subscribe to Virtual Youtuber?")

- CapSule
    It's also not possible I named this for there is a song 
    called [CapSule](https://youtu.be/M85xU-tbQ6c?si=Ysk7pJu1eKIMOCBv)
    by Mori Calliope and Hoshimachi Suisei.
    I must be a coincidence. :3

================================================================
"""

import webbrowser
from random import random

from .jsonablize import parse as jsonablize, quickJSONExport, sort_hashable_ahead
from .quick import quickJSON, quickListCSV, quickRead
from .hoshi import repr_modifier as _repr_modifier

# pylint: disable=invalid-name


def CapSule():
    """Why there is a link to the song "CapSule" by Mori Calliope and Hoshimachi Suisei?
    This package is definitely not related to any Vtuber, right?
    I must be a coincidence. :3
    """
    webbrowser.open("https://www.youtube.com/watch?v=M85xU-tbQ6c")


def guh():
    """Guh~"""
    webbrowser.open("https://www.youtube.com/watch?v=n8Q-smqaUgA")
    print("Guh~")


def talalalala():
    """Talalalala~"""
    webbrowser.open("https://www.youtube.com/watch?v=_RPkBzv2jYc")
    print("Talalalala~")


def dead_beats_lurking_now():
    """Dead Beats Lurking Now~
    Dead Beats Lurking Now~
    Dead Beats Lurking Now~

    This function makes no sense.
    """
    webbrowser.open("https://www.youtube.com/watch?v=6ydgEipkUEU")
    print("Dead Beats Lurking Now~")
    print("Dead Beats Lurking Now~")
    print("Dead Beats Lurking Now~")

    print("This function makes no sense.")


@_repr_modifier("<INTERNET_YAMERO>")
def internet_is_fxxking_awesome():
    """Internet is Fxxking Awesome!

    Rushing through me is Ecstasy
    Lovely dreams brought through heavenly Myslee
    Yearn for your material touch
    Swim in cyber euphoria internet boy
    """
    if random() <= 0.2:
        webbrowser.open("https://www.youtube.com/watch?v=51GIxXFKbzk")
        print("Intaanetto saikou!!!")
        print()
        print("hotobashiru ekusutashii")
        print("amai yume o misete maisurii")
        print("yubisaki de kanjiru oyogu")
        print("denshi no umi intanetto booi")

    else:
        webbrowser.open("https://www.youtube.com/watch?v=Lp5n-YS22tY")
        print("Internet is Fxxking Awesome!!!")
        print()
        print("Rushing through me is Ecstasy")
        print("Lovely dreams brought through heavenly Myslee")
        print("Yearn for your material touch")
        print("Swim in cyber euphoria internet boy")


def your_need_earbuds_then_call_this_function():
    """I have warned you. You need earbuds to call this function."""
    if random() <= 0.2:
        webbrowser.open("https://www.nicovideo.jp/watch/sm19233263")
    else:
        webbrowser.open("https://www.youtube.com/watch?v=4w3zoAbxkbo")


# pylint=enable=invalid-name
