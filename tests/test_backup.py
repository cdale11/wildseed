import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from wildseed.backup import backup
from wildseed.world import World


class BackupTests(unittest.TestCase):
    def test_backup_is_verified_and_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'data' / 'world.json'
            world = World(43, 24, 20, population=10)
            try:
                world.save(source)
            finally:
                world.engine.close()
            original = source.read_bytes()
            instant = datetime(2026, 10, 2, tzinfo=timezone.utc)
            record = backup(source, root / 'external', now=instant)
            copy = Path(record['backup'])
            self.assertEqual(copy.read_bytes(), original)
            self.assertEqual(record['sha256'], hashlib.sha256(original).hexdigest())
            self.assertEqual(json.loads(copy.with_suffix('.sha256.json').read_text()), record)
            self.assertEqual(source.read_bytes(), original)
            with self.assertRaises(FileExistsError):
                backup(source, root / 'external', now=instant)
            self.assertEqual(copy.read_bytes(), original)

    def test_rejects_non_save(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'invalid.json'
            source.write_text('{"version": 10}')
            with self.assertRaises(ValueError):
                backup(source, root / 'backups')


if __name__ == '__main__':
    unittest.main()
