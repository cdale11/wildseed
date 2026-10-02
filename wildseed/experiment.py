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
    humans = [o for o in world.organisms if o.kind == 'human']
    land = [t for t in world.tiles if t['e'] > .37]
    return {
        'tick': world.tick,
        'population': len(world.organisms),
        'species': {kind: counts[kind] for kind in ('grazer', 'predator', 'human')},
        'settlements': len(world.settlements),
        'settlement_food': round(sum(town['stock'] + town.get('reserve', 0.0)
                                     for town in world.settlements), 3),
        'human_mean_energy': round(sum(o.energy for o in humans) / max(1, len(humans)), 3),
        'social_updates': world.social_updates,
        'hunts': world.hunts,
        'hunt_move_updates': world.hunt_move_updates,
        'predator_ticks': predator_ticks,
        'hunts_per_1000_predator_ticks': round(world.hunts * 1000 / max(1, predator_ticks), 3),
        'births': world.births,
        'deaths': world.deaths,
        'training_steps': world.training_steps,
        'critic_updates': world.critic_updates,
        'mean_energy': round(sum(o.energy for o in world.organisms) / max(1, len(world.organisms)), 3),
        'grass_cover': round(sum(t['grass'] for t in land) / max(1, len(land)), 4),
        'tree_cover': round(sum(t['trees'] for t in land) / max(1, len(land)), 4),
        'lake_tiles': sum(t['lake'] >= .05 for t in land),
        'lake_storage': round(sum(t['lake'] for t in land), 4),
        'surface_water': round(sum(t['water'] for t in land), 4),
        'soil_moisture': round(sum(t['m'] for t in land), 4),
        'water_budget_residual': round(world.water_balance()['residual'], 8),
        'mineral_nutrients': round(sum(t['nutrient'] for t in land), 4),
        'organic_litter': round(sum(t['litter'] for t in land), 4),
        'nutrient_budget_residual': round(world.nutrient_balance()['residual'], 8),
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


def threat_avoidance_probe(world):
    """Mean lower move probability toward a synthetic threat cue, in points."""
    grazers = [organism for organism in world.organisms if organism.kind == 'grazer']
    if not grazers:
        return None
    scores = []
    for organism in grazers:
        for direction in range(4):
            danger = [0.0] * 4
            danger[direction] = .8
            observation = [1, .6, .2, .4, 0, .6, 0, 0,
                           *([0.0] * 4), *danger, *([0.0] * 12)]
            _, probabilities = forward((organism.weights, observation))
            scores.append((sum(probabilities[:4]) - probabilities[direction]) / 3 -
                          probabilities[direction])
    return round(sum(scores) / len(scores) * 100, 3)


def run(seed, ticks, population, width, height, cap, learning, interval=100,
        value_learning=True, navigation_learning=False, social_learning=True):
    world = World(seed, width, height, workers=1, population=population,
                  learning=learning, value_learning=value_learning,
                  navigation_learning=navigation_learning,
                  social_learning=social_learning)
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
        threat_probe = threat_avoidance_probe(world)
    finally:
        world.engine.close()
    return {'seed': seed, 'learning': learning, 'value_learning': value_learning,
            'navigation_learning': navigation_learning,
            'social_learning': social_learning,
            'samples': samples,
            'predator_directional_probe_pp': probe,
            'grazer_threat_avoidance_probe_pp': threat_probe}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds', default='42,43,44', help='Comma-separated integer seeds')
    parser.add_argument('--ticks', type=int, default=500)
    parser.add_argument('--population', type=int, default=80)
    parser.add_argument('--width', type=int, default=48)
    parser.add_argument('--height', type=int, default=32)
    parser.add_argument('--cap', type=int, default=500)
    parser.add_argument('--interval', type=int, default=100)
    parser.add_argument('--value-ablation', action='store_true',
                        help='Also run online policy learning without the value head')
    parser.add_argument('--navigation-credit', action='store_true',
                        help='Also run experimental predator prey-proximity movement credit')
    parser.add_argument('--social-ablation', action='store_true',
                        help='Also run online learning without peer imitation')
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
    modes = [(False, True, False, True), (True, True, False, True)]
    if args.value_ablation:
        modes.insert(1, (True, False, False, True))
    if args.navigation_credit:
        modes.append((True, True, True, True))
    if args.social_ablation:
        modes.insert(1, (True, True, False, False))
    results = [run(seed, args.ticks, args.population, args.width, args.height,
                   args.cap, learning, args.interval, value_learning,
                   navigation_learning, social_learning)
               for seed in seeds for learning, value_learning,
               navigation_learning, social_learning in modes]
    print(json.dumps({'config': vars(args), 'runs': results}, indent=2))


if __name__ == '__main__':
    main()
