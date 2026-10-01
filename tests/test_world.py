import math
from pathlib import Path
import tempfile
import unittest
from wildseed.brain import forward, learn, PARAMS, INPUTS, BrainEngine
from wildseed.world import World
from wildseed.server import Simulation

class SimulationTests(unittest.TestCase):
    def world(self, seed=42):
        w = World(seed, 24, 20, population=30)
        self.addCleanup(w.engine.close)
        return w

    def test_seed_and_replay(self):
        a, b = self.world(), self.world()
        for _ in range(12): a.step(); b.step()
        self.assertEqual(a.snapshot(), b.snapshot())

    def test_save_restores_rng_and_neural_weights(self):
        a = self.world()
        for _ in range(10): a.step()
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'world.json'
            a.save(path)
            b = World.load(path)
            self.addCleanup(b.engine.close)
            for _ in range(10): a.step(); b.step()
            self.assertEqual(a.snapshot(), b.snapshot())
            self.assertEqual(a.organisms[0].weights, b.organisms[0].weights)

    def test_learning_increases_rewarded_action_probability(self):
        w = [.1] * PARAMS
        obs = [1.] * INPUTS
        hidden, probabilities = forward((w, obs))
        learn(w, obs, hidden, probabilities, 4, 1.)
        self.assertGreater(forward((w, obs))[1][4], probabilities[4])

    def test_inheritance_mutates_and_tracks_lineage(self):
        w = self.world(); parent = w.organisms[0]
        child = w.spawn(parent.kind, parent.x, parent.y, parent)
        self.assertEqual(child.generation, 1)
        self.assertNotEqual(parent.weights, child.weights)
        self.assertIsNot(parent.weights, child.weights)

    def test_resources_and_policies_stay_finite(self):
        w = self.world()
        for _ in range(100): w.step()
        for t in w.tiles:
            self.assertTrue(all(math.isfinite(v) for v in t.values()))
            for key in ('m', 'f', 'grass', 'trees', 'fire'):
                self.assertTrue(0 <= t[key] <= 1, (key, t[key]))
        for o in w.organisms:
            self.assertTrue(all(math.isfinite(v) and abs(v) <= 4 for v in o.weights))
        self.assertGreater(w.training_steps, 0)

    def test_water_blocks_spawn_and_rain_stops_fire(self):
        w = self.world(); w.tiles[0]['e'] = .2
        self.assertIsNone(w.spawn('human', 0, 0))
        w.tiles[1]['fire'] = 1; w.intervene('rain', 1, 0)
        self.assertEqual(w.tiles[1]['fire'], 0)

    def test_commands_reject_bad_input(self):
        sim = Simulation(self.world(), '/unused')
        for data in ({'action':'speed','value':True}, {'action':'pause','value':'false'},
                     {'action':'tool','tool':'fire','x':-1,'y':0}, {'action':'tool','tool':[]}, []):
            with self.assertRaises(ValueError): sim.command(data)
        sim.command({'action':'pause','value':True}); self.assertTrue(sim.paused)

    def test_multiprocess_matches_scalar(self):
        engine = BrainEngine(workers=2); self.addCleanup(engine.close)
        items = [([.1] * PARAMS, [i / 32] * INPUTS) for i in range(32)]
        self.assertEqual(engine.infer(items), [forward(item) for item in items])

if __name__ == '__main__': unittest.main()
