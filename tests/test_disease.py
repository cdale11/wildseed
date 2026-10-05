import json
from pathlib import Path
import tempfile
import unittest

from wildseed.world import World
from wildseed import disease, society


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

    def test_damp_litter_can_seed_an_unforced_outbreak(self):
        tile = self.world.tiles[self.world.idx(8, 8)]
        tile.update(m=1.0, litter=1.0)
        organism = self.world.spawn('grazer', 8, 8)
        self.world.tick = 20
        self.world.rng.random = lambda: 0.0
        disease.advance(self.world, {self.world.idx(8, 8): [organism]})
        self.assertGreater(organism.infection, 0)
        self.assertEqual(self.world.spillovers, 1)
        self.assertEqual(self.world.ecology_events['environmental_pathogen>grazer'], 1)

    def test_quarantine_reduces_contact_risk_and_pauses_trade(self):
        town = {'id': 1, 'x': 8, 'y': 8, 'culture': 1, 'houses': 2, 'stock': 40.0,
                'wood': 0.0, 'ore': 0.0, 'population': 0, 'age': 0, 'empty_ticks': 0}
        other = {'id': 2, 'x': 10, 'y': 8, 'culture': 2, 'houses': 2, 'stock': 0.0,
                 'wood': 0.0, 'ore': 2.0, 'population': 0, 'age': 0, 'empty_ticks': 0}
        self.world.settlements = [town, other]
        organisms = [self.world.spawn('human', 8, 8) for _ in range(3)]
        organisms[0].infection = organisms[1].infection = 1.0
        organisms[2].immunity = 0
        self.world.tick = 20
        society.update(self.world)
        self.assertGreater(town['quarantine_until'], self.world.tick)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'quarantine.json'
            self.world.save(path)
            restored = World.load(path)
            self.addCleanup(restored.engine.close)
            self.assertEqual(restored.settlements[0]['quarantine_until'],
                             town['quarantine_until'])
        society.dispatch_trade(self.world)
        self.assertEqual(self.world.shipments, [])
        self.world.rng.random = lambda: .08
        disease.advance(self.world, {self.world.idx(8, 8): organisms})
        self.assertEqual(organisms[2].infection, 0)
        town['quarantine_until'] = 0
        disease.advance(self.world, {self.world.idx(8, 8): organisms})
        self.assertGreater(organisms[2].infection, 0)

    def test_v30_migrates_spillover_and_quarantine_state(self):
        human = self.world.spawn('human', 8, 8)
        human.wood = 2.5
        society.work(self.world, human, self.world.tiles[self.world.idx(8, 8)])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'v30.json'
            self.world.save(path)
            payload = json.loads(path.read_text())
            payload['version'] = 30
            del payload['spillovers']
            del payload['settlements'][0]['quarantine_until']
            path.write_text(json.dumps(payload))
            restored = World.load(path)
            self.addCleanup(restored.engine.close)
            self.assertEqual(restored.spillovers, 0)
            self.assertEqual(restored.settlements[0].get('quarantine_until', 0), 0)


if __name__ == '__main__':
    unittest.main()
