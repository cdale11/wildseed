import json
from pathlib import Path
import tempfile
import unittest

from wildseed.brain import ACTIONS, HIDDEN, INPUTS, PARAMS, forward
from wildseed.world import World


class MemoryTests(unittest.TestCase):
    def test_recurrent_input_changes_policy_probabilities(self):
        weights = [0.0] * PARAMS
        weights[20] = 1.0
        weights[INPUTS * HIDDEN + 4 * HIDDEN] = 1.0
        blank = [0.0] * INPUTS
        remembered = blank.copy()
        remembered[20] = 1.0
        self.assertGreater(forward((weights, remembered))[1][4],
                           forward((weights, blank))[1][4])

    def test_world_persists_previous_hidden_state(self):
        world = World(41, 16, 16, population=1)
        self.addCleanup(world.engine.close)
        world.engine.infer = lambda items: [([.25] * HIDDEN, [0, 0, 0, 0, 0, 0, 1]) for _ in items]
        world.step()
        self.assertEqual(world.organisms[0].memory, [.25] * HIDDEN)
        self.assertEqual(world.observe(world.organisms[0])[-HIDDEN:], [.25] * HIDDEN)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'world.json'
            world.save(path)
            restored = World.load(path)
            self.addCleanup(restored.engine.close)
            self.assertEqual(restored.organisms[0].memory, [.25] * HIDDEN)

    def test_v9_migration_preserves_policy_and_pending_move(self):
        world = World(42, 16, 16, population=1)
        self.addCleanup(world.engine.close)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'old.json'
            world.save(path)
            data = json.loads(path.read_text())
            data['version'] = 9
            organism = data['organisms'][0]
            original = organism['weights']
            organism['weights'] = [value for j in range(HIDDEN)
                                   for value in original[j*INPUTS:j*INPUTS+20]] + original[INPUTS*HIDDEN:]
            organism['last_move'] = [[0.0]*20, [0.0]*HIDDEN, [1/ACTIONS]*ACTIONS, 0]
            del organism['memory']
            path.write_text(json.dumps(data))
            migrated = World.load(path)
            self.addCleanup(migrated.engine.close)
            restored = migrated.organisms[0]
            for j in range(HIDDEN):
                self.assertEqual(restored.weights[j*INPUTS:j*INPUTS+20],
                                 original[j*INPUTS:j*INPUTS+20])
                self.assertEqual(restored.weights[j*INPUTS+20:(j+1)*INPUTS], [0]*HIDDEN)
            self.assertEqual(restored.weights[INPUTS*HIDDEN:], original[INPUTS*HIDDEN:])
            self.assertEqual(len(restored.last_move[0]), INPUTS)
            self.assertEqual(restored.memory, [0]*HIDDEN)
