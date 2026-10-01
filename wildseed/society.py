"""Local human households, occupations and settlement resource use."""


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
                'wood': 0, 'ore': organism.ore, 'population': 0, 'age': 0}
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
    humans = [organism for organism in world.organisms if organism.kind == 'human']
    homes_used = set()
    for town in world.settlements:
        residents = [organism for organism in humans
                     if nearest_town(world, organism.x, organism.y) is town]
        town['population'] = len(residents)
        town['age'] += 20
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
    world.households = [home for home in world.households if home['id'] in homes_used]
