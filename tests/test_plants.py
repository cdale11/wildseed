import random
import unittest

from wildseed import plants
from wildseed.world import World


class PlantTests(unittest.TestCase):
    def test_climate_traits_change_growth_and_population(self):
        world = World(15, 16, 16, population=0)
        self.addCleanup(world.engine.close)
        matched = world.tiles[world.idx(7, 7)]
        mismatched = world.tiles[world.idx(8, 7)]
        matched.update(e=.55, m=.7, temp=.7, f=.8, grass=.2, trees=0,
                       grass_seed=.5, tree_seed=0, grass_pop=30, tree_pop=0,
                       grass_temp=.7, grass_moist=.7)
        mismatched.update(matched.copy(), grass_temp=0, grass_moist=0)
        plants.advance(matched, 0)
        plants.advance(mismatched, 0)
        self.assertGreater(matched['grass'] - .2, mismatched['grass'] - .2)
        self.assertGreater(matched['grass_pop'], mismatched['grass_pop'])

    def test_seed_colonization_inherits_mutated_genome(self):
        world = World(16, 16, 16, population=0)
        self.addCleanup(world.engine.close)
        source = world.tiles[world.idx(5, 5)]
        destination = world.tiles[world.idx(6, 5)]
        source.update(grass_seed=.9, grass_temp=.8, grass_moist=.2, tree_seed=.4,
                      tree_temp=.3, tree_moist=.9)
        destination.update(grass_seed=0, tree_seed=0, grass_pop=0, tree_pop=0)
        plants.disperse(source, destination, random.Random(1))
        self.assertGreater(destination['grass_seed'], 0)
        self.assertGreater(destination['tree_seed'], 0)
        self.assertLess(abs(destination['grass_temp'] - source['grass_temp']), .1)
        self.assertLess(abs(destination['tree_moist'] - source['tree_moist']), .1)
        plants.advance(destination, 0)
        self.assertGreater(destination['grass_pop'], 0)

    def test_climate_reversal_favors_opposite_inherited_temperature_trait(self):
        world = World(777, 16, 16, population=0)
        self.addCleanup(world.engine.close)
        base = world.tiles[0].copy()
        base.update(e=.55, m=.7, temp=.2, f=.8, grass=.2, trees=0,
                    grass_seed=.5, tree_seed=0, grass_pop=30, tree_pop=0,
                    nutrient=.8, litter=.2, scar=0, grass_moist=.7)
        cold, warm = base.copy(), base.copy()
        cold['grass_temp'], warm['grass_temp'] = .2, .8
        for _ in range(200):
            plants.advance(cold, 0)
            plants.advance(warm, 0)
        self.assertGreater(cold['grass'] - warm['grass'], .5)
        cold['temp'] = warm['temp'] = .8
        cold['nutrient'] = warm['nutrient'] = .8
        for _ in range(200):
            plants.advance(cold, 0)
            plants.advance(warm, 0)
        self.assertGreater(warm['grass'] - cold['grass'], .2)

    def test_flood_and_meteor_remove_plant_cohorts(self):
        world = World(17, 16, 16, population=0)
        self.addCleanup(world.engine.close)
        for tile in world.tiles:
            tile.update(e=.55, grass=.5, trees=.5, grass_seed=.5, tree_seed=.5,
                        grass_pop=50, tree_pop=20)
        world.intervene('meteor', 8, 8, radius=1)
        target = world.tiles[world.idx(8, 8)]
        self.assertEqual((target['grass_pop'], target['tree_pop']), (0, 0))
        world.intervene('ocean', 5, 5, radius=1)
        flooded = world.tiles[world.idx(5, 5)]
        self.assertEqual((flooded['grass_pop'], flooded['tree_pop']), (0, 0))
