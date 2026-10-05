"""Local contact transmission with bounded acquired and inherited resistance."""
import math

from . import society


def advance(world, occupancy):
    """Resolve infections after movement, using the authoritative occupancy index."""
    for index, occupants in occupancy.items():
        alive = [organism for organism in occupants if organism.energy > 0]
        if not alive:
            continue
        tile = world.tiles[index]
        if world.tick % 20 == 0 and not any(o.infection > 0 for o in alive):
            # Damp litter is a coarse environmental microbial-exposure proxy.
            susceptible = next((o for o in alive if o.immunity < 1), None)
            risk = (.08 * tile['m'] * tile['litter'] *
                    min(3, len(alive)) * (1 - susceptible.immunity)) if susceptible else 0
            if risk > 0 and world.rng.random() < risk:
                susceptible.infection = .65
                world.infections += 1
                world.spillovers += 1
                world.record_interaction('environmental_pathogen', susceptible.kind)
        pressure = sum(organism.infection for organism in alive)
        if pressure > 0:
            town = society.nearest_town(world, index % world.width, index // world.width, radius=3)
            contact_multiplier = .4 if town and town.get('quarantine_until', 0) > world.tick else 1.0
            for organism in alive:
                if organism.infection > 0 or organism.immunity >= 1:
                    continue
                risk = 1 - math.exp(-.08 * min(5.0, pressure) *
                                    (1 - organism.immunity) * contact_multiplier)
                if world.rng.random() < risk:
                    organism.infection = .65
                    world.infections += 1
                    world.record_interaction('pathogen', organism.kind)
        for organism in alive:
            if organism.infection <= 0:
                continue
            organism.infection = max(0.0, organism.infection - .006 - .004 * organism.immunity)
            if organism.infection == 0:
                organism.immunity = min(1.0, organism.immunity + .12)
