import json
from pathlib import Path
import tempfile
import unittest

from wildseed.world import World


class DiseaseTests(unittest.TestCase):
    def setUp(self):
        self.world = World(1301, 16, 16, population=0)
        self.addCleanup(self.world.engine.close)
        for tile in self.world.tiles:
            tile.update(e=.55, lake=0, fire=0)

    def test_plague_power_spreads_by_contact_and_heal_cures(self):
        sick = self.world.spawn('grazer', 8, 8)
        susceptible = self.world.spawn('grazer', 8, 8)
        susceptible.immunity = 0
        result = self.world.intervene('plague', 8, 8, radius=0)
        self.assertEqual(result['organisms_changed'], 2)
        self.assertEqual(self.world.infections, 2)
        sick.infection = .7
        self.world.intervene('plague', 8, 8, radius=0)
        self.assertEqual(self.world.infections, 2)
        self.world.intervene('heal', 8, 8, radius=0)
        self.assertEqual((sick.infection, susceptible.infection), (0, 0))

        sick.infection = 1
        self.world.engine.infer = lambda items: [([0.0] * 8, [0, 0, 0, 0, 0, 0, 1]) for _ in items]
        self.world.rng.random = lambda: 0.0
        self.world.step()
        self.assertGreater(susceptible.infection, 0)
        self.assertGreater(self.world.snapshot()['stats']['infected'], 1)

    def test_full_immunity_blocks_contact_and_recovery_raises_resistance(self):
        sick = self.world.spawn('grazer', 8, 8)
        resistant = self.world.spawn('grazer', 8, 8)
        sick.infection = .01
        resistant.immunity = 1
        self.world.engine.infer = lambda items: [([0.0] * 8, [0, 0, 0, 0, 0, 0, 1]) for _ in items]
        self.world.rng.random = lambda: 0.0
        original = sick.immunity
        for _ in range(3):
            self.world.step()
        self.assertEqual(sick.infection, 0)
        self.assertGreater(sick.immunity, original)
        self.assertEqual(resistant.infection, 0)

    def test_disease_state_replays_and_v26_migrates(self):
        organism = self.world.spawn('human', 8, 8)
        organism.infection = .8
        organism.immunity = .4
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'disease.json'
            self.world.save(path)
            restored = World.load(path)
            self.addCleanup(restored.engine.close)
            for _ in range(24):
                self.world.step()
                restored.step()
            self.assertEqual(self.world.snapshot(), restored.snapshot())

            payload = json.loads(path.read_text())
            payload['version'] = 26
            del payload['infections']
            del payload['organisms'][0]['infection']
            del payload['organisms'][0]['immunity']
            path.write_text(json.dumps(payload))
            migrated = World.load(path)
            self.addCleanup(migrated.engine.close)
            self.assertEqual(migrated.infections, 0)
            self.assertEqual((migrated.organisms[0].infection,
                              migrated.organisms[0].immunity), (0.0, .2))


if __name__ == '__main__':
    unittest.main()
