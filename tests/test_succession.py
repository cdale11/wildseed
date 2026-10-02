import json
from pathlib import Path
import tempfile
import unittest

from wildseed import plants
from wildseed.geography import BIOME_NAMES, classify, client_tiles, generate
from wildseed.world import World


class SuccessionTests(unittest.TestCase):
    def setUp(self):
        self.world = World(117, 16, 16, population=0)
        self.addCleanup(self.world.engine.close)

    def test_burn_scar_favors_pioneer_grass_over_trees(self):
        recovering = self.world.tiles[self.world.idx(5, 5)]
        recovering.update(e=.55, m=.7, temp=.6, f=.8, grass=.2, trees=.2,
                          grass_seed=.5, tree_seed=.5, grass_pop=40, tree_pop=20,
                          grass_temp=.6, tree_temp=.6, grass_moist=.7, tree_moist=.7,
                          nutrient=.5, scar=1.0)
        established = recovering.copy()
        established['scar'] = 0.0
        plants.advance(recovering, 0)
        plants.advance(established, 0)
        self.assertGreater(recovering['grass'], established['grass'])
        self.assertLess(recovering['trees'], established['trees'])

    def test_fire_marks_land_then_recovery_changes_biome(self):
        tile = self.world.tiles[self.world.idx(5, 5)]
        tile.update(e=.55, m=.5, temp=.55, grass=.1, trees=.05, scar=0, fire=0)
        self.world.intervene('fire', 5, 5, radius=0)
        self.assertGreater(tile['scar'], .25)
        self.assertEqual(classify(tile), 'burnscar')
        tile['fire'] = 0
        tile['scar'] = .26
        self.world.tick = self.world.idx(5, 5) % 4
        self.world.climate()
        self.assertLess(tile['scar'], .25)
        self.assertNotEqual(classify(tile), 'burnscar')
        self.world.intervene('forest', 5, 5, radius=0)
        self.assertEqual(classify(tile), 'woodland')
        self.world.intervene('ocean', 5, 5, radius=0)
        self.assertEqual(tile['scar'], 0)

    def test_active_lava_is_volcanic_before_it_becomes_a_burn_scar(self):
        tile = self.world.tiles[self.world.idx(5, 5)]
        tile.update(e=.65, m=.3, temp=.55, grass=0, trees=0, scar=1, lava=.5)
        self.assertEqual(classify(tile), 'volcanic')
        tile['lava'] = 0
        self.assertEqual(classify(tile), 'burnscar')

    def test_burned_woodland_recovers_through_grassland(self):
        world = World(42, 16, 16, population=0, biome='woodland')
        self.addCleanup(world.engine.close)
        tile = world.tiles[world.idx(8, 8)]
        tile.update(e=.55, m=.75, temp=.58, f=.8, grass=.03, trees=.02,
                    grass_seed=.7, tree_seed=.85, grass_pop=4, tree_pop=2,
                    nutrient=.7, litter=.25, scar=1, fire=0, lava=0, lake=0, lake_cap=0)
        stages = {}
        for tick in range(1, 5001):
            world.step()
            if tick in (1, 300, 5000):
                stages[tick] = classify(tile)
        self.assertEqual(stages, {1: 'burnscar', 300: 'grassland', 5000: 'woodland'})

    def test_new_biome_previews_match_active_world_and_save_migrates(self):
        for biome in ('grassland', 'woodland', 'burnscar'):
            with self.subTest(biome=biome):
                tiles = generate(117, 16, 16, biome=biome)
                world = World(117, 16, 16, population=0, biome=biome)
                self.addCleanup(world.engine.close)
                self.assertEqual(client_tiles(tiles), world.snapshot()['tiles'])
                self.assertTrue(any(BIOME_NAMES[row[8]] == biome
                                    for row in world.snapshot()['tiles'] if row[0] > .37))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'old.json'
            self.world.save(path)
            data = json.loads(path.read_text())
            data['version'] = 15
            for tile in data['tiles']:
                del tile['scar']
            path.write_text(json.dumps(data))
            a = World.load(path)
            b = World.load(path)
            self.addCleanup(a.engine.close)
            self.addCleanup(b.engine.close)
            self.assertTrue(all(tile['scar'] == 0 for tile in a.tiles))
            for _ in range(8):
                a.step()
                b.step()
            self.assertEqual(a.snapshot(), b.snapshot())


if __name__ == '__main__':
    unittest.main()
