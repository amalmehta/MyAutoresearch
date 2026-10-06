"""Fixed data, time budget and evaluation. The agent may not edit this file."""

import numpy as np

TIME_BUDGET = 10.0  # seconds of training per experiment


def _target(x):
    return np.sin(3 * x[:, 0]) * np.cos(2 * x[:, 1]) + 0.3 * x[:, 0] ** 2 - 0.2 * x[:, 1]


def load_data():
    """Train and validation splits of a noisy 2-D regression task (same every run)."""
    rng = np.random.default_rng(1234)
    x = rng.uniform(-2, 2, size=(6000, 2))
    y = _target(x) + rng.normal(0, 0.05, size=len(x))
    return (x[:5000], y[:5000, None]), (x[5000:], y[5000:, None])


def evaluate(predict):
    """Mean squared error of predict(x_val) on the validation split."""
    _, (xv, yv) = load_data()
    pred = np.asarray(predict(xv), dtype=float).reshape(yv.shape)
    return float(np.mean((pred - yv) ** 2))
