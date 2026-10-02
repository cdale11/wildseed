"""Matched, descriptive checks for behavioral novelty and ecological change."""
import argparse
import json

from .novelty import distance
from .world import World


def network_shift(before, after):
    """Total-variation shift in event shares between nonempty time windows."""
    keys = set(before) | set(after)
    if not keys or not sum(before.values()) or not sum(after.values()):
        return None
    old_total, new_total = sum(before.values()), sum(after.values())
    return round(sum(abs(before.get(key, 0) / old_total -
                         after.get(key, 0) / new_total) for key in keys) / 2, 4)


def evaluate(seed, ticks, interval, population, width, height, cap, learning):
    world = World(seed, width, height, workers=1, population=population,
                  learning=learning)
    world.max_population = cap
    windows = []
    previous = dict(world.ecology_events)
    previous_window = None
    try:
        for _ in range(ticks):
            world.step()
            if world.tick % interval and world.tick != ticks:
                continue
            current = dict(world.ecology_events)
            events = {key: current.get(key, 0) - previous.get(key, 0)
                      for key in set(current) | set(previous)}
            events = {key: count for key, count in sorted(events.items()) if count > 0}
            stats = world.snapshot()['stats']
            windows.append({'end_tick': world.tick, 'events': events,
                            'event_count': sum(events.values()),
                            'shift_from_previous': network_shift(previous_window, events)
                            if previous_window is not None else None,
                            'population': stats['population'],
                            'births': stats['births'], 'deaths': stats['deaths'],
                            'hunts': stats['hunts'],
                            'behavior_entropy': stats['behavior_entropy']})
            previous, previous_window = current, events
        archive = list(world.novelty_archive)
        # Action-frequency distance is descriptive. A record is only a candidate
        # until survival, reproduction and independent runs support its value.
        return {'seed': seed, 'learning': learning, 'windows': windows,
                'novelty_records': archive, 'novelty_count': len(archive),
                'final_population': len(world.organisms)}
    finally:
        world.engine.close()


def compare(control, learned):
    """Report matched differences without turning novelty into a success claim."""
    if control['seed'] != learned['seed']:
        raise ValueError('Comparisons require matching seeds')
    control_signatures = {}
    for record in control['novelty_records']:
        control_signatures.setdefault(record['kind'], []).append(record['signature'])
    candidates = []
    for record in learned['novelty_records']:
        references = control_signatures.get(record['kind'], [])
        nearest = min((distance(record['signature'], reference)
                       for reference in references), default=None)
        candidates.append({'tick': record['tick'], 'kind': record['kind'],
                           'control_distance': round(nearest, 3) if nearest is not None else None,
                           'status': 'unverified_observation'})
    return {'seed': control['seed'],
            'population_difference': learned['final_population'] - control['final_population'],
            'novelty_difference': learned['novelty_count'] - control['novelty_count'],
            'candidate_behaviors': candidates,
            'interpretation': 'Descriptive only; no adaptive advantage or new action is established.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds', default='42,43,44')
    parser.add_argument('--ticks', type=int, default=500)
    parser.add_argument('--interval', type=int, default=100)
    parser.add_argument('--population', type=int, default=80)
    parser.add_argument('--width', type=int, default=48)
    parser.add_argument('--height', type=int, default=32)
    parser.add_argument('--cap', type=int, default=500)
    args = parser.parse_args()
    try:
        seeds = [int(value) for value in args.seeds.split(',')]
    except ValueError:
        parser.error('seeds must be comma-separated integers')
    if (not seeds or len(seeds) > 100 or not 1 <= args.ticks <= 100000 or
            not 1 <= args.interval <= args.ticks or
            not 0 <= args.population <= args.cap <= 2500 or
            not 16 <= args.width <= 256 or not 16 <= args.height <= 256):
        parser.error('invalid experiment dimensions, population or interval')
    runs = []
    for seed in seeds:
        control = evaluate(seed, args.ticks, args.interval, args.population,
                           args.width, args.height, args.cap, False)
        learned = evaluate(seed, args.ticks, args.interval, args.population,
                           args.width, args.height, args.cap, True)
        runs.append({'control': control, 'learned': learned,
                     'comparison': compare(control, learned)})
    print(json.dumps({'config': vars(args), 'runs': runs}, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
