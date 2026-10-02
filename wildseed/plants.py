"""Bounded grass/tree cohorts with inherited climate preferences per tile."""


def clamp(value):
    return max(0.0, min(1.0, value))


def initialize(tile, variation=0.0):
    tile['grass_pop'] = int(tile['grass'] * 100)
    tile['tree_pop'] = int(tile['trees'] * 40)
    for kind in ('grass', 'tree'):
        tile[kind + '_temp'] = clamp(tile['temp'] + variation)
        tile[kind + '_moist'] = clamp(tile['m'] - variation)


def migrate(tile):
    tile.setdefault('grass_pop', int(tile['grass'] * 100))
    tile.setdefault('tree_pop', int(tile['trees'] * 40))
    for kind in ('grass', 'tree'):
        tile.setdefault(kind + '_temp', tile['temp'])
        tile.setdefault(kind + '_moist', tile['m'])


def establish(tile, kind):
    cover = tile['grass'] if kind == 'grass' else tile['trees']
    tile[kind + '_pop'] = max(tile[kind + '_pop'], int(cover * (100 if kind == 'grass' else 40)))
    tile[kind + '_temp'] = tile['temp']
    tile[kind + '_moist'] = tile['m']


def fitness(tile, kind):
    return max(.05, 1 - abs(tile['temp'] - tile[kind + '_temp']) * 1.6) * max(
        .08, 1 - abs(tile['m'] - tile[kind + '_moist']) * 1.1)


def advance(tile, season):
    """Cohorts germinate, compete, and produce seeds without spontaneous creation."""
    # Soil organisms release minerals from litter; temperature and water set the rate.
    recycled = min(tile['litter'], tile['litter'] * (.008 + .014 * tile['temp']) * (.3 + .7 * tile['m']))
    tile['litter'] -= recycled
    tile['nutrient'] = clamp(tile['nutrient'] + recycled)
    for kind, capacity in (('grass', 100), ('tree', 40)):
        seed = tile[kind + '_seed']
        count_key = kind + '_pop'
        if seed > 0 and tile[count_key] == 0:
            tile[count_key] = 1
        competitor = tile['trees'] if kind == 'grass' else tile['grass']
        target = max(1, int(capacity * seed * fitness(tile, kind) * (1 - competitor * .5))) if seed > 0 else 0
        if tile[count_key] < target:
            tile[count_key] = min(target, tile[count_key] + 2)
        elif tile[count_key] > target:
            tile[count_key] = max(target, tile[count_key] - 2)
    grass_fit = fitness(tile, 'grass')
    tree_fit = fitness(tile, 'tree')
    available = tile['nutrient'] / (tile['nutrient'] + .15)
    grass_growth = .035 * tile['m'] * tile['f'] * (.7 + .3 * season) * (1 + .25 * tile['scar'])
    grass_gain = min(1 - tile['grass'], grass_growth * grass_fit *
                     tile['grass_pop'] / 100 * (1 - tile['trees'] * .65) * available)
    tree_gain = min(1 - tile['trees'], .012 * tile['m'] * tile['f'] *
                    max(0, tile['temp'] - .12) * tree_fit * (1 - .65 * tile['scar']) *
                    tile['tree_pop'] / 40 * (1 - tile['grass'] * .25) * available)
    uptake = min(tile['nutrient'], grass_gain * .20 + tree_gain * .35)
    tile['nutrient'] -= uptake
    grass_turnover = tile['grass'] * .0015
    tree_turnover = tile['trees'] * .0003
    tile['grass'] = clamp(tile['grass'] + grass_gain - grass_turnover)
    tile['trees'] = clamp(tile['trees'] + tree_gain - tree_turnover)
    tile['litter'] = clamp(tile['litter'] + grass_turnover * .6 + tree_turnover * .8)
    tile['grass_seed'] = clamp(tile['grass_seed'] * .999 + tile['grass'] * .003)
    tile['tree_seed'] = clamp(tile['tree_seed'] * .9995 + tile['trees'] * .001)


def disperse(source, destination, rng):
    """Seed transfer carries trait means; colonization adds small heritable variation."""
    for kind, amount in (('grass', .004), ('tree', .002)):
        incoming = source[kind + '_seed'] * amount
        if incoming <= 0:
            continue
        seed_key = kind + '_seed'
        old_seed = destination[seed_key]
        destination[seed_key] = clamp(old_seed + incoming)
        fraction = min(1, incoming / max(.000001, old_seed + incoming))
        founding = destination[kind + '_pop'] == 0 and old_seed < .01
        for trait in ('temp', 'moist'):
            key = kind + '_' + trait
            inherited = clamp(source[key] + (rng.gauss(0, .015) if founding else 0))
            destination[key] = clamp(destination[key] * (1 - fraction) + inherited * fraction)


def burn(tile):
    tile['grass_pop'] = int(tile['grass_pop'] * .6)
    tile['tree_pop'] = int(tile['tree_pop'] * .75)


def clear(tile):
    tile['grass'] = tile['trees'] = tile['grass_seed'] = tile['tree_seed'] = 0
    tile['grass_pop'] = tile['tree_pop'] = 0
