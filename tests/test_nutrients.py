import json
from pathlib import Path
import tempfile
import unittest

from wildseed import plants
from wildseed.world import World


class NutrientTests(unittest.TestCase):
    def setUp(self):
        self.world = World(71, 16, 16, population=0)
        self.addCleanup(self.world.engine.close)

    def test_nutrients_limit_growth_and_litter_recycles(self):
        rich = self.world.tiles[self.world.idx(7, 7)]
        rich.update(e=.55, m=.7, f=.8, temp=.6, grass=.2, trees=0,
                    grass_seed=.6, tree_seed=0, grass_pop=60, tree_pop=0,
                    grass_temp=.6, grass_moist=.7, nutrient=.8, litter=0)
        poor = rich.copy()
        poor['nutrient'] = 0
        plants.advance(rich, 0)
        plants.advance(poor, 0)
        self.assertGreater(rich['grass'], poor['grass'])
        self.assertLess(rich['nutrient'], .8)
        poor['litter'] = .5
        plants.advance(poor, 0)
        self.assertGreater(poor['nutrient'], 0)
        self.assertLess(poor['litter'], .5)

    def test_runoff_transfers_dissolved_nutrients(self):
        source = self.world.tiles[self.world.idx(8, 8)]
        target = self.world.tiles[self.world.idx(9, 8)]
        source.update(e=.8, water=.2, m=.4, temp=.6, nutrient=.5)
        target.update(e=.45, water=0, nutrient=.1)
        for dx, dy in ((-1, 0), (0, -1), (0, 1)):
            self.world.tiles[self.world.idx(8 + dx, 8 + dy)]['e'] = .9
        before = source['nutrient'] + target['nutrient']
        self.world.flow(self.world.idx(8, 8), 8, 8)
        self.assertGreater(target['nutrient'], .1)
        self.assertAlmostEqual(source['nutrient'] + target['nutrient'], before)

    def test_fertile_power_replenishes_nutrients(self):
        tile = self.world.tiles[self.world.idx(8, 8)]
        tile.update(e=.55, f=.2, nutrient=.1)
        effect = self.world.intervene('fertile', 8, 8, radius=1)
        self.assertGreater(effect['affected'], 0)
        self.assertGreater(tile['nutrient'], .1)

    def test_v10_migration_and_exact_continuation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'world.json'
            self.world.save(path)
            data = json.loads(path.read_text())
            data['version'] = 10
            for tile in data['tiles']:
                del tile['nutrient']
                del tile['litter']
            path.write_text(json.dumps(data))
            a = World.load(path)
            b = World.load(path)
            self.addCleanup(a.engine.close)
            self.addCleanup(b.engine.close)
            self.assertTrue(all(0 <= t['nutrient'] <= 1 and 0 <= t['litter'] <= 1 for t in a.tiles))
            for _ in range(8):
                a.step()
                b.step()
            self.assertEqual(a.snapshot(), b.snapshot())
            a.save(path)
            self.assertEqual(json.loads(path.read_text())['version'], 14)


if __name__ == '__main__':
    unittest.main()
