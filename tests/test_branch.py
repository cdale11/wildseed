import json
from pathlib import Path
import tempfile
import unittest

from wildseed.branch import branch, digest
from wildseed.world import World


class BranchTests(unittest.TestCase):
    def test_replay_preserves_parent_and_is_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'parent.json'
            world = World(47, 24, 20, population=12)
            try:
                world.step()
                world.save(source)
            finally:
                world.engine.close()
            original = source.read_bytes()
            first = branch(source, root / 'first.json', ticks=3)
            second = branch(source, root / 'second.json', ticks=3)
            self.assertEqual(first['branch_sha256'], second['branch_sha256'])
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(first['parent_sha256'], digest(source))
            self.assertEqual(first['end_tick'], first['start_tick'] + 3)
            self.assertEqual(json.loads((root / 'first.experiment.json').read_text()), first)
            with self.assertRaises(ValueError):
                branch(source, root / 'first.json')
            with self.assertRaises(ValueError):
                branch(source, source)

    def test_intervention_changes_branch_and_rejects_invalid_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'parent.json'
            world = World(53, 24, 20, population=12)
            try:
                world.save(source)
            finally:
                world.engine.close()
            baseline = branch(source, root / 'baseline.json', ticks=2)
            changed = branch(source, root / 'changed.json', ticks=2,
                             intervention=('rain', 12, 10, 4, 3))
            self.assertNotEqual(baseline['branch_sha256'], changed['branch_sha256'])
            self.assertGreater(changed['intervention']['effect']['affected'], 0)
            self.assertEqual(changed['branch_sha256'], digest(root / 'changed.json'))
            loaded = World.load(root / 'changed.json')
            try:
                self.assertEqual(loaded.tick, changed['end_tick'])
            finally:
                loaded.engine.close()
            with self.assertRaises(ValueError):
                branch(source, root / 'invalid.json', intervention=('rain', 24, 0, 2, 1))
            self.assertFalse((root / 'invalid.json').exists())


if __name__ == '__main__':
    unittest.main()
