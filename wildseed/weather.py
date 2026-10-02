"""Deterministic coarse cloud advection and terrain-dependent precipitation."""
import math
import random

CELL = 8


def initialize(seed, width, height):
    columns = (width + CELL - 1) // CELL
    rows = (height + CELL - 1) // CELL
    rng = random.Random(seed ^ 0x5A17C10D)
    return columns, rows, [.2 + .5 * rng.random() for _ in range(columns * rows)]


def wind(tick):
    return 1 if math.sin(tick / 240) >= 0 else -1


def advance(world):
    """Move fronts as a simultaneous phase; rain reaches every tile in a cell."""
    columns, rows = world.weather_width, world.weather_height
    direction = wind(world.tick)
    moved = [0.0] * len(world.clouds)
    for cy in range(rows):
        for cx in range(columns):
            index = cy * columns + cx
            traveling = world.clouds[index] * .28
            moved[index] += world.clouds[index] - traveling
            moved[cy * columns + (cx + direction) % columns] += traveling
    updated = []
    for cy in range(rows):
        for cx in range(columns):
            cells = [world.tiles[y * world.width + x]
                     for y in range(cy * CELL, min(world.height, (cy + 1) * CELL))
                     for x in range(cx * CELL, min(world.width, (cx + 1) * CELL))]
            sea = sum(t['e'] <= .37 or t['lake'] >= .05 for t in cells) / len(cells)
            elevation = sum(t['e'] for t in cells) / len(cells)
            moisture = sum(t['m'] for t in cells) / len(cells)
            temperature = sum(t['temp'] for t in cells) / len(cells)
            cloud = min(1.0, moved[cy * columns + cx] + .012 * sea +
                        .003 * (1 - sea) * moisture * temperature)
            rain = max(0.0, cloud - .52) * (.10 + max(0.0, elevation - .58) * .30)
            updated.append(max(0.0, cloud - rain))
            if rain > 0:
                for tile in cells:
                    if tile['e'] > .37:
                        tile['m'] = min(1.0, tile['m'] + rain * .10)
                        tile['water'] = min(1.0, tile['water'] + rain * .035)
                        tile['fire'] = max(0.0, tile['fire'] - rain * .7)
    world.clouds = updated
