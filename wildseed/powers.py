"""God interventions with measured, immediate effects on authoritative state."""
from .geography import BIOMES
from . import plants

POWER_INFO = [
 ('raise','↟','Raise land','Land'),('lower','↡','Lower land','Land'),
 ('ocean','≈','Deep ocean','Land'),('mountain','▲','Mountains','Land'),
 ('rain','☂','Rain','Nature'),('drought','☀','Drought','Nature'),
 ('forest','♠','Forest','Nature'),('grass','❧','Meadows','Nature'),
 ('fertile','✿','Fertile soil','Nature'),('minerals','◆','Minerals','Nature'),
 ('freeze','❄','Freeze','Nature'),('heat','♨','Heat','Nature'),
 ('human','♙','Humans','Life'),('grazer','♧','Grazers','Life'),('predator','♜','Predators','Life'),
 ('heal','♡','Heal','Life'),('mutate','✧','Mutate','Life'),('extinction','×','Erase life','Destruction'),
 ('fire','♨','Wildfire','Destruction'),('lightning','ϟ','Lightning','Destruction'),
 ('meteor','☄','Meteor','Destruction'),('volcano','♨','Volcano','Destruction'),
] + [('biome_'+k,'◈',v[0],'Biomes') for k,v in BIOMES.items()]
POWER_IDS = {p[0] for p in POWER_INFO}


def apply(world, tool, x, y, radius=3, strength=1):
    if tool not in POWER_IDS: raise ValueError('Unknown power')
    affected = {}
    for dy in range(-radius,radius+1):
        for dx in range(-radius,radius+1):
            if dx*dx+dy*dy <= radius*radius:
                affected[world.idx(x+dx,y+dy)] = (dx,dy)
    changed = spawned = altered = removed = buildings = 0
    if tool in ('human','grazer','predator'):
        # Spawn only on actual habitable brush cells: water casts report no effect.
        land = [i for i in affected if .37 < world.tiles[i]['e'] < .88]
        if land:
            for _ in range(8*strength):
                index = world.rng.choice(land)
                if world.spawn(tool,index%world.width,index//world.width): spawned += 1
    else:
        for i,(dx,dy) in affected.items():
            t=world.tiles[i]; before=t.copy(); land=t['e']>.37
            if tool=='raise': t['e']=min(.95,t['e']+.055*strength)
            elif tool=='lower': t['e']=max(.05,t['e']-.055*strength)
            elif tool=='ocean': t['e']=.18
            elif tool=='mountain': t['e']=max(t['e'],.76+.1*(1-math_distance(dx,dy)/max(1,radius)))
            elif tool=='rain': t['m']=min(1,t['m']+.3*strength);t['water']=min(1,t['water']+.12*strength);t['fire']=0
            elif tool=='drought': t['m']=max(0,t['m']-.3*strength);t['water']*=.2;t['grass']*=.6
            elif tool=='forest' and land:
                t['trees']=min(1,t['trees']+.4*strength);t['grass']=min(1,t['grass']+.3)
                t['tree_seed']=max(t['tree_seed'],t['trees']);t['grass_seed']=max(t['grass_seed'],t['grass'])
                plants.establish(t,'tree');plants.establish(t,'grass')
            elif tool=='grass' and land:
                t['grass']=min(1,t['grass']+.45*strength);t['grass_seed']=max(t['grass_seed'],t['grass']);plants.establish(t,'grass')
            elif tool=='fertile' and land:
                t['f']=min(1,t['f']+.3*strength)
                t['nutrient']=min(1,t['nutrient']+.3*strength)
            elif tool=='minerals' and land: t['ore']=min(20,t['ore']+2*strength)
            elif tool=='freeze': t['temp']=max(0,t['temp']-.4*strength);t['fire']=0
            elif tool=='heat': t['temp']=min(1,t['temp']+.4*strength);t['m']=max(0,t['m']-.15*strength);t['water']*=.5
            elif tool in ('fire','lightning') and land: t['fire']=1
            elif tool=='meteor': t['e']=max(.05,t['e']-.3*strength);plants.clear(t);t['fire']=1;t['ore']+=strength
            elif tool=='volcano':
                t['e']=min(.95,.65+.25*(1-math_distance(dx,dy)/max(1,radius)))
                t['temp']=1;t['m']=.05;plants.clear(t);t['fire']=1;t['ore']+=strength;t['lava']=min(1,t['lava']+.8)
            elif tool.startswith('biome_') and land:
                temp,moisture,fertility,trees=BIOMES[tool[6:]][1]
                t.update(temp=temp,m=moisture,f=fertility,trees=trees*moisture,grass=moisture*fertility,fire=0)
                t['tree_seed']=t['trees'];t['grass_seed']=t['grass']
                t['nutrient']=fertility*.5;t['litter']=.08*t['grass']+.12*t['trees']
                plants.initialize(t)
            if t['e']<=.37:
                plants.clear(t);t['fire']=t['water']=t['lava']=t['road']=t['traffic']=0
                if land or tool in ('ocean','lower','meteor','volcano'):
                    t['nutrient']=t['litter']=0
            if t!=before: changed+=1
        for o in world.organisms:
            if world.idx(o.x,o.y) not in affected: continue
            if tool=='heal':
                previous=o.energy;o.energy=min(160,o.energy+45*strength);altered+=int(o.energy!=previous)
            elif tool=='mutate':
                o.weights=[max(-4,min(4,w+world.rng.gauss(0,.12*strength))) for w in o.weights]
                o.size=max(.5,min(1.6,o.size+world.rng.gauss(0,.08*strength)))
                o.thermal_opt=max(0,min(1,o.thermal_opt+world.rng.gauss(0,.05*strength)))
                altered+=1
            elif tool in ('extinction','meteor','lightning','volcano'):
                o.energy=0;removed+=1
        if removed:
            world.organisms=[o for o in world.organisms if o.energy>0];world.deaths+=removed
        if tool in ('meteor','volcano'):
            previous=len(world.settlements)
            world.settlements=[s for s in world.settlements if world.idx(s['x'],s['y']) not in affected]
            buildings=previous-len(world.settlements)
            if buildings:
                remaining={s['id'] for s in world.settlements}
                world.households=[home for home in world.households if home['town'] in remaining]
    total=changed+spawned+altered+removed+buildings
    result={'tiles_changed':changed,'spawned':spawned,'organisms_changed':altered,
            'killed':removed,'settlements_removed':buildings,'affected':total}
    world.event(f"{tool.replace('_',' ').title()} at ({x}, {y}): {total} changes.")
    return result


def math_distance(x,y): return (x*x+y*y)**.5
