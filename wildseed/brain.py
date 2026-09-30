"""Small inherited neural policy, trained online with a reward baseline.

Workers perform independent inference; the authoritative process owns training
and RNG. Optional accelerator inference uses batches of individual policies.
"""
import math
import multiprocessing
import os
from concurrent.futures import ProcessPoolExecutor

INPUTS, HIDDEN, ACTIONS = 12, 8, 7
PARAMS = INPUTS * HIDDEN + HIDDEN * ACTIONS


def forward(item):
    weights, obs = item
    hidden = [math.tanh(sum(weights[j * INPUTS + i] * obs[i]
                                 for i in range(INPUTS))) for j in range(HIDDEN)]
    base = INPUTS * HIDDEN
    logits = [sum(weights[base + k * HIDDEN + j] * hidden[j]
                  for j in range(HIDDEN)) for k in range(ACTIONS)]
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
    back = [sum(weights[base + k * HIDDEN + j] * delta[k]
                for k in range(ACTIONS)) * (1 - hidden[j] ** 2)
            for j in range(HIDDEN)]
    for k in range(ACTIONS):
        for j in range(HIDDEN):
            ix = base + k * HIDDEN + j
            weights[ix] = max(-4, min(4, weights[ix] + rate * delta[k] * hidden[j]))
    for j in range(HIDDEN):
        for i in range(INPUTS):
            ix = j * INPUTS + i
            weights[ix] = max(-4, min(4, weights[ix] + rate * back[j] * obs[i]))


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
