# How Gajima makes

- __iter__:
  - [iter參考](https://medium.com/citycoddee/python進階技巧-6-迭代那件小事-深入了解-iteration-iterable-iterator-iter-getitem-next-fac5b4542cf4)

- dynamic `typing.Literal`:
  - [source](https://stackoverflow.com/questions/66785205/python-type-hints-how-to-do-a-literal-range)
  - It's actually used in `qurry.qurstrop`, not `Gajima`.

  ```py
  from typing import Literal

  A = Literal[1,2]
  B = Literal[(1,2)]
  print(A == B) # True

  C = Literal[tuple(range(100))]
  print(C)
  # typing.Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
  ```
