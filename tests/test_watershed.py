import json
from pathlib import Path
import tempfile
import unittest

from wildseed import watershed
from wildseed.world import World


class WatershedTests(unittest.TestCase):
    def setUp(self):
        self.world = World(93, 16, 16, population=0)
        self.addCleanup(self.world.engine.close)

    def valley(self):
        for tile in self.world.tiles:
            tile.update(e=.9, m=.9, water=0, river=0, sediment=0)
        self.world.tiles[self.world.idx(0, 8)]['e'] = .2
        for x in range(1, 15):
            self.world.tiles[self.world.idx(x, 8)]['e'] = .4 + x * .01
        self.world.clouds = [.9] * len(self.world.clouds)

    def test_valley_routes_catchment_to_ocean_and_carves(self):
        self.valley()
        parents, _ = watershed.drainage(self.world.tiles, 16, 16)
        self.assertEqual(parents[self.world.idx(10, 8)], self.world.idx(9, 8))
        mouth = self.world.tiles[self.world.idx(1, 8)]
        before = mouth['e']
        watershed.advance(self.world)
        self.assertGreater(mouth['river'], 0)
        self.assertGreater(mouth['water'], 0)
        self.assertLess(mouth['e'], before)
        self.assertGreater(mouth['sediment'], 0)
        self.assertEqual(self.world.tiles[self.world.idx(0, 8)]['river'], 0)

    def test_no_ocean_has_no_false_river(self):
        for tile in self.world.tiles:
            tile.update(e=.6, m=.9, river=0)
        watershed.advance(self.world)
        self.assertTrue(all(tile['river'] == 0 for tile in self.world.tiles))

    def test_channel_responds_to_drought_and_ocean_power(self):
        self.valley()
        mouth = self.world.tiles[self.world.idx(1, 8)]
        watershed.advance(self.world)
        wet = mouth['river']
        self.assertGreater(wet, 0)
        for tile in self.world.tiles:
            tile['m'] = .25
            tile['water'] = 0
        watershed.advance(self.world)
        self.assertLess(mouth['river'], wet)
        self.world.intervene('ocean', 1, 8, radius=1)
        self.assertEqual(mouth['river'], 0)

    def test_v13_save_migrates_and_replays(self):
        self.valley()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'old.json'
            self.world.save(path)
            data = json.loads(path.read_text())
            data['version'] = 13
            for tile in data['tiles']:
                del tile['river']
            path.write_text(json.dumps(data))
            a = World.load(path)
            b = World.load(path)
            self.addCleanup(a.engine.close)
            self.addCleanup(b.engine.close)
            self.assertTrue(all(tile['river'] == 0 for tile in a.tiles))
            for _ in range(32):
                a.step()
                b.step()
            self.assertEqual(a.snapshot(), b.snapshot())
            a.save(path)
            self.assertEqual(json.loads(path.read_text())['version'], World.VERSION)


if __name__ == '__main__':
    unittest.main()
