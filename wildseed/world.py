"""Seeded ecology with mutable terrain, individual policies and settlements."""
from collections import Counter, deque
from dataclasses import asdict, dataclass
import json
import math
import os
from pathlib import Path
import random

from .brain import BrainEngine, PARAMS, HIDDEN, learn

SPECIES = ('grazer', 'predator', 'human')
DIRECTIONS = ((0, -1), (1, 0), (0, 1), (-1, 0))


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


class World:
    VERSION = 2

    def __init__(self, seed=42, width=96, height=64, workers=1, device='cpu', population=250):
        if not 16 <= width <= 256 or not 16 <= height <= 256:
            raise ValueError('Dimensions must be between 16 and 256')
        self.seed, self.width, self.height = seed, width, height
        self.rng = random.Random(seed)
        self.tick = 0
        self.next_id = 1
        self.max_population = 2500
        self.events = deque(maxlen=60)
        self.organisms = []
        self.settlements = []
        self.births = self.deaths = self.training_steps = 0
        self.engine = BrainEngine(workers, device)
        self.tiles = self.generate()
        for i in range(population):
            self.spawn('human' if i % 8 == 0 else 'predator' if i % 10 == 0 else 'grazer')
        self.event('A new world takes its first breath.')

    def generate(self):
        phases = [self.rng.random() * math.tau for _ in range(8)]
        tiles = []
        for y in range(self.height):
            for x in range(self.width):
                nx, ny = x / self.width, y / self.height
                waves = sum(math.sin(nx * (i + 1) * 6 + phases[i]) *
                            math.cos(ny * (i + 1) * 5 + phases[7 - i]) / (i + 1)
                            for i in range(5))
                elevation = 0.49 + waves * .22 - .25 * ((nx - .5)**2 + (ny - .5)**2)
                moisture = max(.05, min(1, .5 + .3 * math.sin(nx * 11 + phases[5]) + .15 * math.cos(ny * 15)))
                land = elevation > .37
                tiles.append({'e': elevation, 'm': moisture, 'f': .65,
                              'grass': self.rng.random() * moisture if land else 0,
                              'trees': self.rng.random() * moisture if land and elevation < .72 else 0,
                              'ore': max(0, elevation - .52) * 10, 'fire': 0.0})
        return tiles

    def idx(self, x, y):
        return (y % self.height) * self.width + x % self.width

    def event(self, text):
        self.events.appendleft({'tick': self.tick, 'text': text})

    def spawn(self, kind, x=None, y=None, parent=None):
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
        weights = ([max(-4, min(4, w + self.rng.gauss(0, .045))) for w in parent.weights]
                   if parent else [self.rng.gauss(0, .25) for _ in range(PARAMS)])
        org = Organism(self.next_id, kind, x, y, 55 if parent else 85, 0,
                       parent.generation + 1 if parent else 0,
                       max(.5, min(1.6, parent.size + self.rng.gauss(0, .04))) if parent else 1,
                       max(.5, min(1.6, parent.fertility + self.rng.gauss(0, .04))) if parent else 1,
                       weights, culture=parent.culture if parent else (self.next_id % 5 + 1 if kind == 'human' else 0))
        self.next_id += 1
        self.organisms.append(org)
        if parent:
            self.births += 1
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
                t['m'], t['fire'], math.sin(self.tick / 180), *food, *danger, *materials]

    def climate(self):
        season = math.sin(self.tick / 180)
        # Staggered tile updates distribute climate work across ticks.
        for i in range(self.tick % 4, len(self.tiles), 4):
            t = self.tiles[i]
            x, y = i % self.width, i // self.width
            t['m'] = max(0, min(1, t['m'] + .006 * season - .001 + t['trees'] * .0015))
            if t['e'] > .37:
                growth = .028 * t['m'] * t['f'] * (.7 + .3 * season)
                t['grass'] = min(1, t['grass'] + growth * (1 - t['trees'] * .4))
                t['trees'] = min(1, t['trees'] + .0025 * t['m'] * t['f'])
                t['f'] = min(1, t['f'] + .0003)
                if t['fire'] > 0:
                    t['grass'] *= .6
                    t['trees'] *= .88
                    t['f'] = min(1, t['f'] + .008)
                    t['fire'] = max(0, t['fire'] - .12 - t['m'] * .1)
                    if self.rng.random() < .28:
                        dx, dy = self.rng.choice(DIRECTIONS)
                        neighbor = self.tiles[self.idx(x + dx, y + dy)]
                        if neighbor['trees'] > .2 and neighbor['m'] < .6 and neighbor['e'] > .37:
                            neighbor['fire'] = .8
                # Rain erodes slopes, deposits material downhill; coastlines change.
                dx, dy = self.rng.choice(DIRECTIONS)
                neighbor = self.tiles[self.idx(x + dx, y + dy)]
                sediment = max(0, t['e'] - neighbor['e'] - .025) * .001 * t['m']
                t['e'] -= sediment
                neighbor['e'] += sediment
            else:
                t['grass'] = t['trees'] = t['fire'] = 0

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
            before = o.energy
            o.age += 1
            o.energy -= .22 * o.size + (.08 if o.kind == 'predator' else 0)
            action = self.rng.choices(range(7), weights=probs)[0]
            t = self.tiles[self.idx(o.x, o.y)]
            bonus = 0
            if action < 4:
                dx, dy = DIRECTIONS[action]
                nx, ny = (o.x + dx) % self.width, (o.y + dy) % self.height
                dest = self.tiles[self.idx(nx, ny)]
                if dest['e'] > .37 and dest['e'] < .88:
                    occupancy[self.idx(o.x, o.y)].remove(o)
                    o.x, o.y = nx, ny
                    occupancy.setdefault(self.idx(nx, ny), []).append(o)
                    o.energy -= .10
                    t = dest
            elif action == 4:
                if o.kind == 'predator':
                    prey = next((p for p in occupancy.get(self.idx(o.x, o.y), [])
                                 if p.kind == 'grazer' and p.energy > 0), None)
                    if prey:
                        o.energy += min(65, max(0, prey.energy))
                        prey.energy = 0
                else:
                    eaten = min(t['grass'], .15 * o.size)
                    t['grass'] -= eaten
                    o.energy += eaten * 65
                    t['f'] = max(.05, t['f'] - eaten * .015)
            elif action == 5 and o.energy > 105 and o.age > 45:
                if self.rng.random() < .3 * o.fertility:
                    child = self.spawn(o.kind, o.x, o.y, o)
                    if child:
                        o.energy -= 58
                        bonus = 1.8
            elif action == 6 and o.kind == 'human':
                harvest = min(.035, t['trees'])
                t['trees'] -= harvest
                o.wood += harvest * 10
                mined = min(.03, t['ore'])
                t['ore'] -= mined
                o.ore += mined
                o.energy -= .1
                # Accumulated material becomes persistent shelters and farms.
                if o.wood >= 2.5:
                    town = next((s for s in self.settlements if
                                 abs(s['x'] - o.x) + abs(s['y'] - o.y) <= 5), None)
                    if town is None:
                        town = {'id': len(self.settlements) + 1, 'x': o.x, 'y': o.y,
                                'culture': o.culture, 'houses': 0, 'stock': 0, 'ore': 0,
                                'population': 0, 'age': 0}
                        self.settlements.append(town)
                        self.event(f"Culture {o.culture} founded settlement {town['id']}.")
                    town['houses'] += 1
                    town['stock'] += 3
                    town['ore'] += o.ore
                    o.ore = 0
                    o.wood -= 2.5
                    bonus += .8
            if t['e'] <= .37:
                o.energy -= 3
            o.energy -= t['fire'] * 8
            o.energy = min(160, o.energy)
            if o.age > 1400 / o.size:
                o.energy = 0
            reward = (o.energy - before) / 20 + bonus
            learn(o.weights, obs, hidden, probs, action, reward - o.baseline)
            o.baseline = .95 * o.baseline + .05 * reward
            o.updates += 1
            self.training_steps += 1
        dead = [o for o in self.organisms if o.energy <= 0]
        for o in dead:
            t = self.tiles[self.idx(o.x, o.y)]
            t['f'] = min(1, t['f'] + .04)
        self.deaths += len(dead)
        self.organisms = [o for o in self.organisms if o.energy > 0]
        if self.tick % 20 == 0:
            humans = [o for o in self.organisms if o.kind == 'human']
            for s in self.settlements:
                residents = [o for o in humans if abs(o.x - s['x']) + abs(o.y - s['y']) <= 6]
                s['population'] = len(residents)
                s['age'] += 20
                tile = self.tiles[self.idx(s['x'], s['y'])]
                if tile['e'] > .37 and tile['fire'] == 0:
                    s['stock'] = min(100, s['stock'] + len(residents) * tile['m'] * .3)
                for o in residents:
                    ration = min(s['stock'], .8)
                    s['stock'] -= ration
                    o.energy = min(160, o.energy + ration * 3)
                    if self.rng.random() < .05:
                        o.culture = s['culture']
        if self.tick % 300 == 0:
            counts = Counter(o.kind for o in self.organisms)
            self.event(f"Census: {counts['human']} humans, {counts['grazer']} grazers, {counts['predator']} predators.")

    def intervene(self, tool, x, y, radius=3):
        if tool in SPECIES:
            for _ in range(8):
                self.spawn(tool, x + self.rng.randint(-radius, radius), y + self.rng.randint(-radius, radius))
        else:
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx * dx + dy * dy > radius * radius:
                        continue
                    t = self.tiles[self.idx(x + dx, y + dy)]
                    if tool == 'raise': t['e'] = min(.95, t['e'] + .055)
                    elif tool == 'lower': t['e'] = max(.05, t['e'] - .055)
                    elif tool == 'rain': t['m'] = min(1, t['m'] + .3); t['fire'] = 0
                    elif tool == 'forest' and t['e'] > .37: t['trees'] = min(1, t['trees'] + .4); t['grass'] = min(1, t['grass'] + .3)
                    elif tool == 'fire' and t['e'] > .37: t['fire'] = 1
        self.event(f'{tool.capitalize()} at ({x}, {y}).')

    def snapshot(self):
        counts = dict(Counter(o.kind for o in self.organisms))
        return {'seed': self.seed, 'tick': self.tick, 'width': self.width, 'height': self.height,
                'tiles': [[round(t[k], 3) for k in ('e', 'm', 'grass', 'trees', 'ore', 'fire', 'f')] for t in self.tiles],
                'organisms': [{k: v for k, v in asdict(o).items() if k != 'weights'} for o in self.organisms],
                'settlements': self.settlements, 'events': list(self.events),
                'stats': {'population': len(self.organisms), 'counts': counts, 'births': self.births,
                          'deaths': self.deaths, 'training': self.training_steps,
                          'generation': max((o.generation for o in self.organisms), default=0),
                          'cultures': len(set(o.culture for o in self.organisms if o.kind == 'human'))}}

    def save(self, path):
        payload = {'version': self.VERSION, 'seed': self.seed, 'width': self.width, 'height': self.height,
                   'tick': self.tick, 'next_id': self.next_id, 'rng': self.rng.getstate(),
                   'tiles': self.tiles, 'organisms': [asdict(o) for o in self.organisms],
                   'settlements': self.settlements, 'events': list(self.events),
                   'births': self.births, 'deaths': self.deaths, 'training_steps': self.training_steps}
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
        if version not in (1, cls.VERSION):
            raise ValueError('Unsupported save version')
        if version == 1:
            # Retain old connections, introduce new sensory connections at zero.
            for organism in data['organisms']:
                old = organism['weights']
                if len(old) != 152:
                    raise ValueError('Invalid version 1 policy length')
                organism['weights'] = [value for j in range(HIDDEN)
                    for value in old[j * 12:(j + 1) * 12] + [0.0] * 8] + old[96:]
        if any(len(o['weights']) != PARAMS for o in data['organisms']):
            raise ValueError('Invalid policy length')
        world = cls(data['seed'], data['width'], data['height'], workers, device, population=0)
        rng = data.pop('rng')
        world.rng.setstate((rng[0], tuple(rng[1]), rng[2]))
        data['organisms'] = [Organism(**o) for o in data['organisms']]
        data['events'] = deque(data['events'], maxlen=60)
        for key, value in data.items():
            setattr(world, key, value)
        return world
