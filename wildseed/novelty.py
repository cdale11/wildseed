"""Bounded archive of observed action distributions, not a measure of intelligence."""
from collections import Counter
import math

MIN_ACTIONS = 40
ARCHIVE_LIMIT = 64
NOVELTY_DISTANCE = .22


def signature(counts):
    total = sum(counts)
    return [round(count / total, 3) for count in counts]


def distance(left, right):
    """Total-variation distance between two action distributions."""
    return sum(abs(a - b) for a, b in zip(left, right)) / 2


def collect(world):
    """Archive at most one new behavior per species at each census."""
    for kind in ('grazer', 'predator', 'human'):
        candidates = [o for o in world.organisms
                      if o.kind == kind and sum(o.action_counts) >= MIN_ACTIONS]
        if not candidates or len(world.novelty_archive) >= ARCHIVE_LIMIT:
            continue
        existing = [entry['signature'] for entry in world.novelty_archive
                    if entry['kind'] == kind]
        ranked = []
        for organism in candidates:
            observed = signature(organism.action_counts)
            nearest = min((distance(observed, old) for old in existing), default=1.0)
            ranked.append((-nearest, organism.id, organism, observed))
        negative_novelty, _, organism, observed = min(ranked)
        if -negative_novelty < NOVELTY_DISTANCE:
            continue
        world.novelty_archive.append({'tick': world.tick, 'kind': kind,
                                      'organism_id': organism.id,
                                      'signature': observed,
                                      'distance': round(-negative_novelty, 3)})


def diversity(organisms):
    """Normalized Shannon diversity of dominant actions among observed lives."""
    modes = Counter(max(range(7), key=lambda action: o.action_counts[action])
                    for o in organisms if sum(o.action_counts) >= MIN_ACTIONS)
    total = sum(modes.values())
    if not total:
        return {'eligible': 0, 'modes': 0, 'entropy': 0.0}
    entropy = -sum((count / total) * math.log(count / total)
                   for count in modes.values()) / math.log(7)
    return {'eligible': total, 'modes': len(modes), 'entropy': round(entropy, 3)}
