"""Seeded, periodic terrain and climate generation; no simulation side effects."""
import math
import random
from . import plants, watershed

GEOGRAPHIES = {
    'continents': ('Continents', 'Broad landmasses, sheltered bays and open oceans.'),
    'archipelago': ('Archipelago', 'Scattered islands and turquoise channels.'),
    'highlands': ('Highlands', 'Mountain ridges, upland forests and valleys.'),
    'riverlands': ('Riverlands', 'Meandering waterways across fertile lowlands.'),
    'caldera': ('Caldera', 'A volcanic crater enclosed by a mountainous rim.'),
    'atoll': ('Atoll', 'A broken island ring around a blue lagoon.'),
    'inland_sea': ('Inland sea', 'A large central sea surrounded by habitable land.'),
    'lake_country': ('Lake country', 'Inland basins and low ridges surrounding freshwater lakes.'),
    'shattered': ('Shattered coast', 'Rugged peninsulas, straits and fragmented shores.'),
}
# temperature, moisture, fertility, tree cover
BIOMES = {
    'temperate': ('Temperate', (.57, .62, .78, .6)),
    'rainforest': ('Rainforest', (.87, .93, .8, .96)),
    'desert': ('Desert', (.94, .09, .22, .025)),
    'savanna': ('Savanna', (.82, .35, .6, .15)),
    'taiga': ('Taiga', (.28, .58, .52, .76)),
    'tundra': ('Tundra', (.08, .35, .32, .03)),
    'swamp': ('Wetlands', (.67, .98, .85, .42)),
    'volcanic': ('Volcanic', (.75, .12, .36, .03)),
    'grassland': ('Grassland', (.55, .5, .7, .03)),
    'woodland': ('Woodland', (.58, .68, .75, .85)),
    'burnscar': ('Burn scar', (.55, .3, .3, 0.0)),
}
BIOME_NAMES = list(BIOMES) + ['lake']
SIZES = {'small': (64, 48), 'standard': (96, 64), 'large': (144, 96)}


def classify(t):
    if t.get('lake', 0) >= .05: return 'lake'
    if t.get('lava', 0) > .1: return 'volcanic'
    if t.get('scar', 0) > .25 and t['grass'] + t['trees'] < .35: return 'burnscar'
    if t['temp'] < .17: return 'tundra'
    if t['temp'] < .37: return 'taiga' if t['trees'] > .15 else 'tundra'
    if t['m'] < .18: return 'desert' if t['temp'] > .78 else 'volcanic'
    if t['m'] > .84 and t['e'] < .52: return 'swamp'
    if t['m'] > .7 and t['temp'] > .73 and t['trees'] > .3: return 'rainforest'
    if t['m'] < .43 and t['temp'] > .64 and t['grass'] > .15: return 'savanna'
    if t['trees'] > .42: return 'woodland'
    if t['grass'] > .28 and t['trees'] < .25: return 'grassland'
    return 'temperate'


def noise_grid(rng, width, height, frequency):
    lattice = [[rng.random() for _ in range(frequency)] for _ in range(frequency)]
    result = []
    for y in range(height):
        py = y / height * frequency; iy = int(py); fy = py - iy; sy = fy * fy * (3 - 2 * fy)
        for x in range(width):
            px = x / width * frequency; ix = int(px); fx = px - ix; sx = fx * fx * (3 - 2 * fx)
            a = lattice[iy][ix] * (1-sx) + lattice[iy][(ix+1)%frequency] * sx
            b = lattice[(iy+1)%frequency][ix] * (1-sx) + lattice[(iy+1)%frequency][(ix+1)%frequency] * sx
            result.append(a * (1-sy) + b * sy)
    return result


def generate(seed, width, height, geography='continents', biome='mixed'):
    if geography not in GEOGRAPHIES or biome not in {*BIOMES, 'mixed'}:
        raise ValueError('Unknown geography or biome')
    rng = random.Random(seed)
    coarse, detail, fine = [noise_grid(rng, width, height, f) for f in (4, 9, 20)]
    climate = noise_grid(rng, width, height, 5)
    cx, cy, phase = rng.uniform(.4,.6), rng.uniform(.4,.6), rng.random() * math.tau
    tiles = []
    for y in range(height):
        for x in range(width):
            i = y*width+x; nx, ny = x/width, y/height
            n = .6*coarse[i] + .28*detail[i] + .12*fine[i]
            radius = math.hypot(nx-cx, (ny-cy)*.85)
            if geography == 'continents': e = .16 + n*.62
            elif geography == 'archipelago': e = .10 + n*.53
            elif geography == 'highlands': e = .32+n*.55 + abs(detail[i]-.5)*.2
            elif geography == 'riverlands':
                channel = abs(nx - (.5 + .18*math.sin(ny*math.tau+phase) + .04*math.sin(ny*math.tau*3)))
                e = .43+n*.25 - .27*math.exp(-(channel/.045)**2)
            elif geography == 'caldera': e = .26 + .51*math.exp(-((radius-.24)/.09)**2) + (n-.5)*.25
            elif geography == 'atoll': e = .24 + .24*math.exp(-((radius-.29)/.065)**2) + (n-.5)*.18
            elif geography == 'inland_sea': e = .57+n*.22 - .43*math.exp(-(radius/.28)**4)
            elif geography == 'lake_country':
                basin_a = math.exp(-(((nx-.29)/.09)**2 + ((ny-.41)/.11)**2))
                basin_b = math.exp(-(((nx-.69)/.10)**2 + ((ny-.63)/.09)**2))
                e = .53 + (n-.5)*.20 - .16*max(basin_a, basin_b)
            else: e = .15 + .35*detail[i] + .20*coarse[i] + .12*fine[i]
            e = max(.05,min(.95,e))
            if biome == 'mixed':
                temp = .12 + .85*climate[i] - max(0,e-.6)*.5
                moisture = .1 + .85*coarse[(i+width*7)%len(coarse)]
                fertility, trees = .65, .7
            else:
                temp, moisture, fertility, trees = BIOMES[biome][1]
                temp += (climate[i]-.5)*.14 - max(0,e-.6)*.3
                moisture += (coarse[i]-.5)*.2
            temp = max(0,min(1,temp)); moisture=max(0,min(1,moisture))
            land = e > .37
            t = {'e':e,'m':moisture,'f':fertility,'temp':temp,
                 'grass':moisture*fertility*(.5+fine[i]*.5) if land else 0,
                 'trees':trees*moisture*(.3+detail[i]*.7) if land and e<.75 and temp>.17 else 0,
                 'ore':max(0,e-.53)*8 + (fine[i]*.3 if land else 0), 'fire':0.0}
            # Seed banks let vegetation colonize disturbed ground without creating plants from nothing.
            t['grass_seed'] = t['grass']
            t['tree_seed'] = t['trees']
            t['water'] = max(0, moisture - .72) * .03 if land else 0.0
            t['sediment'] = 0.0
            t['lava'] = 0.0
            t['traffic'] = 0.0
            t['road'] = 0.0
            t['river'] = 0.0
            t['scar'] = 1.0 if biome == 'burnscar' and land else 0.0
            t['nutrient'] = fertility * (.35 + .3 * fine[i]) if land else 0.0
            t['litter'] = (.08 * t['grass'] + .12 * t['trees']) if land else 0.0
            plants.initialize(t, (fine[i] - .5) * .12)
            tiles.append(t)
    watershed.seed_lakes(tiles, width, height)
    return tiles


def options():
    return {'geographies':[{'id':k,'name':v[0],'description':v[1]} for k,v in GEOGRAPHIES.items()],
            'biomes':[{'id':'mixed','name':'Natural mosaic'}]+[{'id':k,'name':v[0]} for k,v in BIOMES.items()],
            'sizes':[{'id':k,'name':f'{k.title()} · {w} × {h}'} for k,(w,h) in SIZES.items()]}


def client_tiles(tiles):
    """Stable map payload shared by world previews and active snapshots."""
    return [[round(t[k], 3) for k in ('e', 'm', 'grass', 'trees', 'ore', 'fire', 'f', 'temp')] +
            [BIOME_NAMES.index(classify(t)), round(t['water'], 3), round(t['lava'], 3),
             t['grass_pop'], t['tree_pop'], round(t['road'], 3),
             round(t['nutrient'], 3), round(t['litter'], 3), round(t['river'], 3),
             round(t['scar'], 3), round(t['lake'], 3)] for t in tiles]
