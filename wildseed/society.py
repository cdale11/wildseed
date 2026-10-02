"""Local human households, occupations and settlement resource use."""
import heapq


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
                'wood': 0, 'ore': organism.ore, 'population': 0, 'age': 0,
                'empty_ticks': 0}
        world.next_town_id += 1
        world.settlements.append(town)
        organism.wood -= 2.5
        organism.ore = 0
        world.event(f"Culture {organism.culture} founded settlement {town['id']}.")
        return .8

    job = organism.occupation
    if job == 'farmer':
        harvest = min(tile['grass'], .12)
        tile['grass'] -= harvest
        tile['f'] = max(.05, tile['f'] - harvest * .01)
        town['stock'] = min(200, town['stock'] + harvest * 22)
        return harvest * .4
    if job == 'woodcutter':
        harvest = min(tile['trees'], .05)
        tile['trees'] -= harvest
        town['wood'] = min(100, town['wood'] + harvest * 10)
        return harvest * .5
    if job == 'miner':
        harvest = min(tile['ore'], .05)
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
    counts = {'farmer': 0, 'woodcutter': 0, 'miner': 0, 'builder': 0}
    for organism in sorted(residents, key=lambda o: o.id):
        demand = {
            'farmer': max(2, 22 - town['stock']) * max(.1, tile['grass']) / (1 + counts['farmer']),
            'woodcutter': max(1, 8 - town['wood']) * max(.1, tile['trees']) / (1 + counts['woodcutter']),
            'miner': max(.2, 3 - town['ore']) * max(.1, tile['ore']) / (1 + counts['miner']),
            'builder': (4 if town['wood'] >= 2.5 and town['houses'] < max(2, len(residents) / 3) else .05)
                       / (1 + counts['builder']),
        }
        organism.occupation = max(demand, key=demand.get)
        counts[organism.occupation] += 1


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
        if not residents:
            town['stock'] *= .9
            if town['empty_ticks'] >= 100 and town['empty_ticks'] % 100 == 0:
                town['houses'] = max(0, town['houses'] - 1)
            if town['empty_ticks'] >= 200 and town['houses'] == 0:
                abandoned.add(town['id'])
                world.event(f"Settlement {town['id']} was abandoned and decayed.")
                continue
        assign_jobs(world, town, residents)
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
    world.households = [home for home in world.households if home['id'] in homes_used and home['town'] not in abandoned]
    plan_migration(world, residents_by_town)
    dispatch_trade(world)


def plan_migration(world, residents_by_town):
    """Send at most one resident per hungry town toward reachable spare capacity."""
    incoming = {town['id']: sum(o.migration_town == town['id']
                                for o in world.organisms) for town in world.settlements}
    for source in world.settlements:
        residents = residents_by_town.get(source['id'], [])
        if not residents or source['stock'] >= max(2.0, .8 * len(residents)):
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
    if any(not .37 < world.tiles[index]['e'] < .88 for index in (origin, destination)):
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
            if not .37 < tile['e'] < .88:
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
        world.shipments.append({'from': source['id'], 'to': target['id'], 'food': food,
                                'ore': ore, 'wood': wood, 'start': world.tick,
                                'arrival': world.tick + travel, 'path': path})
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
        if source and target:
            target['stock'] = min(200, target['stock'] + shipment['food'])
            source['ore'] = min(100, source['ore'] + shipment['ore'])
            source['wood'] = min(100, source['wood'] + shipment['wood'])
            world.event(f"Caravan reached settlement {target['id']} with food and returned materials.")
        else:
            world.event('A caravan was lost when its settlement disappeared.')
    world.shipments = traveling
