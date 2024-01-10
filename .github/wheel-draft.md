# Note for wheel-draft.yml

Github CI is basically a x86 machine with difernet OS.
So they can do fast when they build x86 binary.

But when we build ARM binary for Mac, Fujitsu Quantum Simulator, or Raspberry Pi(?).
The cross compile of `cibuildwheel` is very slow.

So sometimes I will choose to build ARM binary on my own Mac for it's M2, an Arm system.
And I upload maunelly to PyPI.
