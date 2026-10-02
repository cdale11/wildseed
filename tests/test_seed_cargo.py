import json
from pathlib import Path
import tempfile
import unittest

from wildseed import plants
from wildseed.world import World


class SeedCargoTests(unittest.TestCase):
    def test_forager_transfer_conserves_seed_bank_and_carries_traits(self):
        world = World(901, 16, 16, population=0)
        self.addCleanup(world.engine.close)
        source = world.tiles[world.idx(8, 8)]
        target = world.tiles[world.idx(8, 7)]
        source.update(e=.55, lake=0, grass_seed=.8, tree_seed=.6,
                      grass_temp=.8, grass_moist=.7, tree_temp=.9, tree_moist=.6)
        target.update(e=.55, lake=0, grass_seed=0, tree_seed=0,
                      grass_temp=.2, grass_moist=.2, tree_temp=.2, tree_moist=.2)
        cargo = [0.0] * 6
        before = source['grass_seed'] + source['tree_seed']
        plants.collect_seed_cargo(source, cargo)
        self.assertAlmostEqual(source['grass_seed'] + source['tree_seed'] + cargo[0] + cargo[3], before)
        self.assertEqual((cargo[1], cargo[2], cargo[4], cargo[5]), (.8, .7, .9, .6))
        plants.deposit_seed_cargo(target, cargo, .5)
        self.assertAlmostEqual(source['grass_seed'] + source['tree_seed'] +
                               target['grass_seed'] + target['tree_seed'] + cargo[0] + cargo[3], before)
        self.assertEqual((target['grass_temp'], target['grass_moist'],
                          target['tree_temp'], target['tree_moist']), (.8, .7, .9, .6))
        target.update(m=.8, f=.8, nutrient=.5, grass=0, trees=0,
                      grass_pop=0, tree_pop=0)
        plants.advance(target, 1)
        self.assertGreater(target['grass_pop'], 0)
        self.assertGreater(target['grass'], 0)

    def test_forager_collects_during_eating_and_deposits_after_move(self):
        world = World(902, 16, 16, population=0)
        self.addCleanup(world.engine.close)
        for tile in world.tiles:
            tile.update(e=.55, lake=0, fire=0, grass=0, grass_seed=0,
                        tree_seed=0, grass_pop=0, tree_pop=0)
        origin = world.tiles[world.idx(8, 8)]
        target = world.tiles[world.idx(8, 7)]
        origin.update(grass=.8, grass_seed=.8, grass_pop=80)
        grazer = world.spawn('grazer', 8, 8)
        actions = iter((4, 0))
        world.rng.choices = lambda *args, **kwargs: [next(actions)]
        world.step()
        self.assertGreater(grazer.seed_cargo[0], 0)
        world.step()
        self.assertEqual((grazer.x, grazer.y), (8, 7))
        self.assertGreater(target['grass_seed'], 0)
        self.assertGreater(world.snapshot()['stats']['seed_transferred'], 0)

    def test_seed_cargo_persists_and_v21_migrates(self):
        world = World(903, 16, 16, population=0)
        self.addCleanup(world.engine.close)
        grazer = world.spawn('grazer')
        grazer.seed_cargo = [.02, .4, .6, .01, .7, .8]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'cargo.json'
            world.save(path)
            restored = World.load(path)
            self.addCleanup(restored.engine.close)
            self.assertEqual(restored.organisms[0].seed_cargo, grazer.seed_cargo)
            for _ in range(16):
                world.step()
                restored.step()
            self.assertEqual(world.snapshot(), restored.snapshot())

            payload = json.loads(path.read_text())
            payload['version'] = 21
            del payload['organisms'][0]['seed_cargo']
            del payload['seed_transferred']
            path.write_text(json.dumps(payload))
            migrated = World.load(path)
            self.addCleanup(migrated.engine.close)
            self.assertEqual(migrated.organisms[0].seed_cargo, [0.0] * 6)
            self.assertEqual(migrated.seed_transferred, 0.0)


if __name__ == '__main__':
    unittest.main()
