"""Periodic lowest-spill drainage and bounded catchment-fed river channels."""
import heapq


def drainage(tiles, width, height, with_spill=False):
    """Return a forest of routes to ocean outlets in upstream-to-downstream order."""
    count = len(tiles)
    cost = [float('inf')] * count
    parent = [-1] * count
    heap = []
    for index, tile in enumerate(tiles):
        if tile['e'] <= .37:
            cost[index] = 0.0
            heapq.heappush(heap, (0.0, index))
    downstream_first = []
    while heap:
        spill, index = heapq.heappop(heap)
        if spill != cost[index]:
            continue
        downstream_first.append(index)
        x, y = index % width, index // width
        for nx, ny in (((x + 1) % width, y), ((x - 1) % width, y),
                       (x, (y + 1) % height), (x, (y - 1) % height)):
            neighbor = ny * width + nx
            if tiles[neighbor]['e'] <= .37:
                continue
            proposed = max(spill, tiles[neighbor]['e']) + .0000001
            if proposed < cost[neighbor]:
                cost[neighbor] = proposed
                parent[neighbor] = index
                heapq.heappush(heap, (proposed, neighbor))
    return (parent, downstream_first, cost) if with_spill else (parent, downstream_first)


def basin_capacity(tile, spill):
    """Water depth available below a basin's lowest ocean outlet."""
    if tile['e'] <= .37:
        return 0.0
    if spill == float('inf'):
        # A completely landlocked periodic world has no ocean outlet. Retain
        # deliberately carved basin capacity rather than draining it away.
        return min(.16, tile.get('lake_cap', 0.0))
    depth = min(.16, max(0.0, spill - tile['e']))
    return depth if depth >= .015 else 0.0


def seed_lakes(tiles, width, height):
    """Give fresh-world basins a climate-dependent initial water level."""
    _, _, spill = drainage(tiles, width, height, with_spill=True)
    for tile, outlet in zip(tiles, spill):
        tile['lake_cap'] = basin_capacity(tile, outlet)
        tile['lake'] = tile['lake_cap'] * (.35 + .5 * tile['m'])


def advance(world):
    parent, downstream_first, spill = drainage(world.tiles, world.width, world.height, with_spill=True)
    flow = [0.0] * len(world.tiles)
    for index, tile in enumerate(world.tiles):
        if tile['e'] > .37:
            x, y = index % world.width, index // world.width
            cloud = world.clouds[(y // 8) * world.weather_width + (x // 8)]
            flow[index] = max(0.0, tile['m'] - .25) * (.4 + .6 * cloud) + tile['water'] * .5
    for index in reversed(downstream_first):
        if parent[index] >= 0:
            flow[parent[index]] += flow[index]
    for index, tile in enumerate(world.tiles):
        capacity = basin_capacity(tile, spill[index])
        tile['water'] = min(1.0, tile['water'] + max(0.0, tile['lake'] - capacity))
        tile['lake_cap'] = capacity
        tile['lake'] = min(tile['lake'], capacity)
        strength = min(1.0, max(0.0, (flow[index] - 5.0) / 60.0)) if parent[index] >= 0 else 0.0
        tile['river'] = strength
        if strength > 0:
            tile['water'] = min(1.0, tile['water'] + strength * .005)
            erosion = min(max(0.0, tile['e'] - .38), strength * .0005)
            tile['e'] -= erosion
            tile['sediment'] += erosion
