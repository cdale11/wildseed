"""Create a reproducible causal branch from a trusted local world save."""
import argparse
import hashlib
import json
import os
from pathlib import Path

from .powers import POWER_IDS
from .world import World


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def branch(source, output, ticks=0, intervention=None):
    source, output = Path(source), Path(output)
    if source.resolve() == output.resolve():
        raise ValueError('Branch output must differ from the source save')
    if output.exists() or output.with_suffix('.experiment.json').exists():
        raise ValueError('Branch output or experiment manifest already exists')
    if not 0 <= ticks <= 100000:
        raise ValueError('Ticks must be between 0 and 100000')
    if intervention is not None:
        tool, x, y, radius, strength = intervention
        if tool not in POWER_IDS or any(type(value) is not int for value in (x, y, radius, strength)):
            raise ValueError('Invalid intervention')
        if not 1 <= radius <= 10 or not 1 <= strength <= 3:
            raise ValueError('Invalid brush size or strength')
    parent_hash = digest(source)
    world = World.load(source, workers=1)
    try:
        started = world.tick
        if intervention is not None:
            if not (0 <= x < world.width and 0 <= y < world.height):
                raise ValueError('Intervention coordinates are outside the world')
            effect = world.intervene(tool, x, y, radius, strength)
        else:
            effect = None
        for _ in range(ticks):
            world.step()
        world.save(output)
        manifest = {'parent': str(source.resolve()), 'parent_sha256': parent_hash,
                    'branch': str(output.resolve()), 'branch_sha256': digest(output),
                    'seed': world.seed, 'start_tick': started, 'end_tick': world.tick,
                    'intervention': {'tool': tool, 'x': x, 'y': y, 'radius': radius,
                                     'strength': strength, 'effect': effect} if intervention else None,
                    'stats': world.snapshot()['stats']}
        target = output.with_suffix('.experiment.json')
        temporary = target.with_suffix('.tmp')
        temporary.parent.mkdir(parents=True, exist_ok=True)
        with temporary.open('w') as handle:
            json.dump(manifest, handle, indent=2, allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(target)
        return manifest
    finally:
        world.engine.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', help='Trusted local world save')
    parser.add_argument('output', help='New branch save')
    parser.add_argument('--ticks', type=int, default=0)
    parser.add_argument('--tool', choices=sorted(POWER_IDS))
    parser.add_argument('--x', type=int)
    parser.add_argument('--y', type=int)
    parser.add_argument('--radius', type=int, default=3)
    parser.add_argument('--strength', type=int, default=1)
    args = parser.parse_args()
    if args.tool and (args.x is None or args.y is None):
        parser.error('--tool requires --x and --y')
    if not args.tool and (args.x is not None or args.y is not None):
        parser.error('--x and --y require --tool')
    intervention = (args.tool, args.x, args.y, args.radius, args.strength) if args.tool else None
    try:
        print(json.dumps(branch(args.source, args.output, args.ticks, intervention), indent=2))
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
