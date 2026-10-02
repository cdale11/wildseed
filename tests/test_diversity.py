import unittest

from wildseed.diversity import summarize
from wildseed.world import World


class DiversityTests(unittest.TestCase):
    def test_primary_lineage_and_trait_spread_follow_retained_ancestry(self):
        world = World(809, 16, 16, population=0)
        self.addCleanup(world.engine.close)
        world.tiles[world.idx(8, 8)].update(e=.55, lake=0)
        a = world.spawn('grazer', 8, 8)
        b = world.spawn('grazer', 8, 8)
        a.mate_signal = b.mate_signal = .5
        a.thermal_opt = b.thermal_opt = .5
        a.size, b.size = .8, 1.2
        child = world.spawn('grazer', 8, 8, a, b)
        report = summarize(world.organisms, world.ancestry)
        grazers = report['species']['grazer']
        self.assertEqual(grazers['primary_lineages'], 2)
        self.assertEqual(grazers['effective_lineages'], 1.8)
        self.assertGreater(grazers['size_spread'], 0)
        self.assertEqual(child.parent_a, a.id)
        self.assertEqual(report['untracked_roots'], 0)

        world.organisms.remove(a)
        report = world.snapshot()['diversity']
        self.assertEqual(report['species']['grazer']['primary_lineages'], 2)
        self.assertEqual(report['untracked_roots'], 1)

    def test_empty_species_have_finite_zero_metrics(self):
        world = World(810, 16, 16, population=0)
        self.addCleanup(world.engine.close)
        report = summarize(world.organisms, world.ancestry)
        for entry in report['species'].values():
            self.assertEqual(entry['living'], 0)
            self.assertEqual(entry['effective_lineages'], 0)
            self.assertEqual(entry['mate_signal_spread'], 0)


if __name__ == '__main__':
    unittest.main()
