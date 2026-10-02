import math
import random
import unittest

from wildseed.brain import ACTIONS, HIDDEN, INPUTS, PARAMS, forward, learn


def reference_forward(weights, obs):
    hidden = [math.tanh(sum(weights[j * INPUTS + i] * obs[i]
                            for i in range(INPUTS))) for j in range(HIDDEN)]
    base = INPUTS * HIDDEN
    logits = [sum(weights[base + k * HIDDEN + j] * hidden[j]
                  for j in range(HIDDEN)) for k in range(ACTIONS)]
    peak = max(logits)
    exps = [math.exp(value - peak) for value in logits]
    return hidden, [value / sum(exps) for value in exps]


def reference_learn(weights, obs, hidden, probabilities, action, advantage, rate=.018):
    advantage = max(-2, min(2, advantage))
    delta = [((1 if k == action else 0) - probabilities[k]) * advantage
             for k in range(ACTIONS)]
    base = INPUTS * HIDDEN
    back = [sum(weights[base + k * HIDDEN + j] * delta[k]
                for k in range(ACTIONS)) * (1 - hidden[j] ** 2)
            for j in range(HIDDEN)]
    for k in range(ACTIONS):
        for j in range(HIDDEN):
            index = base + k * HIDDEN + j
            weights[index] = max(-4, min(4, weights[index] + rate * delta[k] * hidden[j]))
    for j in range(HIDDEN):
        for i in range(INPUTS):
            index = j * INPUTS + i
            weights[index] = max(-4, min(4, weights[index] + rate * back[j] * obs[i]))


class BrainEquivalenceTests(unittest.TestCase):
    def test_weight_bounds_match_reference_at_saturation(self):
        obs = [1.0] * INPUTS
        hidden = [.75] * HIDDEN
        probabilities = [1 / ACTIONS] * ACTIONS
        for initial, advantage in ((4.0, 2.0), (-4.0, -2.0)):
            with self.subTest(initial=initial):
                actual = [initial] * PARAMS
                expected = actual.copy()
                learn(actual, obs, hidden, probabilities, 4, advantage)
                reference_learn(expected, obs, hidden, probabilities, 4, advantage)
                for value, reference in zip(actual, expected):
                    self.assertAlmostEqual(value, reference, places=12)
                    self.assertTrue(-4 <= value <= 4)

    def test_sparse_and_dense_policy_updates_match_reference(self):
        rng = random.Random(72)
        for density in (0, .25, .75, 1):
            with self.subTest(density=density):
                obs = [rng.uniform(-1, 1) if rng.random() < density else 0
                       for _ in range(INPUTS)]
                weights = [rng.uniform(-.5, .5) for _ in range(PARAMS)]
                weights[0] = 3.999
                expected_hidden, expected_probs = reference_forward(weights, obs)
                hidden, probs = forward((weights, obs))
                for actual, expected in zip(hidden + probs, expected_hidden + expected_probs):
                    self.assertAlmostEqual(actual, expected, places=12)
                actual_weights = weights.copy()
                expected_weights = weights.copy()
                learn(actual_weights, obs, hidden, probs, 4, 2.5)
                reference_learn(expected_weights, obs, expected_hidden, expected_probs, 4, 2.5)
                for actual, expected in zip(actual_weights, expected_weights):
                    self.assertAlmostEqual(actual, expected, places=12)


if __name__ == '__main__':
    unittest.main()
