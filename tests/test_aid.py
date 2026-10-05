import json
from pathlib import Path
import tempfile
import unittest

from wildseed import society
from wildseed.world import World


class AidTests(unittest.TestCase):
    def setUp(self):
        self.world = World(551, 16, 16, population=0)
        self.addCleanup(self.world.engine.close)
        for tile in self.world.tiles:
            tile.update(e=.55, lake=0, fire=0)
        self.world.settlements = [
            {'id': 1, 'x': 3, 'y': 3, 'culture': 1, 'houses': 1,
             'stock': 40.0, 'wood': 0.0, 'ore': 0.0, 'population': 2, 'age': 0},
            {'id': 2, 'x': 8, 'y': 3, 'culture': 2, 'houses': 1,
             'stock': 0.0, 'wood': 0.0, 'ore': 0.0, 'population': 2, 'age': 0},
        ]
        for town in self.world.settlements:
            town.update(empty_ticks=0, reserve=0.0, granary=0, grievance=0,
                        tool_recipe=[], tool_quality=0.0, experiments=0)

    def test_trusted_town_sends_real_food_and_delivery_replays(self):
        self.world.relations['1:2'] = .25
        society.dispatch_aid(self.world)
        self.assertEqual(self.world.settlements[0]['stock'], 35)
        self.assertEqual(self.world.aid_sent, 1)
        self.assertEqual(self.world.shipments[0]['kind'], 'aid')
        society.dispatch_aid(self.world)
        self.assertEqual(self.world.aid_sent, 1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'aid.json'
            self.world.save(path)
            restored = World.load(path)
            self.addCleanup(restored.engine.close)
            self.assertEqual(self.world.snapshot(), restored.snapshot())
            for world in (self.world, restored):
                world.tick = world.shipments[0]['arrival']
                society.deliver_shipments(world)
            self.assertEqual(self.world.snapshot(), restored.snapshot())
        self.assertEqual(self.world.settlements[1]['stock'], 5)
        self.assertEqual(self.world.aid_delivered, 1)
        self.assertGreater(self.world.relations['1:2'], .25)

    def test_no_aid_without_trust_or_route(self):
        society.dispatch_aid(self.world)
        self.assertEqual(self.world.shipments, [])
        self.world.relations['1:2'] = .25
        self.world.settlements[1]['population'] = 0
        society.dispatch_aid(self.world)
        self.assertEqual(self.world.shipments, [])
        self.world.settlements[1]['population'] = 2
        for y in range(16):
            for x in (5, 15):
                self.world.tiles[self.world.idx(x, y)]['e'] = .2
        society.dispatch_aid(self.world)
        self.assertEqual(self.world.shipments, [])

    def test_same_culture_sends_small_aid_but_keeps_donor_floor(self):
        source, target = self.world.settlements
        source['culture'] = target['culture']
        source['stock'] = 7.0
        source['population'] = 1
        society.dispatch_aid(self.world)
        self.assertEqual(self.world.aid_sent, 1)
        self.assertEqual(source['stock'], 4)
        self.assertEqual(self.world.shipments[0]['food'], 3)

    def test_v29_defaults_new_counters(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'old.json'
            self.world.save(path)
            payload = json.loads(path.read_text())
            payload['version'] = 29
            del payload['aid_sent']
            del payload['aid_delivered']
            path.write_text(json.dumps(payload))
            restored = World.load(path)
            self.addCleanup(restored.engine.close)
            self.assertEqual((restored.aid_sent, restored.aid_delivered), (0, 0))


if __name__ == '__main__':
    unittest.main()
