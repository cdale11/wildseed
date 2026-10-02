"""Slow exposure of finite subsurface ore by weathering and erosion."""


def expose(tile, requested):
    """Transfer ore from a hidden vein to accessible surface stock."""
    amount = min(max(0.0, requested), max(0.0, tile['ore_vein']),
                 max(0.0, 20.0 - tile['ore']))
    tile['ore_vein'] -= amount
    tile['ore'] += amount
    return amount


def weather(tile):
    """Moisture and thermal cycling slowly reveal ore on exposed land."""
    if tile['e'] <= .37 or tile['lake'] >= .05:
        return 0.0
    amount = .0004 * (.25 + .75 * tile['m']) * (.6 + abs(tile['temp'] - .5))
    return expose(tile, amount)
