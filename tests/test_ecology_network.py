import json
from pathlib import Path
import tempfile
import unittest

from wildseed.world import World


class EcologyNetworkTests(unittest.TestCase):
    def setUp(self):
        self.world = World(1501, 16, 16, population=0)
        self.addCleanup(self.world.engine.close)
        for tile in self.world.tiles:
            tile.update(e=.55, lake=0, fire=0, grass=.8)

    def test_observed_feeding_hunting_and_disease_form_distinct_edges(self):
        self.world.spawn('grazer', 8, 8)
        self.world.spawn('predator', 8, 8)
        self.world.spawn('human', 8, 8)
        self.world.engine.infer = lambda items: [([0.0] * 8, [0, 0, 0, 0, 1, 0, 0]) for _ in items]
        self.world.step()
        self.assertEqual(self.world.ecology_events['grass>grazer'], 1)
        self.assertEqual(self.world.ecology_events['grazer>predator'], 1)
        self.assertEqual(self.world.ecology_events['grass>human'], 1)
        self.world.intervene('plague', 8, 8, radius=0)
        self.assertGreater(self.world.ecology_events['pathogen>human'], 0)
        edges = {(edge['from'], edge['to']) for edge in self.world.snapshot()['ecology_network']}
        self.assertIn(('grazer', 'predator'), edges)
        self.assertEqual(self.world.snapshot()['stats']['ecology_links'], len(edges))

    def test_seed_transport_creates_reciprocal_forager_plant_link(self):
        grazer = self.world.spawn('grazer', 8, 8)
        grazer.seed_cargo = [.02, .5, .6, 0, 0, 0]
        self.world.engine.infer = lambda items: [([0.0] * 8, [1, 0, 0, 0, 0, 0, 0]) for _ in items]
        self.world.step()
        self.assertEqual(self.world.ecology_events['grazer>plants'], 1)

    def test_network_replays_and_v28_starts_empty(self):
        self.world.record_interaction('trees', 'human')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'network.json'
            self.world.save(path)
            restored = World.load(path)
            self.addCleanup(restored.engine.close)
            for _ in range(24):
                self.world.step()
                restored.step()
            self.assertEqual(self.world.snapshot(), restored.snapshot())

            payload = json.loads(path.read_text())
            payload['version'] = 28
            del payload['ecology_events']
            path.write_text(json.dumps(payload))
            migrated = World.load(path)
            self.addCleanup(migrated.engine.close)
            self.assertEqual(migrated.ecology_events, {})


if __name__ == '__main__':
    unittest.main()
