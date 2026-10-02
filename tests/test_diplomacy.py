import json
from pathlib import Path
import tempfile
import unittest

from wildseed import society
from wildseed.world import World


class DiplomacyTests(unittest.TestCase):
    def setUp(self):
        self.world = World(1401, 16, 16, population=0)
        self.addCleanup(self.world.engine.close)
        for tile in self.world.tiles:
            tile.update(e=.55, lake=0, fire=0)
        self.raiders = [self.world.spawn('human', 3, 3) for _ in range(3)]
        for raider in self.raiders:
            raider.energy = 100
            raider.culture = 1
        self.source = {'id': 1, 'x': 3, 'y': 3, 'culture': 1, 'houses': 1,
                       'stock': 0.0, 'reserve': 0.0, 'wood': 0.0, 'ore': 0.0,
                       'population': 3, 'age': 0, 'empty_ticks': 0, 'granary': 0,
                       'tool_recipe': [], 'tool_quality': 0.0, 'experiments': 0,
                       'grievance': 0}
        self.target = {'id': 2, 'x': 9, 'y': 3, 'culture': 2, 'houses': 1,
                       'stock': 40.0, 'reserve': 0.0, 'wood': 0.0, 'ore': 0.0,
                       'population': 0, 'age': 0, 'empty_ticks': 0, 'granary': 0,
                       'tool_recipe': [], 'tool_quality': 0.0, 'experiments': 0,
                       'grievance': 0}
        self.world.settlements = [self.source, self.target]

    def test_persistent_shortage_launches_route_bound_raid_with_real_cost_and_theft(self):
        residents = {1: self.raiders, 2: []}
        for _ in range(2):
            society.dispatch_raid(self.world, residents)
        self.assertEqual(self.world.shipments, [])
        society.dispatch_raid(self.world, residents)
        self.assertEqual(self.world.raids_launched, 1)
        self.assertEqual([o.energy for o in self.raiders], [92] * 3)
        shipment = self.world.shipments[0]
        self.assertEqual(shipment['kind'], 'raid')
        self.assertTrue(all(self.world.tiles[index]['e'] > .37 for index in shipment['path']))
        self.world.tick = shipment['arrival']
        self.world.rng.random = lambda: 0.0
        society.deliver_shipments(self.world)
        self.assertEqual((self.source['stock'], self.target['stock']), (6, 34))
        self.assertEqual(self.world.raids_succeeded, 1)
        self.assertLess(society.relation(self.world, 1, 2), 0)

    def test_water_blocks_raid_and_successful_trade_improves_relations(self):
        for y in range(self.world.height):
            for x in (5, 15):
                self.world.tiles[self.world.idx(x, y)]['e'] = .2
        for _ in range(4):
            society.dispatch_raid(self.world, {1: self.raiders, 2: []})
        self.assertEqual(self.world.raids_launched, 0)

        for tile in self.world.tiles:
            tile['e'] = .55
        self.source['stock'] = 40
        self.target['stock'] = 0
        self.target['ore'] = 2
        society.dispatch_trade(self.world)
        shipment = self.world.shipments[0]
        self.world.tick = shipment['arrival']
        society.deliver_shipments(self.world)
        self.assertGreater(society.relation(self.world, 1, 2), 0)

    def test_relations_and_raid_replay_migrate_from_v27(self):
        for _ in range(3):
            society.dispatch_raid(self.world, {1: self.raiders, 2: []})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'raid.json'
            self.world.save(path)
            restored = World.load(path)
            self.addCleanup(restored.engine.close)
            self.assertEqual(self.world.snapshot(), restored.snapshot())
            self.world.tick = restored.tick = self.world.shipments[0]['arrival']
            society.deliver_shipments(self.world)
            society.deliver_shipments(restored)
            self.assertEqual(self.world.snapshot(), restored.snapshot())

            payload = json.loads(path.read_text())
            payload['version'] = 27
            for key in ('relations', 'raids_launched', 'raids_succeeded'):
                del payload[key]
            for town in payload['settlements']:
                del town['grievance']
            path.write_text(json.dumps(payload))
            migrated = World.load(path)
            self.addCleanup(migrated.engine.close)
            self.assertEqual((migrated.relations, migrated.raids_launched,
                              migrated.raids_succeeded), ({}, 0, 0))
            self.assertTrue(all(town['grievance'] == 0 for town in migrated.settlements))


if __name__ == '__main__':
    unittest.main()
