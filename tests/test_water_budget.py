import json
from pathlib import Path
import tempfile
import unittest

from wildseed.world import World


class WaterBudgetTests(unittest.TestCase):
    def test_weather_ecology_drainage_and_powers_close_represented_pool_budgets(self):
        world = World(712, 24, 20, population=15)
        self.addCleanup(world.engine.close)
        for tick in range(96):
            if tick in (8, 24, 40, 56, 72):
                world.intervene(('rain', 'drought', 'lake', 'ocean', 'volcano')[(tick - 8) // 16],
                                12, 10, radius=2)
            world.step()
            self.assertAlmostEqual(world.water_balance()['residual'], 0, places=7)
            self.assertAlmostEqual(world.nutrient_balance()['residual'], 0, places=7)
        fluxes = world.water_balance()['fluxes']
        self.assertGreater(fluxes['precipitation'], 0)
        self.assertLess(fluxes['evaporation'], 0)
        self.assertNotEqual(fluxes['interventions'], 0)
        self.assertNotEqual(world.nutrient_budget['plant_exchange'], 0)
        self.assertGreaterEqual(world.nutrient_budget['grazing_exchange'], 0)

    def test_budget_survives_save_and_old_schema_starts_new_account(self):
        world = World(713, 24, 20, population=10)
        self.addCleanup(world.engine.close)
        for _ in range(24):
            world.step()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'water.json'
            world.save(path)
            restored = World.load(path)
            self.addCleanup(restored.engine.close)
            self.assertEqual(world.water_budget, restored.water_budget)
            self.assertEqual(world.nutrient_budget, restored.nutrient_budget)
            for _ in range(24):
                world.step()
                restored.step()
            self.assertEqual(world.snapshot(), restored.snapshot())

            payload = json.loads(path.read_text())
            payload['version'] = 20
            del payload['water_budget']
            del payload['nutrient_budget']
            del payload['navigation_learning']
            path.write_text(json.dumps(payload))
            migrated = World.load(path)
            self.addCleanup(migrated.engine.close)
            self.assertAlmostEqual(migrated.water_balance()['residual'], 0, places=7)
            self.assertAlmostEqual(migrated.nutrient_balance()['residual'], 0, places=7)
            self.assertFalse(migrated.navigation_learning)


if __name__ == '__main__':
    unittest.main()
