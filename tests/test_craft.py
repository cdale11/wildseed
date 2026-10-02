import json
from pathlib import Path
import tempfile
import unittest

from wildseed import craft, society
from wildseed.world import World


class CraftTests(unittest.TestCase):
    def setUp(self):
        self.world = World(1201, 16, 16, population=0)
        self.addCleanup(self.world.engine.close)
        for tile in self.world.tiles:
            tile.update(e=.55, lake=0, grass=.8, trees=.8, ore=1)

    def test_operation_order_and_resource_cost_produce_useful_tool(self):
        good = ['handle', 'blade', 'temper', 'hone']
        self.assertGreater(craft.evaluate(good),
                           craft.evaluate(list(reversed(good))))
        town = {'id': 1, 'wood': 3.0, 'ore': 1.0, 'tool_quality': 0.0,
                'tool_recipe': [], 'experiments': 0}
        reward = craft.attempt(self.world, town, good)
        self.assertGreater(reward, 0)
        self.assertGreater(town['tool_quality'], 0)
        self.assertEqual(town['tool_recipe'], good)
        self.assertEqual(town['experiments'], 1)
        self.assertLess(town['wood'], 3)
        self.assertLess(town['ore'], 1)
        self.assertEqual(craft.attempt(self.world, town, good), 0)
        self.assertEqual(town['experiments'], 2)
        with self.assertRaises(ValueError):
            craft.attempt(self.world, town, ['unknown', 'blade'])

    def test_productivity_and_trade_spread_design_without_free_resources(self):
        source = {'id': 1, 'x': 3, 'y': 3, 'culture': 1, 'houses': 2,
                  'stock': 40.0, 'wood': 3.0, 'ore': 1.0, 'population': 0, 'age': 0,
                  'tool_quality': 0.0, 'tool_recipe': [], 'experiments': 0}
        target = {'id': 2, 'x': 10, 'y': 3, 'culture': 2, 'houses': 2,
                  'stock': 0.0, 'wood': 0.0, 'ore': 2.0, 'population': 0, 'age': 0,
                  'tool_quality': 0.0, 'tool_recipe': [], 'experiments': 0}
        self.world.settlements = [source, target]
        craft.attempt(self.world, source, ['handle', 'blade', 'temper', 'hone'])
        human = self.world.spawn('human', 3, 3)
        human.occupation = 'farmer'
        tile = self.world.tiles[self.world.idx(3, 3)]
        tile['grass'] = .8
        society.work(self.world, human, tile)
        enhanced_harvest = .8 - tile['grass']
        tile['grass'] = .8
        source['tool_quality'] = 0
        society.work(self.world, human, tile)
        ordinary_harvest = .8 - tile['grass']
        self.assertGreater(enhanced_harvest, ordinary_harvest)

        source['tool_quality'] = craft.evaluate(source['tool_recipe'])
        society.dispatch_trade(self.world)
        self.assertEqual(len(self.world.shipments), 1)
        shipment = self.world.shipments[0]
        self.assertEqual(shipment['tool_recipe'], source['tool_recipe'])
        self.world.tick = shipment['arrival']
        society.deliver_shipments(self.world)
        self.assertEqual(target['tool_recipe'], source['tool_recipe'])
        self.assertEqual(target['tool_quality'], source['tool_quality'])

    def test_surplus_assigns_an_inventor_who_tries_a_design(self):
        human = self.world.spawn('human', 8, 8)
        town = {'id': 1, 'x': 8, 'y': 8, 'culture': human.culture, 'houses': 2,
                'stock': 20.0, 'wood': 9.0, 'ore': 3.0, 'population': 1,
                'tool_quality': 0.0, 'tool_recipe': [], 'experiments': 0}
        self.world.settlements.append(town)
        society.assign_jobs(self.world, town, [human])
        self.assertEqual(human.occupation, 'inventor')
        before = town['wood'] + town['ore']
        society.work(self.world, human, self.world.tiles[self.world.idx(8, 8)])
        self.assertEqual(town['experiments'], 1)
        self.assertLess(town['wood'] + town['ore'], before)

    def test_old_towns_migrate_empty_knowledge_and_new_saves_replay(self):
        human = self.world.spawn('human', 8, 8)
        town = {'id': 1, 'x': 8, 'y': 8, 'culture': human.culture, 'houses': 2,
                'stock': 20.0, 'wood': 3.0, 'ore': 1.0, 'population': 1, 'age': 0,
                'empty_ticks': 0, 'tool_quality': 0.0, 'tool_recipe': [], 'experiments': 0}
        self.world.settlements.append(town)
        craft.attempt(self.world, town, ['handle', 'blade', 'temper', 'hone'])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'tools.json'
            self.world.save(path)
            restored = World.load(path)
            self.addCleanup(restored.engine.close)
            for _ in range(32):
                self.world.step()
                restored.step()
            self.assertEqual(self.world.snapshot(), restored.snapshot())

            payload = json.loads(path.read_text())
            payload['version'] = 25
            for key in ('tool_quality', 'tool_recipe', 'experiments'):
                del payload['settlements'][0][key]
            path.write_text(json.dumps(payload))
            migrated = World.load(path)
            self.addCleanup(migrated.engine.close)
            self.assertEqual((migrated.settlements[0]['tool_quality'],
                              migrated.settlements[0]['tool_recipe'],
                              migrated.settlements[0]['experiments']), (0.0, [], 0))


if __name__ == '__main__':
    unittest.main()
