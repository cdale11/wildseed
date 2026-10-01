import json
from pathlib import Path
import tempfile
import unittest

from wildseed.world import World, compatible_mates


class LineageTests(unittest.TestCase):
    def setUp(self):
        self.world = World(21, 16, 16, population=0)
        self.addCleanup(self.world.engine.close)
        for tile in self.world.tiles:
            tile.update(e=.55, temp=.7, grass=.5, fire=0)

    def test_mating_recombines_traits_and_records_both_parents(self):
        a = self.world.spawn('grazer', 8, 8)
        b = self.world.spawn('grazer', 8, 8)
        a.age = b.age = 100
        a.energy = b.energy = 150
        a.fertility = 4  # make this controlled attempt certain
        a.thermal_opt = .4
        b.thermal_opt = .5
        a.mate_signal = b.mate_signal = .45
        self.world.engine.infer = lambda items: [([0.0] * 8, [0, 0, 0, 0, 0, 1, 0]) for _ in items]
        self.world.step()
        self.assertGreaterEqual(self.world.sexual_births, 1)
        child = next(o for o in self.world.organisms if o.parent_a == a.id and o.parent_b == b.id)
        self.assertTrue(.35 < child.thermal_opt < .55)
        self.assertEqual(self.world.ancestry[0][:3], [child.id, a.id, b.id])
        self.assertGreater(self.world.snapshot()['stats']['ecotypes'], 0)

    def test_incompatible_adults_block_gene_flow_and_count_encounters(self):
        a = self.world.spawn('grazer', 8, 8)
        b = self.world.spawn('grazer', 8, 8)
        for organism in (a, b):
            organism.age = 100
            organism.energy = 150
            organism.fertility = 4
            organism.thermal_opt = .6
        a.mate_signal, b.mate_signal = .1, .9
        self.assertFalse(compatible_mates(a, b))
        with self.assertRaises(ValueError):
            self.world.spawn('grazer', 8, 8, a, b)
        self.world.engine.infer = lambda items: [([0.0] * 8, [0, 0, 0, 0, 0, 1, 0]) for _ in items]
        self.world.step()
        self.assertEqual(self.world.births, 0)
        self.assertEqual(self.world.sexual_births, 0)
        self.assertGreaterEqual(self.world.mate_rejections, 1)
        self.assertEqual(self.world.mate_rejections, self.world.mate_encounters)
        self.assertEqual(self.world.snapshot()['stats']['mate_types'], 2)

    def test_mate_signal_inherits_and_stays_bounded(self):
        a = self.world.spawn('grazer', 8, 8)
        b = self.world.spawn('grazer', 8, 8)
        a.mate_signal, b.mate_signal = .4, .48
        a.thermal_opt = b.thermal_opt = .6
        child = self.world.spawn('grazer', 8, 8, a, b)
        self.assertTrue(.35 < child.mate_signal < .53)
        self.assertEqual(child.parent_b, b.id)

    def test_v11_migrates_mate_signal_and_metrics(self):
        self.world.spawn('grazer', 8, 8)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'old.json'
            self.world.save(path)
            data = json.loads(path.read_text())
            data['version'] = 11
            del data['mate_encounters']
            del data['mate_rejections']
            for organism in data['organisms']:
                del organism['mate_signal']
            path.write_text(json.dumps(data))
            migrated = World.load(path)
            self.addCleanup(migrated.engine.close)
            self.assertEqual(migrated.organisms[0].mate_signal, .5)
            self.assertEqual((migrated.mate_encounters, migrated.mate_rejections), (0, 0))
            migrated.save(path)
            self.assertEqual(json.loads(path.read_text())['version'], 12)

    def test_local_temperature_affects_heritable_fitness(self):
        adapted = self.world.spawn('grazer', 8, 8)
        maladapted = self.world.spawn('grazer', 8, 8)
        adapted.thermal_opt = .7
        maladapted.thermal_opt = .05
        self.world.engine.infer = lambda items: [([0.0] * 8, [0, 0, 0, 0, 0, 0, 1]) for _ in items]
        self.world.step()
        self.assertGreater(adapted.energy, maladapted.energy)

    def test_v6_save_migrates_ancestry_and_climate_traits(self):
        organism = self.world.spawn('human', 8, 8)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'old.json'
            self.world.save(path)
            data = json.loads(path.read_text())
            data['version'] = 6
            del data['sexual_births']
            del data['ancestry']
            for item in data['organisms']:
                for key in ('parent_a', 'parent_b', 'thermal_opt'):
                    del item[key]
                current = item['weights']
                item['weights'] = [value for j in range(8) for value in current[j*28:j*28+20]] + current[224:]
                del item['memory']
            path.write_text(json.dumps(data))
            migrated = World.load(path)
            self.addCleanup(migrated.engine.close)
            self.assertEqual(migrated.sexual_births, 0)
            self.assertEqual(len(migrated.ancestry), 0)
            self.assertEqual(migrated.organisms[0].thermal_opt,
                             migrated.tiles[migrated.idx(organism.x, organism.y)]['temp'])
