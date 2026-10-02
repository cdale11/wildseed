"""Periodic lowest-spill drainage and bounded catchment-fed river channels."""
import heapq


def drainage(tiles, width, height):
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
    return parent, downstream_first


def advance(world):
    parent, downstream_first = drainage(world.tiles, world.width, world.height)
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
        strength = min(1.0, max(0.0, (flow[index] - 5.0) / 60.0)) if parent[index] >= 0 else 0.0
        tile['river'] = strength
        if strength > 0:
            tile['water'] = min(1.0, tile['water'] + strength * .005)
            erosion = min(max(0.0, tile['e'] - .38), strength * .0005)
            tile['e'] -= erosion
            tile['sediment'] += erosion
