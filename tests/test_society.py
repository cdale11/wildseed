import json
from pathlib import Path
import tempfile
import unittest

from wildseed import society
from wildseed.world import World


class SocietyTests(unittest.TestCase):
    def setUp(self):
        self.world = World(31, 16, 16, population=0)
        self.addCleanup(self.world.engine.close)
        for tile in self.world.tiles:
            tile.update(e=.55, grass=.7, trees=.7, ore=1, fire=0, road=0, traffic=0)

    def test_household_owns_food_and_jobs_respond_to_shortage(self):
        human = self.world.spawn('human', 8, 8)
        human.wood = 2.5
        society.work(self.world, human, self.world.tiles[self.world.idx(8, 8)])
        self.assertEqual(len(self.world.settlements), 1)
        self.assertEqual(self.world.settlements[0]['houses'], 1)
        human.energy = 50
        society.update(self.world)
        self.assertEqual(len(self.world.households), 1)
        self.assertEqual(human.household, self.world.households[0]['id'])
        self.assertGreater(human.energy, 50)
        self.assertIn(human.occupation, ('farmer', 'woodcutter', 'miner', 'builder'))
        self.world.settlements[0]['stock'] = 0
        human.occupation = 'farmer'
        society.work(self.world, human, self.world.tiles[self.world.idx(8, 8)])
        self.assertGreater(self.world.settlements[0]['stock'], 0)

    def test_human_traffic_creates_a_road_with_lower_move_cost(self):
        human = self.world.spawn('human', 8, 8)
        target = self.world.tiles[self.world.idx(9, 8)]
        target['traffic'] = .35
        before = human.energy
        self.world.engine.infer = lambda items: [([0.0] * 8, [0, 1, 0, 0, 0, 0, 0]) for _ in items]
        self.world.step()
        self.assertEqual((human.x, human.y), (9, 8))
        self.assertGreater(target['road'], 0)
        self.assertLess(human.energy, before)

    def test_v7_save_migrates_society_and_road_fields(self):
        human = self.world.spawn('human', 8, 8)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'old.json'
            self.world.save(path)
            data = json.loads(path.read_text())
            data['version'] = 7
            for key in ('households', 'next_town_id', 'next_household_id'):
                del data[key]
            for tile in data['tiles']:
                del tile['road']
                del tile['traffic']
            for organism in data['organisms']:
                del organism['household']
                del organism['occupation']
            path.write_text(json.dumps(data))
            migrated = World.load(path)
            self.addCleanup(migrated.engine.close)
            self.assertEqual(migrated.households, [])
            self.assertEqual(migrated.organisms[0].household, 0)
            self.assertEqual(migrated.organisms[0].occupation, 'forager')
            self.assertTrue(all(tile['road'] == tile['traffic'] == 0 for tile in migrated.tiles))
