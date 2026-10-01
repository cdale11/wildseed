"""Copy an atomically saved world to a separate backup directory with a hash manifest."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile


def _write_once(path, data):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.wildseed-', delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)  # Atomic publication; never replaces an earlier backup.
        directory = os.open(path.parent, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def backup(source, destination, now=None):
    source, destination = Path(source), Path(destination)
    if destination.resolve().is_relative_to(source.parent.resolve()):
        raise ValueError('Backup destination must be outside the source directory')
    data = source.read_bytes()
    document = json.loads(data)
    if not isinstance(document, dict) or type(document.get('version')) is not int or type(document.get('tick')) is not int:
        raise ValueError('Source is not a Wildseed world save')
    stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    sha = hashlib.sha256(data).hexdigest()
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = destination / f'wildseed-{stamp}-{sha[:12]}.json'
    manifest_path = target.with_suffix('.sha256.json')
    _write_once(target, data)
    manifest = {'source': str(source.resolve()), 'backup': str(target.resolve()), 'sha256': sha,
                'version': document['version'], 'tick': document['tick'], 'created_utc': stamp}
    _write_once(manifest_path, (json.dumps(manifest, indent=2) + '\n').encode())
    if hashlib.sha256(target.read_bytes()).hexdigest() != sha:
        raise OSError('Backup checksum mismatch')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', help='Trusted local world save')
    parser.add_argument('destination', help='Backup directory, preferably on separate storage')
    args = parser.parse_args()
    try:
        print(json.dumps(backup(args.source, args.destination), indent=2))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
