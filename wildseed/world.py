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
from . import novelty
from . import diversity
from . import geology
from . import society
from . import weather
from . import watershed

from .brain import (BrainEngine, PARAMS, HIDDEN, VALUE_PARAMS, DISCOUNT,
                    learn, predict_value, learn_value)

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
    value_weights: list = field(default_factory=lambda: [0.0] * VALUE_PARAMS)
    pending_credit: list | None = None
    value_updates: int = 0
    reward_ema: float = 0.0
    social_updates: int = 0
    action_counts: list = field(default_factory=lambda: [0] * 7)
    seed_cargo: list = field(default_factory=lambda: [0.0] * 6)


class World:
    VERSION = 26

    def __init__(self, seed=42, width=96, height=64, workers=1, device='cpu', population=250, geography='continents', biome='mixed', learning=True, value_learning=True, navigation_learning=False, social_learning=True):
        if not 16 <= width <= 256 or not 16 <= height <= 256:
            raise ValueError('Dimensions must be between 16 and 256')
        self.seed, self.width, self.height = seed, width, height
        self.geography, self.biome = geography, biome
        self.learning = learning
        self.value_learning = value_learning
        self.navigation_learning = navigation_learning
        self.social_learning = social_learning
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
        self.critic_updates = 0
        self.seed_transferred = 0.0
        self.ore_exposed = 0.0
        self.social_updates = 0
        self.novelty_archive = []
        self.engine = BrainEngine(workers, device)
        self.tiles = self.generate()
        self.water_budget = {'initial': self.water_total(), 'precipitation': 0.0,
                             'climate_exchange': 0.0, 'evaporation': 0.0,
                             'ocean_drain': 0.0, 'terrain_reset': 0.0,
                             'interventions': 0.0}
        self.nutrient_budget = {'initial': self.nutrient_total(),
                                'plant_exchange': 0.0, 'fire_exchange': 0.0,
                                'grazing_exchange': 0.0, 'death_exchange': 0.0,
                                'ocean_export': 0.0, 'terrain_reset': 0.0,
                                'interventions': 0.0}
        self.weather_width, self.weather_height, self.clouds = weather.initialize(seed, width, height)
        for i in range(population):
            self.spawn('human' if i % 8 == 0 else 'predator' if i % 10 == 0 else 'grazer')
        self.event('A new world takes its first breath.')

    def generate(self):
        return generate(self.seed, self.width, self.height, self.geography, self.biome)

    def idx(self, x, y):
        return (y % self.height) * self.width + x % self.width

    def water_total(self):
        return sum(t['m'] + t['water'] + t['lake'] for t in self.tiles)

    def water_balance(self):
        """Represented tile water versus recorded exchanges with external reservoirs."""
        expected = sum(self.water_budget.values())
        actual = self.water_total()
        return {'actual': actual, 'expected': expected, 'residual': actual - expected,
                'fluxes': self.water_budget.copy()}

    def nutrient_total(self):
        return sum(t['nutrient'] + t['litter'] for t in self.tiles)

    def nutrient_balance(self):
        """Audit represented soil pools; biomass/animals remain external exchanges."""
        expected = sum(self.nutrient_budget.values())
        actual = self.nutrient_total()
        return {'actual': actual, 'expected': expected, 'residual': actual - expected,
                'fluxes': self.nutrient_budget.copy()}

    def event(self, text):
        self.events.appendleft({'tick': self.tick, 'text': text})

    def spawn(self, kind, x=None, y=None, parent=None, mate=None):
        if kind not in SPECIES or len(self.organisms) >= self.max_population:
            return None
        if x is None:
            land = [i for i, t in enumerate(self.tiles) if .38 < t['e'] < .75 and t['lake'] < .05]
            if not land:
                return None
            index = self.rng.choice(land)
            x, y = index % self.width, index // self.width
        x, y = x % self.width, y % self.height
        if self.tiles[self.idx(x, y)]['e'] <= .37 or self.tiles[self.idx(x, y)]['lake'] >= .05:
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
                       household=parent.household if parent else 0,
                       value_weights=([max(-4, min(4, (self.rng.choice((a, b)) if mate else a) +
                                                       self.rng.gauss(0, .02)))
                                       for a, b in zip(parent.value_weights,
                                                       mate.value_weights if mate else parent.value_weights)]
                                      if parent else [0.0] * VALUE_PARAMS))
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
                if dest['e'] <= .37 or dest['e'] >= .88 or dest['lake'] >= .05:
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

    @staticmethod
    def navigation_potential(kind, observation):
        """Bounded local cue used to credit a movement, not to choose it."""
        if kind == 'predator':
            return max(observation[3], *observation[8:12])
        return 0.0

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
            previous_moisture = t['m']
            t['m'] = max(0, min(1, t['m'] + .006 * season - .001 + t['trees'] * .0015))
            self.water_budget['climate_exchange'] += t['m'] - previous_moisture
            if t['e'] > .37:
                self.ore_exposed += geology.weather(t)
                t['scar'] = max(0, t['scar'] - .015 - .02 * t['m'])
                t['traffic'] *= .999
                t['road'] = max(0, t['road'] - .00002)
                if t['lake'] >= .05:
                    plants.clear(t)
                    t['fire'] = 0
                else:
                    before_nutrients = t['nutrient'] + t['litter']
                    plants.advance(t, season)
                    self.nutrient_budget['plant_exchange'] += t['nutrient'] + t['litter'] - before_nutrients
                t['f'] = min(1, t['f'] + .0003)
                if t['fire'] > 0:
                    before_nutrients = t['nutrient'] + t['litter']
                    burned = t['grass'] * .4 + t['trees'] * .12 + t['litter'] * .25
                    t['nutrient'] = min(1, t['nutrient'] + burned * .08)
                    t['litter'] *= .75
                    t['grass'] *= .6
                    t['trees'] *= .88
                    t['grass_seed'] *= .9
                    t['tree_seed'] *= .75
                    plants.burn(t)
                    self.nutrient_budget['fire_exchange'] += t['nutrient'] + t['litter'] - before_nutrients
                    t['f'] = min(1, t['f'] + .008)
                    t['scar'] = min(1, t['scar'] + .18 + burned * .25)
                    t['fire'] = max(0, t['fire'] - .12 - t['m'] * .1)
                    if self.rng.random() < .28:
                        dx, dy = self.rng.choice(DIRECTIONS)
                        neighbor = self.tiles[self.idx(x + dx, y + dy)]
                        if neighbor['trees'] > .2 and neighbor['m'] < .6 and neighbor['e'] > .37:
                            neighbor['fire'] = .8
                # Seeds move locally; surface water and lava follow the lowest neighbor.
                dx, dy = self.rng.choice(DIRECTIONS)
                neighbor = self.tiles[self.idx(x + dx, y + dy)]
                if neighbor['e'] > .37 and neighbor['lake'] < .05:
                    plants.disperse(t, neighbor, self.rng)
                self.flow(i, x, y)
            else:
                self.water_budget['terrain_reset'] -= t['water'] + t['lake']
                self.nutrient_budget['terrain_reset'] -= t['nutrient'] + t['litter']
                plants.clear(t)
                t['river'] = 0
                t['scar'] = 0
                t['nutrient'] = t['litter'] = 0
                t['fire'] = t['water'] = t['lake'] = t['lake_cap'] = t['lava'] = t['traffic'] = t['road'] = 0
                deposit = min(t['sediment'], max(0, 1 - t['e']))
                t['sediment'] -= deposit
                t['e'] += deposit

    def flow(self, index, x, y):
        """Move runoff, suspended soil and lava downhill in bounded local amounts."""
        t = self.tiles[index]
        rain = max(0, t['m'] - .48) * .003 * max(.1, .6 + .4 * math.sin(self.tick / 180))
        evaporation = .0004 + .0006 * t['temp']
        runoff = min(max(0.0, t['m']), rain, max(0.0, 1.0 - t['water']))
        t['m'] -= runoff
        t['water'] += runoff
        surface_before, lake_before = t['water'], t['lake']
        t['water'] = max(0, t['water'] - evaporation)
        t['lake'] = max(0.0, t['lake'] - (.00006 + .00014 * t['temp']))
        self.water_budget['evaporation'] += t['water'] - surface_before + t['lake'] - lake_before
        impounded = min(t['water'], max(0.0, t['lake_cap'] - t['lake']))
        t['lake'] += impounded
        t['water'] -= impounded
        if t['water'] > .001 and t['temp'] > .16:
            neighbor = min((self.tiles[self.idx(x + dx, y + dy)] for dx, dy in DIRECTIONS),
                           key=lambda n: n['e'] + n['lake'] + n['water'])
            slope = t['e'] + t['lake'] + t['water'] - (neighbor['e'] + neighbor['lake'] + neighbor['water'])
            if slope > .001:
                before = t['water']
                capacity = max(0.0, 1 - neighbor['water']) if neighbor['e'] > .37 else 1.0
                outflow = min(before, slope * .25, .035, capacity)
                t['water'] -= outflow
                erosion = min(max(0, t['e'] - .05), outflow * max(0, t['e'] - neighbor['e']) * .006)
                t['e'] -= erosion
                self.ore_exposed += geology.expose(t, erosion * 12)
                t['sediment'] += erosion
                carried = t['sediment'] * outflow / before
                t['sediment'] -= carried
                nutrient_capacity = max(0.0, 1 - neighbor['nutrient']) if neighbor['e'] > .37 else 1.0
                dissolved = min(t['nutrient'], outflow * .025, nutrient_capacity)
                t['nutrient'] -= dissolved
                if neighbor['e'] > .37:
                    neighbor['water'] = min(1, neighbor['water'] + outflow)
                    neighbor['sediment'] += carried
                    neighbor['nutrient'] = min(1, neighbor['nutrient'] + dissolved)
                else:
                    self.water_budget['ocean_drain'] -= outflow
                    self.nutrient_budget['ocean_export'] -= dissolved
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

    def finish_credit(self, organism, next_value):
        """Resolve a previous neural choice using its successor state's value."""
        if not self.learning or not self.value_learning or organism.pending_credit is None:
            return
        obs, hidden, probabilities, action, estimate, reward = organism.pending_credit
        future = DISCOUNT * next_value - estimate
        learn_value(organism.value_weights, hidden, reward + future)
        organism.value_updates += 1
        self.critic_updates += 1
        if abs(future) >= .10:
            learn(organism.weights, obs, hidden, probabilities, action, future, rate=.001)
            organism.updates += 1
            self.training_steps += 1
        organism.pending_credit = None

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
            current_value = predict_value(o.value_weights, hidden) if self.value_learning else 0.0
            self.finish_credit(o, current_value)
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
                    if direction is None or not .37 < self.tiles[target]['e'] < .88 or self.tiles[target]['lake'] >= .05:
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
                if dest['e'] > .37 and dest['e'] < .88 and dest['lake'] < .05:
                    occupancy[self.idx(o.x, o.y)].remove(o)
                    o.x, o.y = nx, ny
                    occupancy.setdefault(self.idx(nx, ny), []).append(o)
                    o.energy -= .10 * (1 - dest['road'] * .6)
                    if o.kind == 'human':
                        dest['traffic'] = min(1, dest['traffic'] + .015)
                        dest['road'] = max(dest['road'], max(0, dest['traffic'] - .3) * .7)
                    t = dest
                    moved = True
                    if o.kind in ('grazer', 'human'):
                        self.seed_transferred += plants.deposit_seed_cargo(t, o.seed_cargo)
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
                    before_litter = t['litter']
                    t['litter'] = min(1, t['litter'] + eaten * .12)
                    self.nutrient_budget['grazing_exchange'] += t['litter'] - before_litter
                    o.energy += eaten * 65
                    if eaten > 0 and o.kind in ('grazer', 'human'):
                        plants.collect_seed_cargo(t, o.seed_cargo)
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
            if t['e'] <= .37 or t['lake'] >= .05:
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
            if self.learning and self.navigation_learning and moved and o.kind == 'predator':
                successor = self.observe(o, perception)
                reward += .6 * (self.navigation_potential(o.kind, successor) -
                                 self.navigation_potential(o.kind, obs))
            if not guided:
                o.action_counts[action] += 1
            o.reward_ema = .95 * o.reward_ema + .05 * max(-2, min(2, reward))
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
                if self.value_learning:
                    o.pending_credit = [obs, hidden, probs, action, current_value, reward]
        dead = [o for o in self.organisms if o.energy <= 0]
        for o in dead:
            self.finish_credit(o, 0.0)
            t = self.tiles[self.idx(o.x, o.y)]
            t['f'] = min(1, t['f'] + .04)
            if t['e'] > .37:
                self.seed_transferred += plants.deposit_seed_cargo(t, o.seed_cargo, 1.0)
                before_litter = t['litter']
                t['litter'] = min(1, t['litter'] + .035 * o.size)
                self.nutrient_budget['death_exchange'] += t['litter'] - before_litter
        self.deaths += len(dead)
        self.organisms = [o for o in self.organisms if o.energy > 0]
        if self.tick % 20 == 0:
            society.update(self)
        if self.tick % 300 == 0:
            counts = Counter(o.kind for o in self.organisms)
            self.event(f"Census: {counts['human']} humans, {counts['grazer']} grazers, {counts['predator']} predators.")
        if self.tick % 100 == 0:
            novelty.collect(self)

    def intervene(self, tool, x, y, radius=3, strength=1):
        before = self.water_total()
        nutrients_before = self.nutrient_total()
        result = apply_power(self, tool, x, y, radius, strength)
        self.water_budget['interventions'] += self.water_total() - before
        self.nutrient_budget['interventions'] += self.nutrient_total() - nutrients_before
        return result

    def snapshot(self):
        counts = dict(Counter(o.kind for o in self.organisms))
        behaviors = novelty.diversity(self.organisms)
        lineage = diversity.summarize(self.organisms, self.ancestry)
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
                'organisms': [{k: v for k, v in asdict(o).items() if k not in ('weights', 'last_move', 'memory', 'migration_route', 'value_weights', 'pending_credit')} for o in self.organisms],
                'settlements': self.settlements, 'households': self.households,
                'caravans': caravans,
                'events': list(self.events),
                'novelty_archive': list(self.novelty_archive),
                'diversity': lineage,
                'stats': {'population': len(self.organisms), 'counts': counts, 'births': self.births,
                          'deaths': self.deaths, 'training': self.training_steps, 'hunts': self.hunts,
                          'hunt_move_updates': self.hunt_move_updates, 'sexual_births': self.sexual_births,
                          'ecotypes': len(ecotypes), 'households': len(self.households),
                          'granaries': sum(bool(town.get('granary')) for town in self.settlements),
                          'food_reserves': round(sum(town.get('reserve', 0.0) for town in self.settlements), 2),
                          'tool_designs': sum(bool(town.get('tool_recipe')) for town in self.settlements),
                          'tool_experiments': sum(town.get('experiments', 0) for town in self.settlements),
                          'best_tool_quality': round(max((town.get('tool_quality', 0.0)
                                                          for town in self.settlements), default=0.0), 3),
                          'mate_types': len(mate_types), 'mate_encounters': self.mate_encounters,
                          'mate_rejections': self.mate_rejections,
                          'seed_transferred': round(self.seed_transferred, 3),
                          'ore_exposed': round(self.ore_exposed, 3),
                          'water_budget_residual': round(self.water_balance()['residual'], 8),
                          'nutrient_budget_residual': round(self.nutrient_balance()['residual'], 8),
                          'caravans': len(self.shipments),
                          'migrants': sum(bool(o.migration_route) for o in self.organisms),
                          'critic_updates': self.critic_updates,
                          'social_updates': self.social_updates,
                          'novelty_records': len(self.novelty_archive),
                          'behavior_modes': behaviors['modes'],
                          'behavior_entropy': behaviors['entropy'],
                          'behavior_eligible': behaviors['eligible'],
                          'generation': max((o.generation for o in self.organisms), default=0),
                          'cultures': len(set(o.culture for o in self.organisms if o.kind == 'human'))}}

    def save(self, path):
        payload = {'version': self.VERSION, 'seed': self.seed, 'width': self.width, 'height': self.height,
                   'tick': self.tick, 'next_id': self.next_id, 'rng': self.rng.getstate(),
                   'geography': self.geography, 'biome': self.biome,
                   'clouds': self.clouds,
                   'water_budget': self.water_budget,
                   'nutrient_budget': self.nutrient_budget,
                   'tiles': self.tiles, 'organisms': [asdict(o) for o in self.organisms],
                   'settlements': self.settlements, 'events': list(self.events),
                   'births': self.births, 'deaths': self.deaths, 'training_steps': self.training_steps,
                   'hunts': self.hunts, 'hunt_move_updates': self.hunt_move_updates,
                   'learning': self.learning, 'value_learning': self.value_learning,
                   'navigation_learning': self.navigation_learning,
                   'social_learning': self.social_learning,
                   'sexual_births': self.sexual_births,
                   'mate_encounters': self.mate_encounters, 'mate_rejections': self.mate_rejections,
                   'critic_updates': self.critic_updates,
                   'seed_transferred': self.seed_transferred,
                   'ore_exposed': self.ore_exposed,
                   'social_updates': self.social_updates,
                   'novelty_archive': self.novelty_archive,
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
        if version not in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, cls.VERSION):
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
            tile.setdefault('lake', 0.0)
            tile.setdefault('lake_cap', 0.0)
            tile.setdefault('ore_vein', 0.0)
            tile.setdefault('scar', 0.0)
            tile.setdefault('nutrient', tile['f'] * .5 if tile['e'] > .37 else 0.0)
            tile.setdefault('litter', (.08 * tile['grass'] + .12 * tile['trees']) if tile['e'] > .37 else 0.0)
            plants.migrate(tile)
        data.setdefault('geography', 'continents')
        data.setdefault('biome', 'mixed')
        data.setdefault('learning', True)
        data.setdefault('value_learning', True)
        data.setdefault('navigation_learning', False)
        data.setdefault('social_learning', True)
        data.setdefault('water_budget', {'initial': sum(t['m'] + t['water'] + t['lake'] for t in data['tiles']),
                                         'precipitation': 0.0, 'climate_exchange': 0.0,
                                         'evaporation': 0.0, 'ocean_drain': 0.0,
                                         'terrain_reset': 0.0, 'interventions': 0.0})
        data.setdefault('nutrient_budget', {'initial': sum(t['nutrient'] + t['litter'] for t in data['tiles']),
                                            'plant_exchange': 0.0, 'fire_exchange': 0.0,
                                            'grazing_exchange': 0.0, 'death_exchange': 0.0,
                                            'ocean_export': 0.0, 'terrain_reset': 0.0,
                                            'interventions': 0.0})
        data.setdefault('hunts', 0)
        data.setdefault('hunt_move_updates', 0)
        data.setdefault('sexual_births', 0)
        data.setdefault('mate_encounters', 0)
        data.setdefault('mate_rejections', 0)
        data.setdefault('critic_updates', 0)
        data.setdefault('seed_transferred', 0.0)
        data.setdefault('ore_exposed', 0.0)
        data.setdefault('social_updates', 0)
        data.setdefault('novelty_archive', [])
        data.setdefault('ancestry', [])
        data.setdefault('households', [])
        data.setdefault('shipments', [])
        data.setdefault('next_town_id', max((town['id'] for town in data['settlements']), default=0) + 1)
        data.setdefault('next_household_id', 1)
        for town in data['settlements']:
            town.setdefault('wood', 0.0)
            town.setdefault('empty_ticks', 0)
            town.setdefault('reserve', 0.0)
            town.setdefault('granary', 0)
            if version < 26:
                town.setdefault('tool_recipe', [])
                town.setdefault('tool_quality', 0.0)
                town.setdefault('experiments', 0)
        world = cls(data['seed'], data['width'], data['height'], workers, device, population=0,
                    geography=data['geography'], biome=data['biome'], learning=data['learning'],
                    value_learning=data['value_learning'],
                    navigation_learning=data['navigation_learning'],
                    social_learning=data['social_learning'])
        rng = data.pop('rng')
        world.rng.setstate((rng[0], tuple(rng[1]), rng[2]))
        for organism in data['organisms']:
            organism.setdefault('value_weights', [0.0] * VALUE_PARAMS)
            organism.setdefault('pending_credit', None)
            organism.setdefault('value_updates', 0)
            organism.setdefault('reward_ema', 0.0)
            organism.setdefault('social_updates', 0)
            organism.setdefault('action_counts', [0] * 7)
            organism.setdefault('seed_cargo', [0.0] * 6)
            if len(organism['seed_cargo']) != 6:
                raise ValueError('Invalid seed cargo length')
            if len(organism['action_counts']) != 7:
                raise ValueError('Invalid action history length')
            if len(organism['value_weights']) != VALUE_PARAMS:
                raise ValueError('Invalid value head length')
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
