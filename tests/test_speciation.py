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

    def test_two_isolated_mating_pools_produce_no_cross_group_children(self):
        world = World(608, 16, 16, population=0)
        self.addCleanup(world.engine.close)
        world.tiles[world.idx(8, 8)].update(e=.55, lake=0, fire=0)
        adults = [world.spawn('grazer', 8, 8) for _ in range(4)]
        for organism, signal in zip(adults, (.1, .12, .8, .82)):
            organism.age = 60
            organism.energy = 150
            organism.mate_signal = signal
            organism.thermal_opt = world.tiles[world.idx(8, 8)]['temp']
        groups = {organism.id: i // 2 for i, organism in enumerate(adults)}
        world.rng.choices = lambda *args, **kwargs: [5]
        world.rng.random = lambda: 0.0
        world.step()
        children = [o for o in world.organisms if o.parent_b]
        self.assertGreaterEqual(len(children), 2)
        self.assertTrue(all(groups[o.parent_a] == groups[o.parent_b] for o in children))
        self.assertGreater(world.mate_rejections, 0)

    def test_forced_contact_barrier_persists_across_six_mutating_generations(self):
        world = World(609, 16, 16, population=0)
        self.addCleanup(world.engine.close)
        world.tiles[world.idx(8, 8)].update(e=.55, lake=0)
        pools = [[world.spawn('grazer', 8, 8) for _ in range(2)] for _ in range(2)]
        for pool, signal in zip(pools, (.15, .85)):
            for organism in pool:
                organism.mate_signal = signal
                organism.thermal_opt = .5
        for generation in range(1, 7):
            self.assertFalse(any(compatible_mates(a, b) for a in pools[0] for b in pools[1]))
            next_pools = []
            for pool in pools:
                children = [world.spawn('grazer', 8, 8, pool[0], pool[1]) for _ in range(2)]
                self.assertTrue(all(child.generation == generation and child.parent_b for child in children))
                next_pools.append(children)
            pools = next_pools
        self.assertFalse(any(compatible_mates(a, b) for a in pools[0] for b in pools[1]))


if __name__ == '__main__':
    unittest.main()
