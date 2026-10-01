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

    def test_trade_uses_land_route_and_delivers_real_goods(self):
        source = {'id': 1, 'x': 3, 'y': 3, 'culture': 1, 'houses': 1,
                  'stock': 40.0, 'wood': 0.0, 'ore': 0.0, 'population': 0, 'age': 0}
        target = {'id': 2, 'x': 10, 'y': 3, 'culture': 2, 'houses': 1,
                  'stock': 0.0, 'wood': 0.0, 'ore': 2.0, 'population': 0, 'age': 0}
        self.world.settlements = [source, target]
        society.dispatch_trade(self.world)
        self.assertEqual(len(self.world.shipments), 1)
        shipment = self.world.shipments[0]
        self.assertEqual((source['stock'], target['ore']), (35, 1))
        self.assertTrue(all(self.world.tiles[index]['e'] > .37 for index in shipment['path']))
        self.assertEqual(self.world.snapshot()['stats']['caravans'], 1)
        self.world.tick = shipment['arrival']
        society.deliver_shipments(self.world)
        self.assertEqual((target['stock'], source['ore']), (5, 1))
        self.assertEqual(self.world.shipments, [])

    def test_trade_does_not_cross_water_without_route(self):
        for y in range(self.world.height):
            for x in (5, 15):
                self.world.tiles[self.world.idx(x, y)]['e'] = .2
        self.world.settlements = [
            {'id': 1, 'x': 3, 'y': 3, 'stock': 40, 'ore': 0, 'wood': 0},
            {'id': 2, 'x': 10, 'y': 3, 'stock': 0, 'ore': 2, 'wood': 0},
        ]
        society.dispatch_trade(self.world)
        self.assertEqual(self.world.shipments, [])

    def test_v8_save_migrates_empty_caravans(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'old.json'
            self.world.save(path)
            data = json.loads(path.read_text())
            data['version'] = 8
            del data['shipments']
            path.write_text(json.dumps(data))
            loaded = World.load(path)
            self.addCleanup(loaded.engine.close)
            self.assertEqual(loaded.shipments, [])

    def test_unoccupied_town_loses_houses_and_is_abandoned(self):
        town = {'id': 1, 'x': 8, 'y': 8, 'culture': 1, 'houses': 1,
                'stock': 0.0, 'wood': 0.0, 'ore': 0.0,
                'population': 0, 'age': 0, 'empty_ticks': 0}
        self.world.settlements = [town]
        for _ in range(10):
            self.world.tick += 20
            society.update(self.world)
        self.assertEqual(self.world.settlements, [])
        self.assertTrue(any('abandoned' in event['text'] for event in self.world.events))
