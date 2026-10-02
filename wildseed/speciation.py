"""Offline mating-compatibility graph for trusted world saves."""
import argparse
import json

from .world import World


def candidate_components(organisms):
    """Exact compatibility components among living reproductive adults."""
    results = {}
    for kind in ('grazer', 'predator', 'human'):
        adults = sorted((o for o in organisms if o.kind == kind and o.age > 45 and o.energy > 75),
                        key=lambda o: (o.mate_signal, o.id))
        roots = list(range(len(adults)))

        def root(index):
            while roots[index] != index:
                roots[index] = roots[roots[index]]
                index = roots[index]
            return index

        for i, first in enumerate(adults):
            for j in range(i + 1, len(adults)):
                other = adults[j]
                if other.mate_signal - first.mate_signal >= .13:
                    break
                if abs(other.thermal_opt - first.thermal_opt) >= .28:
                    continue
                a, b = root(i), root(j)
                if a != b:
                    roots[max(a, b)] = min(a, b)
        sizes = {}
        for i in range(len(adults)):
            ancestor = root(i)
            sizes[ancestor] = sizes.get(ancestor, 0) + 1
        results[kind] = {'adults': len(adults), 'component_sizes': sorted(sizes.values(), reverse=True),
                         'isolated_groups': sum(size >= 2 for size in sizes.values())}
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('save', help='Trusted local world save')
    args = parser.parse_args()
    world = World.load(args.save)
    try:
        print(json.dumps({'seed': world.seed, 'tick': world.tick,
                          'candidate_components': candidate_components(world.organisms)}, indent=2))
    finally:
        world.engine.close()


if __name__ == '__main__':
    main()
