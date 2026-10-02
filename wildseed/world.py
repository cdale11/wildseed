"""Seeded ecology with mutable terrain, individual policies and settlements."""
from collections import Counter, deque
from dataclasses import asdict, dataclass, field
import json
import math
import os
from pathlib import Path
import random

from .geography import generate, client_tiles
from .powers import apply as apply_power
from . import plants
from . import society
from . import weather
from . import watershed

from .brain import BrainEngine, PARAMS, HIDDEN, learn

SPECIES = ('grazer', 'predator', 'human')
DIRECTIONS = ((0, -1), (1, 0), (0, 1), (-1, 0))


def compatible_mates(a, b):
    """Heritable recognition and climate traits determine potential gene flow."""
    return (a.kind == b.kind and a.id != b.id and
            abs(a.mate_signal - b.mate_signal) < .13 and
            abs(a.thermal_opt - b.thermal_opt) < .28)


@dataclass
class Organism:
    id: int
    kind: str
    x: int
    y: int
    energy: float
    age: int
    generation: int
    size: float
    fertility: float
    weights: list
    baseline: float = 0
    updates: int = 0
    culture: int = 0
    wood: float = 0
    ore: float = 0
    last_move: list | None = None
    parent_a: int = 0
    parent_b: int = 0
    thermal_opt: float = .55
    mate_signal: float = .5
    household: int = 0
    occupation: str = 'forager'
    memory: list = field(default_factory=lambda: [0.0] * HIDDEN)
    migration_town: int = 0
    migration_route: list = field(default_factory=list)


class World:
    VERSION = 15

    def __init__(self, seed=42, width=96, height=64, workers=1, device='cpu', population=250, geography='continents', biome='mixed', learning=True):
        if not 16 <= width <= 256 or not 16 <= height <= 256:
            raise ValueError('Dimensions must be between 16 and 256')
        self.seed, self.width, self.height = seed, width, height
        self.geography, self.biome = geography, biome
        self.learning = learning
        self.rng = random.Random(seed)
        self.tick = 0
        self.next_id = 1
        self.max_population = 2500
        self.events = deque(maxlen=60)
        self.organisms = []
        self.settlements = []
        self.households = []
        self.shipments = []
        self.next_town_id = self.next_household_id = 1
        self.ancestry = deque(maxlen=50000)
        self.births = self.deaths = self.training_steps = self.hunts = self.hunt_move_updates = 0
        self.sexual_births = 0
        self.mate_encounters = self.mate_rejections = 0
        self.engine = BrainEngine(workers, device)
        self.tiles = self.generate()
        self.weather_width, self.weather_height, self.clouds = weather.initialize(seed, width, height)
        for i in range(population):
            self.spawn('human' if i % 8 == 0 else 'predator' if i % 10 == 0 else 'grazer')
        self.event('A new world takes its first breath.')

    def generate(self):
        return generate(self.seed, self.width, self.height, self.geography, self.biome)

    def idx(self, x, y):
        return (y % self.height) * self.width + x % self.width

    def event(self, text):
        self.events.appendleft({'tick': self.tick, 'text': text})

    def spawn(self, kind, x=None, y=None, parent=None, mate=None):
        if kind not in SPECIES or len(self.organisms) >= self.max_population:
            return None
        if x is None:
            land = [i for i, t in enumerate(self.tiles) if .38 < t['e'] < .75]
            if not land:
                return None
            index = self.rng.choice(land)
            x, y = index % self.width, index // self.width
        x, y = x % self.width, y % self.height
        if self.tiles[self.idx(x, y)]['e'] <= .37:
            return None
        if mate and (not parent or not compatible_mates(parent, mate)):
            raise ValueError('Invalid mate')
        weights = ([max(-4, min(4, (self.rng.choice((a, b)) if mate else a) + self.rng.gauss(0, .045)))
                    for a, b in zip(parent.weights, mate.weights if mate else parent.weights)]
                   if parent else [self.rng.gauss(0, .25) for _ in range(PARAMS)])
        inherited_size = (parent.size + mate.size) / 2 if mate else parent.size if parent else 1
        inherited_fertility = (parent.fertility + mate.fertility) / 2 if mate else parent.fertility if parent else 1
        inherited_temp = ((parent.thermal_opt + mate.thermal_opt) / 2 if mate else parent.thermal_opt) if parent else self.tiles[self.idx(x, y)]['temp']
        inherited_signal = ((parent.mate_signal + mate.mate_signal) / 2 if mate else parent.mate_signal) if parent else .5
        org = Organism(self.next_id, kind, x, y, 55 if parent else 85, 0,
                       parent.generation + 1 if parent else 0,
                       max(.5, min(1.6, inherited_size + self.rng.gauss(0, .04))) if parent else 1,
                       max(.5, min(1.6, inherited_fertility + self.rng.gauss(0, .04))) if parent else 1,
                       weights, culture=parent.culture if parent else (self.next_id % 5 + 1 if kind == 'human' else 0),
                       parent_a=parent.id if parent else 0, parent_b=mate.id if mate else 0,
                       thermal_opt=max(0, min(1, inherited_temp + self.rng.gauss(0, .025))),
                       mate_signal=max(0, min(1, inherited_signal + self.rng.gauss(0, .015 if parent else .06))),
                       household=parent.household if parent else 0)
        self.next_id += 1
        self.organisms.append(org)
        if parent:
            self.births += 1
            self.sexual_births += int(mate is not None)
            self.ancestry.append([org.id, org.parent_a, org.parent_b, self.tick, kind])
        return org

    def perception_index(self):
        """Snapshot living occupancy once per tick, never scan all agents per ray."""
        prey, threats = Counter(), Counter()
        for organism in self.organisms:
            if organism.energy <= 0:
                continue
            index = self.idx(organism.x, organism.y)
            if organism.kind == 'grazer':
                prey[index] += 1
            elif organism.kind == 'predator':
                threats[index] += 1
        return prey, threats

    def observe(self, o, perception=None):
        prey, threats = perception if perception is not None else self.perception_index()
        index = self.idx(o.x, o.y)
        t = self.tiles[index]
        food, danger, materials = [], [], []
        for dx, dy in DIRECTIONS:
            food_signal = danger_signal = material_signal = 0.0
            for distance in range(1, 4):
                target = self.idx(o.x + dx * distance, o.y + dy * distance)
                dest = self.tiles[target]
                if dest['e'] <= .37 or dest['e'] >= .88:
                    if distance == 1:
                        food_signal = -1
                    break
                attenuation = 1 / distance
                edible = min(1, prey[target]) if o.kind == 'predator' else dest['grass']
                food_signal = max(food_signal, edible * attenuation)
                threat = min(1, threats[target]) if o.kind == 'grazer' else 0
                danger_signal = max(danger_signal, max(threat, dest['fire']) * attenuation)
                resource = max(dest['trees'], min(1, dest['ore'])) if o.kind == 'human' else 0
                material_signal = max(material_signal, resource * attenuation)
            food.append(food_signal)
            danger.append(danger_signal)
            materials.append(material_signal)
        local_food = min(1, prey[index]) if o.kind == 'predator' else t['grass']
        return [1, o.energy / 150, min(1, o.age / 1000), local_food, t['trees'],
                t['m'], t['fire'], math.sin(self.tick / 180), *food, *danger, *materials,
                *o.memory]

    def climate(self):
        season = math.sin(self.tick / 180)
        if self.tick % 8 == 0:
            weather.advance(self)
        if self.tick % 32 == 0:
            watershed.advance(self)
        # Staggered tile updates distribute climate work across ticks.
        for i in range(self.tick % 4, len(self.tiles), 4):
            t = self.tiles[i]
            x, y = i % self.width, i // self.width
            t['m'] = max(0, min(1, t['m'] + .006 * season - .001 + t['trees'] * .0015))
            if t['e'] > .37:
                t['traffic'] *= .999
                t['road'] = max(0, t['road'] - .00002)
                plants.advance(t, season)
                t['f'] = min(1, t['f'] + .0003)
                if t['fire'] > 0:
                    burned = t['grass'] * .4 + t['trees'] * .12 + t['litter'] * .25
                    t['nutrient'] = min(1, t['nutrient'] + burned * .08)
                    t['litter'] *= .75
                    t['grass'] *= .6
                    t['trees'] *= .88
                    t['grass_seed'] *= .9
                    t['tree_seed'] *= .75
                    plants.burn(t)
                    t['f'] = min(1, t['f'] + .008)
                    t['fire'] = max(0, t['fire'] - .12 - t['m'] * .1)
                    if self.rng.random() < .28:
                        dx, dy = self.rng.choice(DIRECTIONS)
                        neighbor = self.tiles[self.idx(x + dx, y + dy)]
                        if neighbor['trees'] > .2 and neighbor['m'] < .6 and neighbor['e'] > .37:
                            neighbor['fire'] = .8
                # Seeds move locally; surface water and lava follow the lowest neighbor.
                dx, dy = self.rng.choice(DIRECTIONS)
                neighbor = self.tiles[self.idx(x + dx, y + dy)]
                if neighbor['e'] > .37:
                    plants.disperse(t, neighbor, self.rng)
                self.flow(i, x, y)
            else:
                plants.clear(t)
                t['river'] = 0
                t['nutrient'] = t['litter'] = 0
                t['fire'] = t['water'] = t['lava'] = t['traffic'] = t['road'] = 0
                deposit = min(t['sediment'], max(0, 1 - t['e']))
                t['sediment'] -= deposit
                t['e'] += deposit

    def flow(self, index, x, y):
        """Move runoff, suspended soil and lava downhill in bounded local amounts."""
        t = self.tiles[index]
        rain = max(0, t['m'] - .48) * .003 * max(.1, .6 + .4 * math.sin(self.tick / 180))
        evaporation = .0004 + .0006 * t['temp']
        t['water'] = max(0, min(1, t['water'] + rain - evaporation))
        if t['water'] > .001 and t['temp'] > .16:
            neighbor = min((self.tiles[self.idx(x + dx, y + dy)] for dx, dy in DIRECTIONS),
                           key=lambda n: n['e'] + n['water'])
            slope = t['e'] + t['water'] - (neighbor['e'] + neighbor['water'])
            if slope > .001:
                before = t['water']
                outflow = min(before, slope * .25, .035)
                t['water'] -= outflow
                erosion = min(max(0, t['e'] - .05), outflow * max(0, t['e'] - neighbor['e']) * .006)
                t['e'] -= erosion
                t['sediment'] += erosion
                carried = t['sediment'] * outflow / before
                t['sediment'] -= carried
                dissolved = min(t['nutrient'], outflow * .025)
                t['nutrient'] -= dissolved
                if neighbor['e'] > .37:
                    neighbor['water'] = min(1, neighbor['water'] + outflow)
                    neighbor['sediment'] += carried
                    neighbor['nutrient'] = min(1, neighbor['nutrient'] + dissolved)
                    neighbor['m'] = min(1, neighbor['m'] + outflow * .025)
                else:
                    neighbor['e'] = min(1, neighbor['e'] + carried)
        if t['water'] < .005 and t['sediment'] > 0:
            deposit = min(t['sediment'], .0008, max(0, 1 - t['e']))
            t['sediment'] -= deposit
            t['e'] += deposit

        if t['lava'] > 0:
            cooling = min(t['lava'], .022 + t['water'] * .12)
            t['lava'] -= cooling
            t['e'] = min(1, t['e'] + cooling * .012)
            t['temp'] = min(1, t['temp'] + t['lava'] * .008)
            if t['lava'] > .02:
                t['fire'] = max(t['fire'], .8)
                t['trees'] *= .8
                t['grass'] *= .7
                neighbor = min((self.tiles[self.idx(x + dx, y + dy)] for dx, dy in DIRECTIONS),
                               key=lambda n: n['e'] + n['lava'] * .2)
                if neighbor['e'] + neighbor['lava'] * .2 < t['e'] + t['lava'] * .2:
                    outflow = min(t['lava'] * .3, .12)
                    t['lava'] -= outflow
                    if neighbor['e'] > .37:
                        neighbor['lava'] = min(1, neighbor['lava'] + outflow)
                    else:
                        neighbor['e'] = min(1, neighbor['e'] + outflow * .012)

    def step(self):
        self.tick += 1
        self.climate()
        cohort = list(self.organisms)
        perception = self.perception_index()
        observations = [self.observe(o, perception) for o in cohort]
        predictions = self.engine.infer([(o.weights, obs) for o, obs in zip(cohort, observations)])
        occupancy = {}
        for o in cohort:
            occupancy.setdefault(self.idx(o.x, o.y), []).append(o)
        for o, obs, (hidden, probs) in zip(cohort, observations, predictions):
            if o.energy <= 0:
                continue
            o.memory = hidden.copy()
            before = o.energy
            o.age += 1
            o.energy -= .22 * o.size + (.08 if o.kind == 'predator' else 0)
            action = self.rng.choices(range(7), weights=probs)[0]
            guided = False
            if o.kind == 'human' and o.migration_route:
                if not any(town['id'] == o.migration_town for town in self.settlements):
                    o.migration_route = []
                    o.migration_town = 0
                else:
                    target = o.migration_route[0]
                    direction = next((i for i, (dx, dy) in enumerate(DIRECTIONS)
                                      if self.idx(o.x + dx, o.y + dy) == target), None)
                    if direction is None or not .37 < self.tiles[target]['e'] < .88:
                        o.migration_route = []
                        o.migration_town = 0
                    else:
                        action = direction
                        guided = True
            t = self.tiles[self.idx(o.x, o.y)]
            bonus = 0
            moved = hunted = False
            arrived_town = 0
            if action < 4:
                dx, dy = DIRECTIONS[action]
                nx, ny = (o.x + dx) % self.width, (o.y + dy) % self.height
                dest = self.tiles[self.idx(nx, ny)]
                if dest['e'] > .37 and dest['e'] < .88:
                    occupancy[self.idx(o.x, o.y)].remove(o)
                    o.x, o.y = nx, ny
                    occupancy.setdefault(self.idx(nx, ny), []).append(o)
                    o.energy -= .10 * (1 - dest['road'] * .6)
                    if o.kind == 'human':
                        dest['traffic'] = min(1, dest['traffic'] + .015)
                        dest['road'] = max(dest['road'], max(0, dest['traffic'] - .3) * .7)
                    t = dest
                    moved = True
                    if guided:
                        o.migration_route.pop(0)
                        if not o.migration_route:
                            arrived_town = o.migration_town
            elif action == 4:
                if o.kind == 'predator':
                    prey = next((p for p in occupancy.get(self.idx(o.x, o.y), [])
                                 if p.kind == 'grazer' and p.energy > 0), None)
                    if prey:
                        o.energy += min(65, max(0, prey.energy))
                        prey.energy = 0
                        self.hunts += 1
                        hunted = True
                else:
                    eaten = min(t['grass'], .15 * o.size)
                    t['grass'] -= eaten
                    t['litter'] = min(1, t['litter'] + eaten * .12)
                    o.energy += eaten * 65
                    t['f'] = max(.05, t['f'] - eaten * .015)
            elif action == 5 and o.energy > 105 and o.age > 45:
                if self.rng.random() < .3 * o.fertility:
                    eligible = [p for p in occupancy.get(self.idx(o.x, o.y), [])
                                if p is not o and p.kind == o.kind and p.energy > 75 and p.age > 45]
                    mates = [p for p in eligible if compatible_mates(o, p)]
                    self.mate_encounters += len(eligible)
                    self.mate_rejections += len(eligible) - len(mates)
                    mate = self.rng.choice(mates) if mates else None
                    # Solitary asexual births remain possible, but contact with
                    # incompatible adults cannot bypass mating isolation.
                    child = self.spawn(o.kind, o.x, o.y, o, mate) if mates or not eligible else None
                    if child:
                        o.energy -= 58
                        if mate:
                            mate.energy -= 20
                        bonus = 1.8
            elif action == 6 and o.kind == 'human':
                bonus += society.work(self, o, t)
            if t['e'] <= .37:
                o.energy -= 3
            o.energy -= t['fire'] * 8 + max(0, abs(t['temp'] - o.thermal_opt) - .08) * .6
            o.energy = min(160, o.energy)
            if o.age > 1400 / o.size:
                o.energy = 0
            if arrived_town and o.energy > 0:
                o.household = 0
                o.migration_town = 0
                self.event(f"Human {o.id} reached settlement {arrived_town} after migrating.")
            reward = (o.energy - before) / 20 + bonus
            if self.learning and not guided:
                # A hunt pays the move that put the predator on its prey's tile.
                if hunted and o.last_move:
                    old_obs, old_hidden, old_probs, old_action = o.last_move
                    learn(o.weights, old_obs, old_hidden, old_probs, old_action, 1.5)
                    o.updates += 1
                    self.training_steps += 1
                    self.hunt_move_updates += 1
                learn(o.weights, obs, hidden, probs, action, reward - o.baseline)
                o.baseline = .95 * o.baseline + .05 * reward
                o.updates += 1
                self.training_steps += 1
                o.last_move = [obs, hidden, probs, action] if moved and o.kind == 'predator' else None
        dead = [o for o in self.organisms if o.energy <= 0]
        for o in dead:
            t = self.tiles[self.idx(o.x, o.y)]
            t['f'] = min(1, t['f'] + .04)
            if t['e'] > .37:
                t['litter'] = min(1, t['litter'] + .035 * o.size)
        self.deaths += len(dead)
        self.organisms = [o for o in self.organisms if o.energy > 0]
        if self.tick % 20 == 0:
            society.update(self)
        if self.tick % 300 == 0:
            counts = Counter(o.kind for o in self.organisms)
            self.event(f"Census: {counts['human']} humans, {counts['grazer']} grazers, {counts['predator']} predators.")

    def intervene(self, tool, x, y, radius=3, strength=1):
        return apply_power(self, tool, x, y, radius, strength)

    def snapshot(self):
        counts = dict(Counter(o.kind for o in self.organisms))
        ecotypes = {(o.kind, int(o.thermal_opt * 4), int(o.size * 2)) for o in self.organisms}
        mate_types = {(o.kind, min(9, int(o.mate_signal * 10))) for o in self.organisms}
        caravans = []
        for shipment in self.shipments:
            progress = max(0, min(1, (self.tick - shipment['start']) /
                                  max(1, shipment['arrival'] - shipment['start'])))
            index = shipment['path'][int(progress * (len(shipment['path']) - 1))]
            caravans.append({'x': index % self.width, 'y': index // self.width,
                             'from': shipment['from'], 'to': shipment['to'],
                             'food': round(shipment['food'], 2)})
        return {'seed': self.seed, 'tick': self.tick, 'width': self.width, 'height': self.height,
                'geography': self.geography, 'biome': self.biome,
                'weather': {'width': self.weather_width, 'height': self.weather_height,
                            'clouds': [round(value, 3) for value in self.clouds],
                            'wind': weather.wind(self.tick)},
                'tiles': client_tiles(self.tiles),
                'organisms': [{k: v for k, v in asdict(o).items() if k not in ('weights', 'last_move', 'memory', 'migration_route')} for o in self.organisms],
                'settlements': self.settlements, 'households': self.households,
                'caravans': caravans,
                'events': list(self.events),
                'stats': {'population': len(self.organisms), 'counts': counts, 'births': self.births,
                          'deaths': self.deaths, 'training': self.training_steps, 'hunts': self.hunts,
                          'hunt_move_updates': self.hunt_move_updates, 'sexual_births': self.sexual_births,
                          'ecotypes': len(ecotypes), 'households': len(self.households),
                          'mate_types': len(mate_types), 'mate_encounters': self.mate_encounters,
                          'mate_rejections': self.mate_rejections,
                          'caravans': len(self.shipments),
                          'migrants': sum(bool(o.migration_route) for o in self.organisms),
                          'generation': max((o.generation for o in self.organisms), default=0),
                          'cultures': len(set(o.culture for o in self.organisms if o.kind == 'human'))}}

    def save(self, path):
        payload = {'version': self.VERSION, 'seed': self.seed, 'width': self.width, 'height': self.height,
                   'tick': self.tick, 'next_id': self.next_id, 'rng': self.rng.getstate(),
                   'geography': self.geography, 'biome': self.biome,
                   'clouds': self.clouds,
                   'tiles': self.tiles, 'organisms': [asdict(o) for o in self.organisms],
                   'settlements': self.settlements, 'events': list(self.events),
                   'births': self.births, 'deaths': self.deaths, 'training_steps': self.training_steps,
                   'hunts': self.hunts, 'hunt_move_updates': self.hunt_move_updates,
                   'learning': self.learning, 'sexual_births': self.sexual_births,
                   'mate_encounters': self.mate_encounters, 'mate_rejections': self.mate_rejections,
                   'ancestry': list(self.ancestry), 'households': self.households,
                   'shipments': self.shipments,
                   'next_town_id': self.next_town_id, 'next_household_id': self.next_household_id}
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix('.tmp')
        with temporary.open('w') as f:
            json.dump(payload, f, separators=(',', ':'), allow_nan=False)
            f.flush()
            os.fsync(f.fileno())
        temporary.replace(target)

    @classmethod
    def load(cls, path, workers=1, device='cpu'):
        data = json.loads(Path(path).read_text())
        version = data.pop('version')
        if version not in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, cls.VERSION):
            raise ValueError('Unsupported save version')
        if version == 1:
            # Retain old connections, introduce new sensory connections at zero.
            for organism in data['organisms']:
                old = organism['weights']
                if len(old) != 152:
                    raise ValueError('Invalid version 1 policy length')
                organism['weights'] = [value for j in range(HIDDEN)
                    for value in old[j * 12:(j + 1) * 12] + [0.0] * 16] + old[96:]
        elif version < 10:
            for organism in data['organisms']:
                old = organism['weights']
                if len(old) != 216:
                    raise ValueError('Invalid legacy policy length')
                organism['weights'] = [value for j in range(HIDDEN)
                    for value in old[j * 20:(j + 1) * 20] + [0.0] * 8] + old[160:]
        if any(len(o['weights']) != PARAMS for o in data['organisms']):
            raise ValueError('Invalid policy length')
        for tile in data['tiles']:
            tile.setdefault('temp', .57)
            tile.setdefault('grass_seed', tile['grass'])
            tile.setdefault('tree_seed', tile['trees'])
            tile.setdefault('water', 0.0)
            tile.setdefault('sediment', 0.0)
            tile.setdefault('lava', 0.0)
            tile.setdefault('traffic', 0.0)
            tile.setdefault('road', 0.0)
            tile.setdefault('river', 0.0)
            tile.setdefault('nutrient', tile['f'] * .5 if tile['e'] > .37 else 0.0)
            tile.setdefault('litter', (.08 * tile['grass'] + .12 * tile['trees']) if tile['e'] > .37 else 0.0)
            plants.migrate(tile)
        data.setdefault('geography', 'continents')
        data.setdefault('biome', 'mixed')
        data.setdefault('learning', True)
        data.setdefault('hunts', 0)
        data.setdefault('hunt_move_updates', 0)
        data.setdefault('sexual_births', 0)
        data.setdefault('mate_encounters', 0)
        data.setdefault('mate_rejections', 0)
        data.setdefault('ancestry', [])
        data.setdefault('households', [])
        data.setdefault('shipments', [])
        data.setdefault('next_town_id', max((town['id'] for town in data['settlements']), default=0) + 1)
        data.setdefault('next_household_id', 1)
        for town in data['settlements']:
            town.setdefault('wood', 0.0)
            town.setdefault('empty_ticks', 0)
        world = cls(data['seed'], data['width'], data['height'], workers, device, population=0,
                    geography=data['geography'], biome=data['biome'], learning=data['learning'])
        rng = data.pop('rng')
        world.rng.setstate((rng[0], tuple(rng[1]), rng[2]))
        for organism in data['organisms']:
            organism.setdefault('thermal_opt', data['tiles'][organism['y'] * data['width'] + organism['x']]['temp'])
            organism.setdefault('mate_signal', .5)
            organism.setdefault('memory', [0.0] * HIDDEN)
            if organism.get('last_move') and len(organism['last_move'][0]) == 20:
                organism['last_move'][0].extend([0.0] * HIDDEN)
        data['organisms'] = [Organism(**o) for o in data['organisms']]
        data['events'] = deque(data['events'], maxlen=60)
        data['ancestry'] = deque(data['ancestry'], maxlen=50000)
        for key, value in data.items():
            setattr(world, key, value)
        return world
