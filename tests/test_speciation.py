import unittest

from wildseed.speciation import candidate_components
from wildseed.world import World, compatible_mates


class SpeciationMetricsTests(unittest.TestCase):
    def test_compatibility_components_detect_isolated_mating_pools(self):
        world = World(607, 16, 16, population=0)
        self.addCleanup(world.engine.close)
        world.tiles[world.idx(8, 8)].update(e=.55, lake=0)
        adults = [world.spawn('grazer', 8, 8) for _ in range(4)]
        for organism, signal in zip(adults, (.1, .12, .8, .82)):
            organism.age = 60
            organism.energy = 100
            organism.mate_signal = signal
            organism.thermal_opt = .5
        metrics = candidate_components(world.organisms)['grazer']
        self.assertEqual(metrics, {'adults': 4, 'component_sizes': [2, 2],
                                   'isolated_groups': 2})
        self.assertTrue(compatible_mates(adults[0], adults[1]))
        self.assertFalse(compatible_mates(adults[0], adults[2]))
        adults[3].energy = 40
        self.assertEqual(candidate_components(world.organisms)['grazer']['component_sizes'], [2, 1])


if __name__ == '__main__':
    unittest.main()
