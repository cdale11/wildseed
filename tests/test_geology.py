import json
from pathlib import Path
import tempfile
import unittest

from wildseed import geology, society
from wildseed.world import World


class GeologyTests(unittest.TestCase):
    def test_weathering_moves_finite_ore_into_mineable_stock(self):
        world = World(1001, 16, 16, population=0)
        self.addCleanup(world.engine.close)
        tile = world.tiles[world.idx(8, 8)]
        tile.update(e=.65, lake=0, m=.8, temp=.5, ore=0, ore_vein=1)
        before = tile['ore'] + tile['ore_vein']
        for _ in range(80):
            released = geology.weather(tile)
            self.assertGreater(released, 0)
        self.assertAlmostEqual(tile['ore'] + tile['ore_vein'], before)
        self.assertGreater(tile['ore'], 0)
        for _ in range(4):
            world.step()
        self.assertGreater(world.ore_exposed, 0)
        self.assertGreater(world.snapshot()['tiles'][world.idx(8, 8)][19], 0)

        human = world.spawn('human', 8, 8)
        human.occupation = 'miner'
        world.settlements.append({'id': 1, 'x': 8, 'y': 8, 'culture': human.culture,
                                  'houses': 1, 'stock': 3, 'wood': 0, 'ore': 0,
                                  'population': 1, 'age': 0, 'empty_ticks': 0})
        surface_before = tile['ore']
        society.work(world, human, tile)
        self.assertLess(tile['ore'], surface_before)
        self.assertGreater(world.settlements[0]['ore'], 0)

    def test_exposure_respects_surface_capacity_and_save_migration(self):
        world = World(1002, 16, 16, population=0)
        self.addCleanup(world.engine.close)
        tile = world.tiles[world.idx(8, 8)]
        tile.update(e=.7, lake=0, ore=19.99, ore_vein=.5)
        self.assertAlmostEqual(geology.expose(tile, .2), .01)
        self.assertAlmostEqual(tile['ore'] + tile['ore_vein'], 20.49)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'ore.json'
            world.save(path)
            restored = World.load(path)
            self.addCleanup(restored.engine.close)
            for _ in range(32):
                world.step()
                restored.step()
            self.assertEqual(world.snapshot(), restored.snapshot())

            payload = json.loads(path.read_text())
            payload['version'] = 22
            del payload['ore_exposed']
            for older_tile in payload['tiles']:
                del older_tile['ore_vein']
            path.write_text(json.dumps(payload))
            migrated = World.load(path)
            self.addCleanup(migrated.engine.close)
            self.assertEqual(migrated.ore_exposed, 0)
            self.assertTrue(all(t['ore_vein'] == 0 for t in migrated.tiles))


if __name__ == '__main__':
    unittest.main()
