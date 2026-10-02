"""Small inherited neural policy and value head, trained online.

Workers perform independent inference; the authoritative process owns training
and RNG. Optional accelerator inference uses batches of individual policies.
"""
import math
import multiprocessing
import os
from concurrent.futures import ProcessPoolExecutor

INPUTS, HIDDEN, ACTIONS = 28, 8, 7
PARAMS = INPUTS * HIDDEN + HIDDEN * ACTIONS
VALUE_PARAMS = HIDDEN + 1
DISCOUNT = .96


def forward(item):
    weights, obs = item
    active = [(i, value) for i, value in enumerate(obs) if value]
    hidden = []
    for j in range(HIDDEN):
        offset = j * INPUTS
        total = 0.0
        for i, value in active:
            total += weights[offset + i] * value
        hidden.append(math.tanh(total))
    base = INPUTS * HIDDEN
    logits = []
    for k in range(ACTIONS):
        offset = base + k * HIDDEN
        total = 0.0
        for j in range(HIDDEN):
            total += weights[offset + j] * hidden[j]
        logits.append(total)
    peak = max(logits)
    exps = [math.exp(v - peak) for v in logits]
    total = sum(exps)
    return hidden, [v / total for v in exps]


def learn(weights, obs, hidden, probabilities, action, advantage, rate=0.018):
    """REINFORCE gradient through both layers; bounded reward and weights."""
    advantage = max(-2.0, min(2.0, advantage))
    delta = [((1 if k == action else 0) - probabilities[k]) * advantage
             for k in range(ACTIONS)]
    base = INPUTS * HIDDEN
    back = []
    for j in range(HIDDEN):
        total = 0.0
        for k in range(ACTIONS):
            total += weights[base + k * HIDDEN + j] * delta[k]
        back.append(total * (1 - hidden[j] ** 2))
    active = [(i, value) for i, value in enumerate(obs) if value]
    for k in range(ACTIONS):
        for j in range(HIDDEN):
            ix = base + k * HIDDEN + j
            candidate = weights[ix] + rate * delta[k] * hidden[j]
            weights[ix] = -4 if candidate < -4 else 4 if candidate > 4 else candidate
    for j in range(HIDDEN):
        for i, value in active:
            ix = j * INPUTS + i
            candidate = weights[ix] + rate * back[j] * value
            weights[ix] = -4 if candidate < -4 else 4 if candidate > 4 else candidate


def predict_value(weights, hidden):
    """Bounded expected near-future reward from recurrent policy features."""
    total = weights[0]
    for j in range(HIDDEN):
        total += weights[j + 1] * hidden[j]
    return 2 * math.tanh(total)


def learn_value(weights, hidden, error, rate=.02):
    """One-step TD regression through the bounded value head."""
    error = max(-2.0, min(2.0, error))
    estimate = predict_value(weights, hidden)
    slope = 2 * (1 - (estimate / 2) ** 2)
    features = (1, *hidden)
    for i, feature in enumerate(features):
        candidate = weights[i] + rate * error * slope * feature
        weights[i] = -4 if candidate < -4 else 4 if candidate > 4 else candidate


def available_cpus():
    return len(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else (os.cpu_count() or 1)


class BrainEngine:
    def __init__(self, workers=0, device='cpu'):
        self.workers = workers or available_cpus()
        self.pool = None
        self.torch = None
        self.device = device
        if device != 'cpu':
            import torch
            if device != 'cuda' or not torch.cuda.is_available():
                raise RuntimeError('CUDA requested but no CUDA device is available')
            self.torch = torch
            torch.set_num_threads(self.workers)
        elif self.workers > 1:
            self.pool = ProcessPoolExecutor(self.workers,
                mp_context=multiprocessing.get_context('spawn'))

    def infer(self, items):
        if not items:
            return []
        if self.torch:
            t = self.torch
            with t.inference_mode():
                w = t.tensor([p[0] for p in items], device=self.device)
                x = t.tensor([p[1] for p in items], device=self.device)
                h = t.tanh(t.bmm(w[:, :INPUTS * HIDDEN].reshape(-1, HIDDEN, INPUTS), x.unsqueeze(2)).squeeze(2))
                p = t.softmax(t.bmm(w[:, INPUTS * HIDDEN:].reshape(-1, ACTIONS, HIDDEN), h.unsqueeze(2)).squeeze(2), dim=1)
                return list(zip(h.cpu().tolist(), p.cpu().tolist()))
        # Tiny batches cost more to serialize than calculate locally.
        if self.pool and len(items) >= self.workers * 8:
            return list(self.pool.map(forward, items, chunksize=max(8, len(items) // (self.workers * 2))))
        return [forward(item) for item in items]

    def close(self):
        if self.pool:
            self.pool.shutdown()
