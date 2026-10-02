import json
from pathlib import Path
import tempfile
import unittest

from wildseed.experiment import run, threat_avoidance_probe
from wildseed.brain import forward, INPUTS, HIDDEN
from wildseed.world import World


class ExperimentTests(unittest.TestCase):
    def test_frozen_policy_survives_save_and_resume(self):
        world = World(11, 24, 20, population=12, learning=False)
        self.addCleanup(world.engine.close)
        original = {o.id: o.weights.copy() for o in world.organisms}
        for _ in range(15):
            world.step()
        self.assertEqual(world.training_steps, 0)
        for organism in world.organisms:
            if organism.id in original:
                self.assertEqual(organism.weights, original[organism.id])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'frozen.json'
            world.save(path)
            restored = World.load(path)
            self.addCleanup(restored.engine.close)
            self.assertFalse(restored.learning)
            for _ in range(10):
                world.step()
                restored.step()
            self.assertEqual(world.snapshot(), restored.snapshot())

    def test_paired_experiment_is_reproducible_and_learning_changes_weights(self):
        frozen_a = run(7, 25, 12, 24, 20, 60, False, 10)
        frozen_b = run(7, 25, 12, 24, 20, 60, False, 10)
        learned = run(7, 25, 12, 24, 20, 60, True, 10)
        self.assertEqual(frozen_a, frozen_b)
        self.assertEqual(frozen_a['samples'][-1]['training_steps'], 0)
        self.assertGreater(learned['samples'][-1]['training_steps'], 0)
        self.assertEqual(frozen_a['samples'][0], learned['samples'][0])

    def test_value_ablation_keeps_immediate_policy_learning_and_replays(self):
        ablated = run(7, 25, 12, 24, 20, 60, True, 10, value_learning=False)
        full = run(7, 25, 12, 24, 20, 60, True, 10, value_learning=True)
        self.assertEqual(ablated['samples'][0], full['samples'][0])
        self.assertGreater(ablated['samples'][-1]['training_steps'], 0)
        self.assertEqual(ablated['samples'][-1]['critic_updates'], 0)
        self.assertGreater(full['samples'][-1]['critic_updates'], 0)

        world = World(7, 24, 20, population=12, value_learning=False)
        self.addCleanup(world.engine.close)
        for _ in range(8):
            world.step()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'ablation.json'
            world.save(path)
            resumed = World.load(path)
            self.addCleanup(resumed.engine.close)
            self.assertFalse(resumed.value_learning)
            for _ in range(8):
                world.step()
                resumed.step()
            self.assertEqual(world.snapshot(), resumed.snapshot())

    def test_threat_probe_detects_avoidance_and_approach(self):
        world = World(8, 16, 16, population=0)
        self.addCleanup(world.engine.close)
        world.tiles[world.idx(8, 8)].update(e=.55, lake=0)
        grazer = world.spawn('grazer', 8, 8)
        grazer.weights = [0.0] * len(grazer.weights)
        for direction in range(4):
            grazer.weights[direction * INPUTS + 12 + direction] = 2.0
            grazer.weights[INPUTS * HIDDEN + direction * HIDDEN + direction] = -2.0
        self.assertGreater(threat_avoidance_probe(world), 0)
        for direction in range(4):
            grazer.weights[INPUTS * HIDDEN + direction * HIDDEN + direction] = 2.0
        self.assertLess(threat_avoidance_probe(world), 0)

    def test_v4_save_defaults_to_learning_and_zero_hunts(self):
        world = World(7, 24, 20, population=0)
        self.addCleanup(world.engine.close)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'v4.json'
            world.save(path)
            data = json.loads(path.read_text())
            data['version'] = 4
            del data['learning']
            del data['hunts']
            path.write_text(json.dumps(data))
            loaded = World.load(path)
            self.addCleanup(loaded.engine.close)
            self.assertTrue(loaded.learning)
            self.assertEqual(loaded.hunts, 0)

    def test_successful_hunt_credits_previous_move(self):
        world = World(17, 24, 20, population=0)
        self.addCleanup(world.engine.close)
        for tile in world.tiles:
            tile.update(e=.55, grass=0, fire=0)
        predator = world.spawn('predator', 8, 8)
        grazer = world.spawn('grazer', 8, 8)
        observation = world.observe(predator)
        hidden, probabilities = forward((predator.weights, observation))
        predator.last_move = [observation, hidden, probabilities, 0]
        before = predator.weights.copy()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'pending-hunt.json'
            world.save(path)
            restored = World.load(path)
            self.addCleanup(restored.engine.close)
            # Eat is deterministic; only credit for the previous move changes weights.
            eat = lambda items: [([0.0] * 8, [0, 0, 0, 0, 1, 0, 0]) for _ in items]
            world.engine.infer = restored.engine.infer = eat
            world.step()
            restored.step()
            self.assertEqual(world.snapshot(), restored.snapshot())
            self.assertEqual(world.organisms[0].weights, restored.organisms[0].weights)
        self.assertEqual(world.hunts, 1)
        self.assertEqual(world.hunt_move_updates, 1)
        self.assertNotEqual(predator.weights, before)
        self.assertNotIn(grazer, world.organisms)
