"""Local contact transmission with bounded acquired and inherited resistance."""
import math


def advance(world, occupancy):
    """Resolve infections after movement, using the authoritative occupancy index."""
    for occupants in occupancy.values():
        alive = [organism for organism in occupants if organism.energy > 0]
        pressure = sum(organism.infection for organism in alive)
        if pressure > 0:
            for organism in alive:
                if organism.infection > 0 or organism.immunity >= 1:
                    continue
                risk = 1 - math.exp(-.08 * min(5.0, pressure) * (1 - organism.immunity))
                if world.rng.random() < risk:
                    organism.infection = .65
                    world.infections += 1
        for organism in alive:
            if organism.infection <= 0:
                continue
            organism.infection = max(0.0, organism.infection - .006 - .004 * organism.immunity)
            if organism.infection == 0:
                organism.immunity = min(1.0, organism.immunity + .12)
