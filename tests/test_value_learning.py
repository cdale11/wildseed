import json
from pathlib import Path
import tempfile
import unittest

from wildseed.brain import ACTIONS, DISCOUNT, HIDDEN, INPUTS, VALUE_PARAMS, forward, learn_value, predict_value
from wildseed.world import World


class ValueLearningTests(unittest.TestCase):
    def test_value_head_learns_bounded_positive_and_negative_outcomes(self):
        weights = [0.0] * VALUE_PARAMS
        hidden = [.5] * HIDDEN
        for _ in range(40):
            learn_value(weights, hidden, 1.0)
        positive = predict_value(weights, hidden)
        self.assertGreater(positive, .5)
        for _ in range(80):
            learn_value(weights, hidden, -1.0)
        self.assertLess(predict_value(weights, hidden), positive)
        self.assertTrue(all(-4 <= weight <= 4 for weight in weights))

    def test_future_value_changes_previous_action_probability(self):
        world = World(223, 16, 16, population=0)
        self.addCleanup(world.engine.close)
        organism = world.spawn('grazer', 8, 8)
        obs = world.observe(organism)
        hidden, probabilities = forward((organism.weights, obs))
        organism.pending_credit = [obs, hidden, probabilities, 4, 0.0, 0.0]
        world.finish_credit(organism, 1.0)
        self.assertGreater(forward((organism.weights, obs))[1][4], probabilities[4])
        self.assertEqual(organism.value_updates, 1)
        self.assertEqual(world.critic_updates, 1)
        self.assertIsNone(organism.pending_credit)

        old = forward((organism.weights, obs))[1][4]
        organism.pending_credit = [obs, hidden, probabilities, 4, 1.0, 0.0]
        world.finish_credit(organism, 0.0)
        self.assertLess(forward((organism.weights, obs))[1][4], old)

    def test_learned_successor_value_bootstraps_previous_action(self):
        world = World(223, 16, 16, population=0)
        self.addCleanup(world.engine.close)
        world.tiles[world.idx(8, 8)]['e'] = .55
        organism = world.spawn('grazer', 8, 8)
        obs = world.observe(organism)
        hidden, probabilities = forward((organism.weights, obs))
        successor_hidden = [-value for value in hidden]
        for _ in range(80):
            learn_value(organism.value_weights, successor_hidden,
                        1.0 - predict_value(organism.value_weights, successor_hidden))
        previous_value = predict_value(organism.value_weights, hidden)
        successor_value = predict_value(organism.value_weights, successor_hidden)
        self.assertGreater(DISCOUNT * successor_value - previous_value, .2)
        organism.pending_credit = [obs, hidden, probabilities, 4, previous_value, 0.0]
        world.finish_credit(organism, successor_value)
        self.assertGreater(forward((organism.weights, obs))[1][4], probabilities[4])

    def test_save_continues_pending_credit_and_v16_defaults_are_neutral(self):
        world = World(224, 16, 16, population=1)
        self.addCleanup(world.engine.close)
        world.step()
        self.assertIsNotNone(world.organisms[0].pending_credit)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'value.json'
            world.save(path)
            restored = World.load(path)
            self.addCleanup(restored.engine.close)
            for _ in range(8):
                world.step()
                restored.step()
            self.assertEqual(world.snapshot(), restored.snapshot())
            self.assertEqual(world.organisms[0].weights, restored.organisms[0].weights)
            self.assertEqual(world.organisms[0].value_weights, restored.organisms[0].value_weights)
            self.assertGreater(world.critic_updates, 0)

            data = json.loads(path.read_text())
            data['version'] = 16
            del data['critic_updates']
            for organism in data['organisms']:
                del organism['value_weights']
                del organism['pending_credit']
                del organism['value_updates']
            path.write_text(json.dumps(data))
            migrated = World.load(path)
            self.addCleanup(migrated.engine.close)
            self.assertEqual(migrated.critic_updates, 0)
            self.assertEqual(migrated.organisms[0].value_weights, [0.0] * VALUE_PARAMS)
            self.assertIsNone(migrated.organisms[0].pending_credit)

    def test_frozen_world_never_trains_value_head(self):
        world = World(225, 16, 16, population=8, learning=False)
        self.addCleanup(world.engine.close)
        for _ in range(12):
            world.step()
        self.assertEqual(world.critic_updates, 0)
        self.assertTrue(all(o.value_weights == [0.0] * VALUE_PARAMS and
                            o.pending_credit is None for o in world.organisms))

    def test_terminal_death_flushes_credit_and_children_inherit_value_head(self):
        world = World(226, 16, 16, population=0)
        self.addCleanup(world.engine.close)
        parent = world.spawn('grazer', 8, 8)
        parent.value_weights = [.5] * VALUE_PARAMS
        child = world.spawn('grazer', 8, 8, parent=parent)
        self.assertEqual(len(child.value_weights), VALUE_PARAMS)
        self.assertNotEqual(child.value_weights, parent.value_weights)
        self.assertIsNone(child.pending_credit)
        world.organisms.remove(child)
        parent.energy = 1
        for tile in world.tiles:
            tile.update(e=.55, fire=1)
        world.engine.infer = lambda items: [([0.0] * HIDDEN, [0, 0, 0, 0, 0, 0, 1]) for _ in items]
        world.step()
        self.assertNotIn(parent, world.organisms)
        self.assertEqual(parent.value_updates, 1)
        self.assertIsNone(parent.pending_credit)

    def test_mutation_power_changes_value_head_and_clears_stale_credit(self):
        world = World(227, 16, 16, population=0)
        self.addCleanup(world.engine.close)
        world.tiles[world.idx(8, 8)]['e'] = .55
        organism = world.spawn('grazer', 8, 8)
        before = organism.value_weights.copy()
        organism.pending_credit = [[0.0] * INPUTS, [0.0] * HIDDEN,
                                   [1 / ACTIONS] * ACTIONS, 4, 0.0, 1.0]
        organism.last_move = [[0.0] * INPUTS, [0.0] * HIDDEN,
                              [1 / ACTIONS] * ACTIONS, 0]
        result = world.intervene('mutate', 8, 8, radius=0)
        self.assertEqual(result['organisms_changed'], 1)
        self.assertNotEqual(organism.value_weights, before)
        self.assertIsNone(organism.pending_credit)
        self.assertIsNone(organism.last_move)


if __name__ == '__main__':
    unittest.main()
