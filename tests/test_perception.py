import json
import tempfile
from pathlib import Path
import unittest
from wildseed.world import World
from wildseed.brain import PARAMS

class PerceptionTests(unittest.TestCase):
    def setUp(self):
        self.w = World(width=16, height=16, population=0)
        self.addCleanup(self.w.engine.close)
        for t in self.w.tiles:
            t.update(e=.5, grass=0, trees=0, ore=0, fire=0)

    def test_predator_sees_prey_across_world_boundary(self):
        predator = self.w.spawn('predator', 15, 8)
        self.w.spawn('grazer', 1, 8)
        obs = self.w.observe(predator)
        self.assertEqual(obs[9], .5)  # east, two steps across periodic seam
        self.assertEqual(obs[8], 0)
        self.w.tiles[self.w.idx(0, 8)]['e'] = .2
        self.assertEqual(self.w.observe(predator)[9], -1)

    def test_dead_prey_is_not_food(self):
        predator = self.w.spawn('predator', 8, 8)
        prey = self.w.spawn('grazer', 8, 8)
        self.assertEqual(self.w.observe(predator)[3], 1)
        prey.energy = 0
        self.assertEqual(self.w.observe(predator)[3], 0)

    def test_grazer_threat_and_human_material_sensors(self):
        grazer = self.w.spawn('grazer', 8, 8)
        human = self.w.spawn('human', 8, 8)
        self.w.spawn('predator', 8, 7)
        self.w.tiles[self.w.idx(9, 8)]['trees'] = .8
        self.assertEqual(self.w.observe(grazer)[12], 1)
        self.assertEqual(self.w.observe(human)[17], .8)
        self.assertEqual(self.w.observe(grazer)[17], 0)

    def test_v1_migration_preserves_old_connections(self):
        org = self.w.spawn('human', 8, 8)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'world.json'
            self.w.save(path)
            data = json.loads(path.read_text()); data['version'] = 1
            old = [i / 152 for i in range(152)]
            data['organisms'][0]['weights'] = old
            path.write_text(json.dumps(data))
            loaded = World.load(path); self.addCleanup(loaded.engine.close)
            weights = loaded.organisms[0].weights
            self.assertEqual(len(weights), PARAMS)
            for j in range(8):
                self.assertEqual(weights[j*20:j*20+12],old[j*12:j*12+12])
                self.assertEqual(weights[j*20+12:j*20+20],[0]*8)
            self.assertEqual(weights[160:],old[96:])
            loaded.step(); loaded.save(path)
            self.assertEqual(json.loads(path.read_text())['version'],3)
