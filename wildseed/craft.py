"""Bounded settlement experiments with composable material operations."""
import math

OPERATIONS = ('handle', 'blade', 'temper', 'hone')
COSTS = {'handle': (.15, 0.0), 'blade': (0.0, .10),
         'temper': (.10, 0.0), 'hone': (0.0, .03)}


def evaluate(recipe):
    """Sequence matters: processing before a blade exists has no effect."""
    grip = edge = durability = 0.0
    for operation in recipe:
        if operation == 'handle':
            grip = min(1.0, grip + .35)
        elif operation == 'blade':
            edge = min(1.0, edge + .45)
            durability = min(1.0, durability + .25)
        elif operation == 'temper' and edge > 0:
            durability = min(1.0, durability + .3)
            edge = max(0.0, edge - .05)
        elif operation == 'hone' and edge > 0:
            edge = min(1.0, edge + .2)
            durability = max(0.0, durability - .04)
    return math.sqrt(grip * edge) * (.5 + .5 * durability)


def attempt(world, town, recipe):
    """Consume inputs for one design trial and retain only useful knowledge."""
    if not 2 <= len(recipe) <= 4 or any(op not in OPERATIONS for op in recipe):
        raise ValueError('Invalid tool recipe')
    wood = sum(COSTS[op][0] for op in recipe)
    ore = sum(COSTS[op][1] for op in recipe)
    if town['wood'] < wood or town['ore'] < ore:
        return 0.0
    town['wood'] -= wood
    town['ore'] -= ore
    town['experiments'] = town.get('experiments', 0) + 1
    quality = evaluate(recipe)
    previous = town.get('tool_quality', 0.0)
    if quality > previous + .015:
        town['tool_quality'] = quality
        town['tool_recipe'] = list(recipe)
        world.event(f"Settlement {town['id']} discovered a better tool design.")
        return min(.5, quality - previous)
    return 0.0


def propose(world, town):
    """Try a new operation sequence or vary the settlement's best design."""
    best = town.get('tool_recipe', [])
    if best and world.rng.random() < .7:
        recipe = list(best)
        if len(recipe) < 4 and world.rng.random() < .25:
            recipe.append(world.rng.choice(OPERATIONS))
        else:
            recipe[world.rng.randrange(len(recipe))] = world.rng.choice(OPERATIONS)
    else:
        recipe = [world.rng.choice(OPERATIONS) for _ in range(world.rng.randint(2, 4))]
    return attempt(world, town, recipe)


def productivity(town):
    return 1.0 + .3 * town.get('tool_quality', 0.0)
