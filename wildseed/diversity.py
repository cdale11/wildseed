"""Bounded, descriptive trait and primary-parent lineage diversity."""
from collections import Counter
import math


def summarize(organisms, ancestry):
    """Report living diversity from the retained ancestry window.

    Primary-parent lineages are useful continuity markers, not taxonomic
    species. A pruned ancestry record can split an older lineage into several
    apparent roots, so reports include the window's truncation count.
    """
    parents = {child: parent_a for child, parent_a, _parent_b, _tick, _kind in ancestry}
    parents.update({organism.id: organism.parent_a for organism in organisms})
    root_cache = {}
    truncated = set()

    def root(identifier):
        path = []
        current = identifier
        while current not in root_cache and parents.get(current, 0):
            path.append(current)
            current = parents[current]
        if current in root_cache:
            answer = root_cache[current]
        else:
            answer = current
            if current not in parents:
                truncated.add(current)
        root_cache[identifier] = answer
        for item in path:
            root_cache[item] = answer
        return answer

    result = {}
    for kind in ('grazer', 'predator', 'human'):
        members = [organism for organism in organisms if organism.kind == kind]
        counts = Counter(root(organism.id) for organism in members)
        population = len(members)

        def spread(name):
            if not population:
                return 0.0
            values = [getattr(organism, name) for organism in members]
            mean = sum(values) / population
            return math.sqrt(sum((value - mean) ** 2 for value in values) / population)

        result[kind] = {'living': population,
                        'primary_lineages': len(counts),
                        'effective_lineages': round(population ** 2 / sum(n * n for n in counts.values()), 3)
                        if counts else 0.0,
                        'size_spread': round(spread('size'), 4),
                        'thermal_spread': round(spread('thermal_opt'), 4),
                        'mate_signal_spread': round(spread('mate_signal'), 4)}
    return {'species': result, 'ancestry_records': len(ancestry),
            'untracked_roots': len(truncated)}
