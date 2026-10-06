"""A small NumPy MLP. The agent edits this file to lower val_loss."""

import time

import numpy as np

from prepare import TIME_BUDGET, evaluate, load_data

HIDDEN = 16
LR = 0.01
BATCH = 32

(x, y), _ = load_data()
rng = np.random.default_rng(0)
w1 = rng.normal(0, 1, (2, HIDDEN))
b1 = np.zeros(HIDDEN)
w2 = rng.normal(0, 1, (HIDDEN, 1))
b2 = np.zeros(1)


def forward(xb):
    h = np.tanh(xb @ w1 + b1)
    return h, h @ w2 + b2


start = time.time()
steps = 0
while time.time() - start < TIME_BUDGET:
    idx = rng.integers(0, len(x), BATCH)
    xb, yb = x[idx], y[idx]
    h, out = forward(xb)
    g_out = 2 * (out - yb) / BATCH
    g_w2, g_b2 = h.T @ g_out, g_out.sum(0)
    g_h = g_out @ w2.T * (1 - h**2)
    g_w1, g_b1 = xb.T @ g_h, g_h.sum(0)
    w1 -= LR * g_w1
    b1 -= LR * g_b1
    w2 -= LR * g_w2
    b2 -= LR * g_b2
    steps += 1

print(f"steps: {steps}")
print(f"val_loss: {evaluate(lambda xv: forward(xv)[1]):.6f}")
