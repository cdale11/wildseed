import json
from pathlib import Path
import tempfile
import unittest

from wildseed import novelty
from wildseed.world import World


class NoveltyTests(unittest.TestCase):
    def make_world(self):
        world = World(419, 16, 16, population=0)
        self.addCleanup(world.engine.close)
        world.tiles[world.idx(8, 8)]['e'] = .55
        return world

    def test_archive_records_distinct_observed_behaviors_but_not_duplicates(self):
        world = self.make_world()
        first = world.spawn('grazer', 8, 8)
        second = world.spawn('grazer', 8, 8)
        immature = world.spawn('human', 8, 8)
        first.action_counts = [45, 0, 0, 0, 0, 0, 0]
        second.action_counts = [0, 0, 0, 0, 45, 0, 0]
        immature.action_counts = [39, 0, 0, 0, 0, 0, 0]
        world.tick = 100
        novelty.collect(world)
        self.assertEqual(len(world.novelty_archive), 1)
        self.assertEqual(world.novelty_archive[0]['organism_id'], first.id)
        self.assertEqual(world.novelty_archive[0]['outcome_rate'], 0)
        world.tick = 200
        novelty.collect(world)
        self.assertEqual(len(world.novelty_archive), 2)
        world.tick = 300
        novelty.collect(world)
        self.assertEqual(len(world.novelty_archive), 2)
        self.assertEqual(novelty.diversity(world.organisms)['modes'], 2)

    def test_step_counts_chosen_actions_and_snapshot_reports_diversity(self):
        world = self.make_world()
        world.tiles[world.idx(8, 8)]['grass'] = .8
        organism = world.spawn('grazer', 8, 8)
        world.engine.infer = lambda items: [([0.0] * 8, [0, 0, 0, 0, 1, 0, 0]) for _ in items]
        for _ in range(41):
            world.step()
        self.assertEqual(organism.action_counts[4], 41)
        self.assertGreater(organism.action_outcomes[4], 0)
        self.assertLess(organism.action_outcomes[4], 41)
        stats = world.snapshot()['stats']
        self.assertEqual(stats['behavior_eligible'], 1)
        self.assertEqual(stats['behavior_modes'], 1)
        self.assertEqual(stats['behavior_entropy'], 0.0)

    def test_socially_guided_move_is_not_mistaken_for_neural_choice(self):
        world = self.make_world()
        world.tiles[world.idx(9, 8)]['e'] = .55
        organism = world.spawn('human', 8, 8)
        organism.migration_town = 1
        organism.migration_route = [world.idx(9, 8)]
        world.settlements.append({'id': 1, 'x': 9, 'y': 8, 'culture': organism.culture,
                                  'houses': 1, 'stock': 10, 'wood': 0, 'ore': 0,
                                  'population': 0, 'age': 0, 'empty_ticks': 0})
        world.engine.infer = lambda items: [([0.0] * 8, [0, 0, 0, 0, 1, 0, 0]) for _ in items]
        world.step()
        self.assertEqual((organism.x, organism.y), (9, 8))
        self.assertEqual(organism.action_counts, [0] * 7)

    def test_save_replay_and_v18_migration(self):
        world = self.make_world()
        organism = world.spawn('grazer', 8, 8)
        organism.action_counts = [45, 0, 0, 0, 0, 0, 0]
        world.tick = 100
        novelty.collect(world)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'novelty.json'
            world.save(path)
            restored = World.load(path)
            self.addCleanup(restored.engine.close)
            for _ in range(8):
                world.step()
                restored.step()
            self.assertEqual(world.snapshot(), restored.snapshot())

            data = json.loads(path.read_text())
            data['version'] = 18
            del data['novelty_archive']
            for old in data['organisms']:
                del old['action_counts']
                del old['action_outcomes']
            path.write_text(json.dumps(data))
            migrated = World.load(path)
            self.addCleanup(migrated.engine.close)
            self.assertEqual(migrated.novelty_archive, [])
            self.assertEqual(migrated.organisms[0].action_counts, [0] * 7)
            self.assertEqual(migrated.organisms[0].action_outcomes, [0] * 7)


if __name__ == '__main__':
    unittest.main()
