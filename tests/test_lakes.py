import json
from pathlib import Path
import tempfile
import unittest

from wildseed import watershed
from wildseed.world import World


class LakeTests(unittest.TestCase):
    def setUp(self):
        self.world = World(507, 16, 16, population=0)
        self.addCleanup(self.world.engine.close)

    def bowl(self):
        for tile in self.world.tiles:
            tile.update(e=.6, m=.7, water=0.0, lake=0.0, lake_cap=0.0)
        self.world.tiles[self.world.idx(0, 0)]['e'] = .2
        center = self.world.tiles[self.world.idx(8, 8)]
        center['e'] = .4
        watershed.advance(self.world)
        return center

    def test_closed_basin_stores_water_then_drains_after_spill(self):
        center = self.bowl()
        self.assertGreater(center['lake_cap'], .1)
        center['water'] = .08
        self.world.flow(self.world.idx(8, 8), 8, 8)
        self.assertGreater(center['lake'], .07)
        self.assertLess(center['water'], .001)
        self.assertGreater(center['e'] + center['lake'], center['e'])
        self.assertEqual(self.world.snapshot()['tiles'][self.world.idx(8, 8)][18],
                         round(center['lake'], 3))

    def test_lake_power_blocks_life_and_ocean_clears_storage(self):
        self.world.tiles[self.world.idx(8, 8)].update(e=.55, lake=0, lake_cap=0)
        result = self.world.intervene('lake', 8, 8, radius=0)
        self.assertEqual(result['tiles_changed'], 1)
        self.assertIsNone(self.world.spawn('human', 8, 8))
        self.assertGreater(self.world.tiles[self.world.idx(8, 8)]['lake'], 0)
        self.world.intervene('ocean', 8, 8, radius=0)
        tile = self.world.tiles[self.world.idx(8, 8)]
        self.assertEqual((tile['lake'], tile['lake_cap']), (0, 0))

    def test_lake_brush_basin_survives_drainage_refresh(self):
        for tile in self.world.tiles:
            tile.update(e=.5, lake=0, lake_cap=0)
        self.world.tiles[self.world.idx(0, 0)]['e'] = .2
        result = self.world.intervene('lake', 8, 8, radius=3)
        self.assertGreater(result['tiles_changed'], 0)
        center = self.world.tiles[self.world.idx(8, 8)]
        for _ in range(64):
            self.world.step()
        self.assertGreaterEqual(center['lake'], .05)
        self.assertGreater(center['lake_cap'], .05)

    def test_lake_brush_persists_on_oceanless_world(self):
        for tile in self.world.tiles:
            tile.update(e=.5, lake=0, lake_cap=0)
        self.world.intervene('lake', 8, 8, radius=3)
        center = self.world.tiles[self.world.idx(8, 8)]
        for _ in range(64):
            self.world.step()
        self.assertGreater(center['lake'], .05)

    def test_volcano_replaces_lake_with_lava_immediately(self):
        tile = self.world.tiles[self.world.idx(8, 8)]
        tile.update(e=.55, lake=0, lake_cap=0)
        self.world.intervene('lake', 8, 8, radius=0)
        self.world.intervene('volcano', 8, 8, radius=0)
        self.assertEqual((tile['lake'], tile['lake_cap']), (0, 0))
        self.assertGreater(tile['lava'], 0)

    def test_v19_migration_and_exact_continuation(self):
        self.bowl()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'lake.json'
            self.world.save(path)
            restored = World.load(path)
            self.addCleanup(restored.engine.close)
            for _ in range(40):
                self.world.step()
                restored.step()
            self.assertEqual(self.world.snapshot(), restored.snapshot())

            data = json.loads(path.read_text())
            data['version'] = 19
            for tile in data['tiles']:
                del tile['lake']
                del tile['lake_cap']
            path.write_text(json.dumps(data))
            migrated = World.load(path)
            self.addCleanup(migrated.engine.close)
            self.assertTrue(all(t['lake'] == t['lake_cap'] == 0 for t in migrated.tiles))

    def test_local_runoff_transfers_water_and_nutrients_without_clipping_loss(self):
        for tile in self.world.tiles:
            tile.update(e=.9, m=.48, water=.99, lake=0, lake_cap=0,
                        sediment=0, nutrient=0, temp=.5)
        source = self.world.tiles[self.world.idx(8, 8)]
        target = self.world.tiles[self.world.idx(9, 8)]
        source.update(e=.86, water=.6, nutrient=.4)
        target.update(e=.4, water=.99, nutrient=.9999)
        initial_water = source['water'] + target['water']
        initial_nutrient = source['nutrient'] + target['nutrient']
        self.world.flow(self.world.idx(8, 8), 8, 8)
        self.assertAlmostEqual(source['water'] + target['water'], initial_water - .0007)
        self.assertAlmostEqual(source['nutrient'] + target['nutrient'], initial_nutrient)
        self.assertLessEqual(target['water'], 1)
        self.assertLessEqual(target['nutrient'], 1)

    def test_runoff_moves_soil_moisture_into_surface_storage(self):
        for tile in self.world.tiles:
            tile.update(e=.9, m=.48, water=0, lake=0, lake_cap=0,
                        sediment=0, nutrient=0, temp=.5)
        tile = self.world.tiles[self.world.idx(8, 8)]
        tile.update(e=.6, m=1.0)
        before = tile['m'] + tile['water'] + tile['lake']
        self.world.flow(self.world.idx(8, 8), 8, 8)
        self.assertAlmostEqual(tile['m'] + tile['water'] + tile['lake'], before - .0007)
        self.assertLess(tile['m'], 1.0)


if __name__ == '__main__':
    unittest.main()
