import json
from pathlib import Path
import tempfile
import unittest

from wildseed import weather
from wildseed.world import World


class WeatherTests(unittest.TestCase):
    def setUp(self):
        self.world = World(83, 16, 16, population=0)
        self.addCleanup(self.world.engine.close)

    def test_cloud_front_advects_across_periodic_boundary(self):
        for tile in self.world.tiles:
            tile.update(e=.5, m=0, temp=0, water=0)
        self.world.clouds = [0, .4, 0, 0]
        self.world.tick = 8
        weather.advance(self.world)
        self.assertAlmostEqual(self.world.clouds[0], .112)
        self.assertAlmostEqual(self.world.clouds[1], .288)
        self.assertEqual(self.world.clouds[2:], [0, 0])

    def test_uplands_receive_more_rain_from_same_front(self):
        for y in range(16):
            for x in range(16):
                self.world.tiles[self.world.idx(x, y)].update(
                    e=.8 if x < 8 else .5, m=.2, temp=.6, water=0)
        self.world.clouds = [.9] * 4
        self.world.tick = 8
        weather.advance(self.world)
        high = self.world.tiles[self.world.idx(2, 2)]
        low = self.world.tiles[self.world.idx(10, 2)]
        self.assertGreater(high['water'], low['water'])
        self.assertGreater(high['m'], low['m'])
        self.assertTrue(all(0 <= cloud <= 1 for cloud in self.world.clouds))

    def test_world_tick_applies_weather_before_local_climate(self):
        for tile in self.world.tiles:
            tile.update(e=.7, m=.2, temp=.6, water=0)
        self.world.clouds = [.9] * 4
        self.world.tick = 7
        target = self.world.tiles[self.world.idx(1, 1)]
        self.world.step()
        self.assertEqual(self.world.tick, 8)
        self.assertGreater(target['m'], .2)
        self.assertLess(max(self.world.clouds), .9)

    def test_v12_migration_and_exact_continuation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'old.json'
            self.world.save(path)
            data = json.loads(path.read_text())
            data['version'] = 12
            del data['clouds']
            path.write_text(json.dumps(data))
            a = World.load(path)
            b = World.load(path)
            self.addCleanup(a.engine.close)
            self.addCleanup(b.engine.close)
            self.assertEqual(a.clouds, self.world.clouds)
            for _ in range(16):
                a.step()
                b.step()
            self.assertEqual(a.snapshot(), b.snapshot())
            a.save(path)
            self.assertEqual(json.loads(path.read_text())['version'], 14)


if __name__ == '__main__':
    unittest.main()
