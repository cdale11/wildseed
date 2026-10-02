import json
from pathlib import Path
import tempfile
import unittest

from wildseed import society
from wildseed.world import World


class GranaryTests(unittest.TestCase):
    def setUp(self):
        self.world = World(1101, 16, 16, population=0)
        self.addCleanup(self.world.engine.close)
        for tile in self.world.tiles:
            tile.update(e=.55, lake=0, fire=0)
        self.human = self.world.spawn('human', 8, 8)
        self.town = {'id': 1, 'x': 8, 'y': 8, 'culture': self.human.culture,
                     'houses': 1, 'stock': 20.0, 'wood': 3.0, 'ore': 0.0,
                     'reserve': 0.0, 'granary': 0, 'population': 0,
                     'age': 0, 'empty_ticks': 0}
        self.world.settlements.append(self.town)

    def test_surplus_builds_store_and_shortage_releases_real_food(self):
        society.update(self.world)
        self.assertEqual(self.town['granary'], 1)
        self.assertEqual(self.town['wood'], 1.0)
        self.assertGreater(self.town['reserve'], 0)
        self.assertEqual(self.world.snapshot()['stats']['granaries'], 1)
        self.assertTrue(any('granary' in event['text'] for event in self.world.events))

        self.town['stock'] = 0
        self.human.energy = 50
        reserve_before = self.town['reserve']
        society.update(self.world)
        self.assertLess(self.town['reserve'], reserve_before)
        self.assertGreater(self.human.energy, 50)

    def test_old_town_migrates_empty_granary_fields_and_replays(self):
        society.update(self.world)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'town.json'
            self.world.save(path)
            restored = World.load(path)
            self.addCleanup(restored.engine.close)
            for _ in range(40):
                self.world.step()
                restored.step()
            self.assertEqual(self.world.snapshot(), restored.snapshot())

            payload = json.loads(path.read_text())
            payload['version'] = 23
            del payload['settlements'][0]['granary']
            del payload['settlements'][0]['reserve']
            path.write_text(json.dumps(payload))
            migrated = World.load(path)
            self.addCleanup(migrated.engine.close)
            self.assertEqual((migrated.settlements[0]['granary'],
                              migrated.settlements[0]['reserve']), (0, 0.0))


if __name__ == '__main__':
    unittest.main()
