"""Reproducible paired ecology runs with online learning enabled or frozen.

The frozen control still samples actions and inherits mutated weights. Only
within-lifetime gradient updates are disabled, isolating that part of learning.
"""
import argparse
from collections import Counter
import json

from .brain import forward
from .world import World


def measure(world, predator_ticks=0):
    counts = Counter(o.kind for o in world.organisms)
    land = [t for t in world.tiles if t['e'] > .37]
    return {
        'tick': world.tick,
        'population': len(world.organisms),
        'species': {kind: counts[kind] for kind in ('grazer', 'predator', 'human')},
        'hunts': world.hunts,
        'hunt_move_updates': world.hunt_move_updates,
        'predator_ticks': predator_ticks,
        'hunts_per_1000_predator_ticks': round(world.hunts * 1000 / max(1, predator_ticks), 3),
        'births': world.births,
        'deaths': world.deaths,
        'training_steps': world.training_steps,
        'mean_energy': round(sum(o.energy for o in world.organisms) / max(1, len(world.organisms)), 3),
        'grass_cover': round(sum(t['grass'] for t in land) / max(1, len(land)), 4),
        'tree_cover': round(sum(t['trees'] for t in land) / max(1, len(land)), 4),
    }


def directional_probe(world):
    """Mean extra move probability toward a visible prey cue, in percentage points."""
    predators = [organism for organism in world.organisms if organism.kind == 'predator']
    if not predators:
        return None
    scores = []
    for organism in predators:
        for direction in range(4):
            food = [0.0] * 4
            food[direction] = .8
            observation = [1, .6, .2, 0, 0, .6, 0, 0, *food, *([0.0] * 16)]
            _, probabilities = forward((organism.weights, observation))
            scores.append(probabilities[direction] -
                          (sum(probabilities[:4]) - probabilities[direction]) / 3)
    return round(sum(scores) / len(scores) * 100, 3)


def run(seed, ticks, population, width, height, cap, learning, interval=100):
    world = World(seed, width, height, workers=1, population=population, learning=learning)
    world.max_population = cap
    predator_ticks = 0
    samples = [measure(world)]
    try:
        for _ in range(ticks):
            predator_ticks += sum(o.kind == 'predator' for o in world.organisms)
            world.step()
            if world.tick % interval == 0 or world.tick == ticks:
                samples.append(measure(world, predator_ticks))
        probe = directional_probe(world)
    finally:
        world.engine.close()
    return {'seed': seed, 'learning': learning, 'samples': samples,
            'predator_directional_probe_pp': probe}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds', default='42,43,44', help='Comma-separated integer seeds')
    parser.add_argument('--ticks', type=int, default=500)
    parser.add_argument('--population', type=int, default=80)
    parser.add_argument('--width', type=int, default=48)
    parser.add_argument('--height', type=int, default=32)
    parser.add_argument('--cap', type=int, default=500)
    parser.add_argument('--interval', type=int, default=100)
    args = parser.parse_args()
    try:
        seeds = [int(value) for value in args.seeds.split(',')]
    except ValueError:
        parser.error('seeds must be comma-separated integers')
    if not seeds or not 1 <= args.ticks <= 100000 or not 1 <= args.interval <= args.ticks:
        parser.error('seeds, ticks and interval must be nonempty positive values')
    if not 1 <= args.population <= args.cap <= 2500:
        parser.error('population must be positive and no greater than cap (maximum 2500)')
    if not 16 <= args.width <= 256 or not 16 <= args.height <= 256:
        parser.error('dimensions must be between 16 and 256')
    results = [run(seed, args.ticks, args.population, args.width, args.height,
                   args.cap, learning, args.interval)
               for seed in seeds for learning in (False, True)]
    print(json.dumps({'config': vars(args), 'runs': results}, indent=2))


if __name__ == '__main__':
    main()
