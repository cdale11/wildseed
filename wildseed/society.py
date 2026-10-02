"""Local human households, occupations and settlement resource use."""
import heapq
from . import craft


def distance(world, x, y, a, b):
    dx = abs(x - a)
    dy = abs(y - b)
    return min(dx, world.width - dx) + min(dy, world.height - dy)


def nearest_town(world, x, y, radius=6):
    candidates = [town for town in world.settlements
                  if distance(world, x, y, town['x'], town['y']) <= radius]
    return min(candidates, key=lambda town: (distance(world, x, y, town['x'], town['y']), town['id'])) if candidates else None


def work(world, organism, tile):
    town = nearest_town(world, organism.x, organism.y)
    organism.energy -= .1
    if town is None:
        timber = min(.035, tile['trees'])
        tile['trees'] -= timber
        organism.wood += timber * 10
        mineral = min(.03, tile['ore'])
        tile['ore'] -= mineral
        organism.ore += mineral
        if organism.wood < 2.5:
            return 0
        town = {'id': world.next_town_id, 'x': organism.x, 'y': organism.y,
                'culture': organism.culture, 'houses': 1, 'stock': 3,
                'wood': 0, 'ore': organism.ore, 'reserve': 0.0, 'granary': 0,
                'tool_recipe': [], 'tool_quality': 0.0, 'experiments': 0,
                'grievance': 0,
                'population': 0, 'age': 0,
                'empty_ticks': 0}
        world.next_town_id += 1
        world.settlements.append(town)
        organism.wood -= 2.5
        organism.ore = 0
        world.event(f"Culture {organism.culture} founded settlement {town['id']}.")
        return .8

    job = organism.occupation
    if job == 'inventor':
        return craft.propose(world, town)
    if job == 'farmer':
        harvest = min(tile['grass'], .12 * craft.productivity(town))
        tile['grass'] -= harvest
        tile['f'] = max(.05, tile['f'] - harvest * .01)
        town['stock'] = min(200, town['stock'] + harvest * 22)
        return harvest * .4
    if job == 'woodcutter':
        harvest = min(tile['trees'], .05 * craft.productivity(town))
        tile['trees'] -= harvest
        town['wood'] = min(100, town['wood'] + harvest * 10)
        return harvest * .5
    if job == 'miner':
        harvest = min(tile['ore'], .05 * craft.productivity(town))
        tile['ore'] -= harvest
        town['ore'] = min(100, town['ore'] + harvest)
        return harvest * .3
    if job == 'builder' and town['wood'] >= 2.5:
        town['wood'] -= 2.5
        town['houses'] += 1
        tile['road'] = min(1, tile['road'] + .15)
        return .8
    # Unassigned people still gather materials for a future job.
    timber = min(.02, tile['trees'])
    tile['trees'] -= timber
    town['wood'] = min(100, town['wood'] + timber * 10)
    return 0


def assign_jobs(world, town, residents):
    tile = world.tiles[world.idx(town['x'], town['y'])]
    counts = {'farmer': 0, 'woodcutter': 0, 'miner': 0, 'builder': 0, 'inventor': 0}
    for organism in sorted(residents, key=lambda o: o.id):
        demand = {
            'farmer': max(2, 22 - town['stock']) * max(.1, tile['grass']) / (1 + counts['farmer']),
            'woodcutter': max(1, 8 - town['wood']) * max(.1, tile['trees']) / (1 + counts['woodcutter']),
            'miner': max(.2, 3 - town['ore']) * max(.1, tile['ore']) / (1 + counts['miner']),
            'builder': (4 if town['wood'] >= 2.5 and town['houses'] < max(2, len(residents) / 3) else .05)
                       / (1 + counts['builder']),
            'inventor': (2.0 if town['stock'] > 12 and town['wood'] >= 2 and town['ore'] >= .3
                         else 0.0) / (1 + counts['inventor']),
        }
        organism.occupation = max(demand, key=demand.get)
        counts[organism.occupation] += 1


def share_learned_behavior(world, residents):
    """Let humans weakly imitate a successful local peer of their culture."""
    if not world.learning or not world.social_learning:
        return
    cultures = {}
    for organism in residents:
        cultures.setdefault(organism.culture, []).append(organism)
    for group in cultures.values():
        if len(group) < 2:
            continue
        mentor = max(group, key=lambda o: (o.reward_ema, -o.id))
        if mentor.updates < 10:
            continue
        policy = mentor.weights.copy()
        value = mentor.value_weights.copy()
        for learner in group:
            if learner is mentor or mentor.reward_ema - learner.reward_ema < .05:
                continue
            learner.weights = [max(-4, min(4, .98 * old + .02 * model))
                               for old, model in zip(learner.weights, policy)]
            learner.value_weights = [max(-4, min(4, .98 * old + .02 * model))
                                     for old, model in zip(learner.value_weights, value)]
            learner.pending_credit = None
            learner.last_move = None
            learner.social_updates += 1
            world.social_updates += 1


def update(world):
    deliver_shipments(world)
    humans = [organism for organism in world.organisms if organism.kind == 'human']
    residents_by_town = {}
    homes_used = set()
    abandoned = set()
    for town in world.settlements:
        residents = [organism for organism in humans
                     if nearest_town(world, organism.x, organism.y) is town]
        residents_by_town[town['id']] = residents
        town['population'] = len(residents)
        town['age'] += 20
        town['empty_ticks'] = 0 if residents else town.get('empty_ticks', 0) + 20
        manage_granary(world, town, residents)
        if not residents:
            town['stock'] *= .9
            if town['empty_ticks'] >= 100 and town['empty_ticks'] % 100 == 0:
                town['houses'] = max(0, town['houses'] - 1)
            if town['empty_ticks'] >= 200 and town['houses'] == 0:
                abandoned.add(town['id'])
                world.event(f"Settlement {town['id']} was abandoned and decayed.")
                continue
        assign_jobs(world, town, residents)
        share_learned_behavior(world, residents)
        households = [home for home in world.households if home['town'] == town['id']]
        members = {home['id']: [] for home in households}
        for organism in residents:
            if organism.household in members:
                members[organism.household].append(organism)
        for organism in residents:
            if organism.household in members:
                continue
            home = next((h for h in households if len(members[h['id']]) < 4), None)
            if home is None and len(households) < town['houses']:
                home = {'id': world.next_household_id, 'town': town['id'],
                        'head': organism.id, 'food': 0.0, 'wood': 0.0}
                world.next_household_id += 1
                world.households.append(home)
                households.append(home)
                members[home['id']] = []
            if home:
                organism.household = home['id']
                members[home['id']].append(organism)
        for home in households:
            group = members[home['id']]
            if not group:
                continue
            homes_used.add(home['id'])
            if home['head'] not in {organism.id for organism in group}:
                home['head'] = group[0].id
            ration = min(town['stock'], len(group) * .8)
            town['stock'] -= ration
            home['food'] = min(20, home['food'] + ration)
            for organism in group:
                eaten = min(home['food'], .8)
                home['food'] -= eaten
                organism.energy = min(160, organism.energy + eaten * 3)
                if world.rng.random() < .05:
                    organism.culture = town['culture']
    # Abandoned homes retain a short food reserve, then decay with their town.
    if abandoned:
        world.settlements = [town for town in world.settlements if town['id'] not in abandoned]
        world.relations = {key: value for key, value in world.relations.items()
                           if not ({int(part) for part in key.split(':')} & abandoned)}
    world.households = [home for home in world.households if home['id'] in homes_used and home['town'] not in abandoned]
    plan_migration(world, residents_by_town)
    dispatch_trade(world)
    dispatch_raid(world, residents_by_town)


def adjust_relation(world, first, second, amount):
    key = f'{min(first, second)}:{max(first, second)}'
    world.relations[key] = max(-1.0, min(1.0, world.relations.get(key, 0.0) + amount))


def relation(world, first, second):
    return world.relations.get(f'{min(first, second)}:{max(first, second)}', 0.0)


def dispatch_raid(world, residents_by_town):
    """Sustained shortage can send one costly, route-bound food raid."""
    if len(world.shipments) >= 16:
        return
    for source in sorted(world.settlements, key=lambda town: town['id']):
        residents = [o for o in residents_by_town.get(source['id'], [])
                     if o.energy > 30 and not o.migration_route]
        if len(residents) < 2 or source['stock'] + source.get('reserve', 0) >= max(2, .8 * len(residents)):
            source['grievance'] = max(0, source.get('grievance', 0) - 1)
            continue
        choices = []
        for target in world.settlements:
            if (target is source or target.get('culture') == source.get('culture') or
                    target['stock'] <= max(4, 1.5 * target.get('population', 0)) or
                    distance(world, source['x'], source['y'], target['x'], target['y']) > 16):
                continue
            choices.append((-target['stock'],
                            distance(world, source['x'], source['y'], target['x'], target['y']),
                            target['id'], target))
        if not choices:
            source['grievance'] = max(0, source.get('grievance', 0) - 1)
            continue
        source['grievance'] = min(5, source.get('grievance', 0) + 1)
        if source['grievance'] < 3:
            continue
        route = next(((target, path) for _, _, _, target in sorted(choices)
                      if (path := land_route(world, source, target)) and len(path) <= 17), None)
        if route is None:
            source['grievance'] = 2
            continue
        target, path = route
        raiders = sorted(residents, key=lambda o: (-o.energy, o.id))[:3]
        for raider in raiders:
            raider.energy -= 8
        source['grievance'] = 0
        world.shipments.append({'kind': 'raid', 'from': source['id'], 'to': target['id'],
                                'food': 0.0, 'ore': 0.0, 'wood': 0.0,
                                'start': world.tick, 'arrival': world.tick + max(20, len(path) * 2),
                                'path': path, 'raiders': [o.id for o in raiders]})
        world.raids_launched += 1
        adjust_relation(world, source['id'], target['id'], -.1)
        world.event(f"Settlement {source['id']} sent a food raid toward settlement {target['id']}.")
        return


def manage_granary(world, town, residents):
    """Build a communal food store from local surplus and release it in shortages."""
    town.setdefault('reserve', 0.0)
    town.setdefault('granary', 0)
    if not residents:
        town['reserve'] *= .9
        return
    population = len(residents)
    if not town['granary'] and town['wood'] >= 2 and town['stock'] >= max(12, 4 * population):
        town['wood'] -= 2
        town['granary'] = 1
        world.event(f"Settlement {town['id']} built a communal granary from its surplus.")
    if not town['granary']:
        return
    town['reserve'] *= .998
    if town['stock'] > 2 * population + 8:
        stored = min(2.0, max(0.0, 40.0 - town['reserve']),
                     town['stock'] - (2 * population + 8))
        town['stock'] -= stored
        town['reserve'] += stored
    elif town['stock'] < .8 * population:
        released = min(town['reserve'], .8 * population - town['stock'])
        town['reserve'] -= released
        town['stock'] += released


def plan_migration(world, residents_by_town):
    """Send at most one resident per hungry town toward reachable spare capacity."""
    incoming = {town['id']: sum(o.migration_town == town['id']
                                for o in world.organisms) for town in world.settlements}
    for source in world.settlements:
        residents = residents_by_town.get(source['id'], [])
        if not residents or source['stock'] + source.get('reserve', 0.0) >= max(2.0, .8 * len(residents)):
            continue
        if world.tiles[world.idx(source['x'], source['y'])]['grass'] >= .18:
            continue
        travelers = [o for o in residents if o.energy > 35 and not o.migration_route]
        if not travelers:
            continue
        traveler = min(travelers, key=lambda o: (o.energy, o.id))
        choices = []
        for target in world.settlements:
            if target is source:
                continue
            expected = target['population'] + incoming[target['id']]
            if (target['houses'] * 4 <= expected or
                    target['stock'] <= max(8.0, 2.0 * (expected + 1)) or
                    distance(world, traveler.x, traveler.y, target['x'], target['y']) > 24):
                continue
            route = land_route(world, {'x': traveler.x, 'y': traveler.y}, target)
            if route and 1 < len(route) <= 25:
                score = target['stock'] / (expected + 1) - .15 * (len(route) - 1)
                choices.append((-score, len(route), target['id'], route))
        if choices:
            _, _, destination, route = min(choices)
            traveler.migration_town = destination
            traveler.migration_route = route[1:]
            incoming[destination] += 1
            world.event(f"Human {traveler.id} left settlement {source['id']} for settlement {destination} as food ran short.")


def land_route(world, start, goal):
    """Shortest passable periodic route, biased toward existing roads."""
    origin = world.idx(start['x'], start['y'])
    destination = world.idx(goal['x'], goal['y'])
    if any(not .37 < world.tiles[index]['e'] < .88 or world.tiles[index]['lake'] >= .05
           for index in (origin, destination)):
        return None
    queue = [(0.0, origin)]
    best = {origin: 0.0}
    parent = {}
    while queue:
        cost, current = heapq.heappop(queue)
        if cost != best[current]:
            continue
        if current == destination:
            path = [current]
            while current != origin:
                current = parent[current]
                path.append(current)
            return list(reversed(path))
        x, y = current % world.width, current // world.width
        for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            neighbor = world.idx(x + dx, y + dy)
            tile = world.tiles[neighbor]
            if not .37 < tile['e'] < .88 or tile['lake'] >= .05:
                continue
            new_cost = cost + 1 - tile['road'] * .4
            if new_cost < best.get(neighbor, float('inf')):
                best[neighbor] = new_cost
                parent[neighbor] = current
                heapq.heappush(queue, (new_cost, neighbor))
    return None


def dispatch_trade(world):
    if len(world.shipments) >= 16:
        return
    candidates = []
    for source in world.settlements:
        if source['stock'] <= 30:
            continue
        for target in world.settlements:
            if source is target or target['stock'] >= 10:
                continue
            if relation(world, source['id'], target['id']) <= -.5:
                continue
            if target['ore'] < .5 and target['wood'] < 2:
                continue
            candidates.append((distance(world, source['x'], source['y'], target['x'], target['y']),
                               source['id'], target['id'], source, target))
    for _, _, _, source, target in sorted(candidates):
        path = land_route(world, source, target)
        if not path:
            continue
        food = min(5.0, source['stock'] - 25)
        ore = min(1.0, target['ore']) if target['ore'] >= .5 else 0.0
        wood = min(2.0, target['wood']) if ore == 0 else 0.0
        source['stock'] -= food
        target['ore'] -= ore
        target['wood'] -= wood
        for index in path:
            tile = world.tiles[index]
            tile['traffic'] = min(1, tile['traffic'] + .04)
            tile['road'] = max(tile['road'], max(0, tile['traffic'] - .3) * .7)
        average_road = sum(world.tiles[index]['road'] for index in path) / len(path)
        travel = max(20, int(len(path) * 2 * (1 - average_road * .5)))
        world.shipments.append({'kind': 'trade', 'from': source['id'], 'to': target['id'], 'food': food,
                                'ore': ore, 'wood': wood, 'start': world.tick,
                                'arrival': world.tick + travel, 'path': path,
                                'tool_recipe': list(source.get('tool_recipe', [])),
                                'tool_quality': source.get('tool_quality', 0.0)})
        world.event(f"Settlements {source['id']} and {target['id']} sent a barter caravan.")
        return


def deliver_shipments(world):
    towns = {town['id']: town for town in world.settlements}
    traveling = []
    for shipment in world.shipments:
        if shipment['arrival'] > world.tick:
            traveling.append(shipment)
            continue
        source = towns.get(shipment['from'])
        target = towns.get(shipment['to'])
        if shipment.get('kind') == 'raid':
            if source and target:
                alive = sum(any(o.id == identifier and o.energy > 0 for o in world.organisms)
                            for identifier in shipment['raiders'])
                if alive and world.rng.random() < max(.2, min(.85, .5 + .08 * (alive - target.get('population', 0)))):
                    stolen = min(6.0, target['stock'] * .5, max(0.0, 200 - source['stock']))
                    target['stock'] -= stolen
                    source['stock'] += stolen
                    world.raids_succeeded += 1
                    adjust_relation(world, source['id'], target['id'], -.2)
                    world.event(f"Raiders from settlement {source['id']} took {stolen:.1f} food from settlement {target['id']}.")
                else:
                    world.event(f"The raid from settlement {source['id']} against settlement {target['id']} failed.")
            else:
                world.event('A raid was lost when its settlement disappeared.')
            continue
        if source and target:
            target['stock'] = min(200, target['stock'] + shipment['food'])
            source['ore'] = min(100, source['ore'] + shipment['ore'])
            source['wood'] = min(100, source['wood'] + shipment['wood'])
            if shipment.get('tool_quality', 0.0) > target.get('tool_quality', 0.0) + .015:
                target['tool_quality'] = shipment['tool_quality']
                target['tool_recipe'] = list(shipment['tool_recipe'])
                world.event(f"Settlement {target['id']} learned a tool design from traders.")
            adjust_relation(world, source['id'], target['id'], .08)
            world.event(f"Caravan reached settlement {target['id']} with food and returned materials.")
        else:
            world.event('A caravan was lost when its settlement disappeared.')
    world.shipments = traveling
