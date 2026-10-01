import json
from pathlib import Path
import tempfile
import unittest

from wildseed.world import World


class HydrologyTests(unittest.TestCase):
    def setUp(self):
        self.world = World(9, 16, 16, population=0)
        self.addCleanup(self.world.engine.close)
        for tile in self.world.tiles:
            tile.update(e=.8, m=.4, temp=.6, water=0, sediment=0, lava=0, fire=0)
        self.source = self.world.tiles[self.world.idx(8, 8)]
        self.downhill = self.world.tiles[self.world.idx(9, 8)]
        self.downhill['e'] = .45

    def test_runoff_moves_water_and_soil_downhill(self):
        self.source['water'] = .2
        before = self.source['e'] + self.downhill['e'] + self.source['sediment'] + self.downhill['sediment']
        self.world.flow(self.world.idx(8, 8), 8, 8)
        self.assertGreater(self.downhill['water'], 0)
        self.assertGreater(self.downhill['sediment'], 0)
        self.assertLess(self.source['e'], .8)
        after = self.source['e'] + self.downhill['e'] + self.source['sediment'] + self.downhill['sediment']
        self.assertAlmostEqual(before, after, places=12)

    def test_lava_flows_burns_and_cools_into_rock(self):
        self.source['lava'] = .8
        self.world.flow(self.world.idx(8, 8), 8, 8)
        self.assertGreater(self.downhill['lava'], 0)
        self.assertGreater(self.source['e'], .8)
        self.assertGreater(self.source['fire'], 0)

    def test_rain_and_volcano_powers_feed_dynamic_fields(self):
        self.source['e'] = .55
        self.world.intervene('rain', 8, 8, 1)
        self.assertGreater(self.source['water'], 0)
        self.world.intervene('volcano', 8, 8, 1)
        self.assertGreater(self.source['lava'], 0)

    def test_version_five_save_migrates_flow_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'old.json'
            self.world.save(path)
            data = json.loads(path.read_text())
            data['version'] = 5
            for tile in data['tiles']:
                for key in ('water', 'sediment', 'lava', 'grass_pop', 'tree_pop',
                            'grass_temp', 'grass_moist', 'tree_temp', 'tree_moist'):
                    del tile[key]
            path.write_text(json.dumps(data))
            loaded = World.load(path)
            self.addCleanup(loaded.engine.close)
            self.assertTrue(all(t['water'] == t['sediment'] == t['lava'] == 0 for t in loaded.tiles))
            self.assertTrue(all(t['grass_pop'] == int(t['grass'] * 100) for t in loaded.tiles))
            loaded.step()
            loaded.save(path)
            self.assertEqual(json.loads(path.read_text())['version'], 9)
