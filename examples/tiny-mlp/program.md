# Research Program: Tiny MLP

## Context
`train.py` trains a small NumPy MLP on a noisy 2-D regression task for a fixed
10-second budget (set in `prepare.py`, which you may not change). It prints
`val_loss`, the mean squared error on a fixed validation split. Lower is better.
The noise floor is about 0.0025, so that is roughly the best possible.

## Ideas worth trying
- Optimizer: momentum, Adam, learning-rate schedules.
- Architecture: width, depth, activation, initialisation.
- Batch size and how the time budget is spent.

## Rules
- NumPy only, CPU only. Don't add dependencies.
- Don't read the validation split for training; `evaluate()` is the only judge.
- One idea per experiment. At equal loss, prefer simpler code.
