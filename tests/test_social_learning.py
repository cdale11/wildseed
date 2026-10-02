import json
from pathlib import Path
import tempfile
import unittest

from wildseed import society
from wildseed.brain import forward
from wildseed.world import World


class SocialLearningTests(unittest.TestCase):
    def make_world(self, learning=True):
        world = World(331, 16, 16, population=0, learning=learning)
        self.addCleanup(world.engine.close)
        world.tiles[world.idx(8, 8)]['e'] = .55
        mentor = world.spawn('human', 8, 8)
        learner = world.spawn('human', 8, 8)
        learner.culture = mentor.culture
        mentor.updates = 10
        mentor.reward_ema = .6
        learner.reward_ema = -.2
        mentor.weights = [1.0] * len(mentor.weights)
        learner.weights = [0.0] * len(learner.weights)
        mentor.value_weights = [1.0] * len(mentor.value_weights)
        learner.value_weights = [0.0] * len(learner.value_weights)
        return world, mentor, learner

    def test_peer_learning_changes_policy_and_value_without_copying_mentor(self):
        world, mentor, learner = self.make_world()
        obs = world.observe(learner)
        before = forward((learner.weights, obs))
        learner.pending_credit = [obs, before[0], before[1], 4, 0.0, 0.0]
        society.share_learned_behavior(world, [mentor, learner])
        self.assertEqual(learner.weights, [.02] * len(learner.weights))
        self.assertEqual(learner.value_weights, [.02] * len(learner.value_weights))
        self.assertEqual(mentor.weights, [1.0] * len(mentor.weights))
        self.assertIsNone(learner.pending_credit)
        self.assertEqual((learner.social_updates, world.social_updates), (1, 1))

    def test_learning_requires_local_culture_and_success_advantage(self):
        world, mentor, learner = self.make_world()
        learner.culture += 1
        society.share_learned_behavior(world, [mentor, learner])
        self.assertEqual(world.social_updates, 0)
        learner.culture = mentor.culture
        learner.reward_ema = mentor.reward_ema - .04
        society.share_learned_behavior(world, [mentor, learner])
        self.assertEqual(world.social_updates, 0)
        learner.reward_ema = -.2
        society.share_learned_behavior(world, [mentor, learner])
        self.assertEqual(world.social_updates, 1)

    def test_settlement_update_triggers_local_peer_learning(self):
        world, mentor, learner = self.make_world()
        world.settlements.append({'id': 1, 'x': 8, 'y': 8, 'culture': mentor.culture,
                                  'houses': 1, 'stock': 20.0, 'wood': 0.0,
                                  'ore': 0.0, 'population': 0, 'age': 0,
                                  'empty_ticks': 0})
        world.tick = 20
        society.update(world)
        self.assertEqual(world.social_updates, 1)
        self.assertEqual(learner.social_updates, 1)
        self.assertEqual(world.settlements[0]['population'], 2)

    def test_frozen_mode_and_save_migration(self):
        frozen, mentor, learner = self.make_world(learning=False)
        society.share_learned_behavior(frozen, [mentor, learner])
        self.assertEqual(frozen.social_updates, 0)
        self.assertEqual(learner.weights, [0.0] * len(learner.weights))

        world, mentor, learner = self.make_world()
        society.share_learned_behavior(world, [mentor, learner])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'world.json'
            world.save(path)
            restored = World.load(path)
            self.addCleanup(restored.engine.close)
            self.assertEqual(restored.snapshot(), world.snapshot())
            for _ in range(21):
                world.step()
                restored.step()
            self.assertEqual(restored.snapshot(), world.snapshot())

            data = json.loads(path.read_text())
            data['version'] = 17
            del data['social_updates']
            for organism in data['organisms']:
                del organism['reward_ema']
                del organism['social_updates']
            path.write_text(json.dumps(data))
            migrated = World.load(path)
            self.addCleanup(migrated.engine.close)
            self.assertEqual(migrated.social_updates, 0)
            self.assertTrue(all(o.reward_ema == 0 and o.social_updates == 0
                                for o in migrated.organisms))


if __name__ == '__main__':
    unittest.main()
