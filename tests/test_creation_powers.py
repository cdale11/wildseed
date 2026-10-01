"""End-to-end rule effects, startup semantics and procedural generation contracts."""
import copy
import tempfile
import unittest
from pathlib import Path
from wildseed.geography import generate, GEOGRAPHIES, BIOMES
from wildseed.powers import POWER_IDS
from wildseed.world import World
from wildseed.server import Simulation

class CreationTests(unittest.TestCase):
    def test_all_geographies_and_biomes_generate_bounded_diverse_worlds(self):
        signatures=set()
        for geography in GEOGRAPHIES:
            for biome in ['mixed',*BIOMES]:
                with self.subTest(geography=geography,biome=biome):
                    tiles=generate(123,32,24,geography,biome)
                    self.assertEqual(len(tiles),768)
                    self.assertTrue(any(t['e']>.37 for t in tiles))
                    self.assertTrue(all(0<=t[k]<=1 for t in tiles for k in ('e','temp','m','f','grass','trees','grass_seed','tree_seed')))
                    self.assertTrue(all(t['grass']==t['trees']==0 for t in tiles if t['e']<=.37))
            signatures.add(tuple(round(t['e'],4) for t in tiles))
        self.assertEqual(len(signatures),len(GEOGRAPHIES))
        self.assertEqual(generate(123,32,24),generate(123,32,24))
        self.assertNotEqual(generate(123,32,24),generate(124,32,24))

    def test_fresh_setup_preview_exactness_and_archive(self):
        with tempfile.TemporaryDirectory() as d:
            sim=Simulation(None,Path(d)/'world.json',workers=1)
            self.addCleanup(lambda:sim.world.engine.close() if sim.world else None)
            self.assertIsNone(sim.world)
            # Existing disk saves are preserved, never silently auto-loaded.
            sim.save_path.write_text('previous saved world')
            with self.assertRaises(ValueError):sim.command({'action':'pause','value':True})
            request={'geography':'atoll','biome':'rainforest','size':'small'}
            a=sim.command({'action':'preview',**request});b=sim.command({'action':'preview',**request})
            self.assertNotEqual(a['seed'],b['seed'])
            sim.command({'action':'new_world',**request,'seed':a['seed'],'population':0,'epoch':sim.epoch})
            self.assertEqual(a['tiles'],sim.world.snapshot()['tiles'])
            self.assertEqual(next((Path(d)/'archives').glob('*.json')).read_text(),'previous saved world')
            old_epoch=sim.epoch
            c=sim.command({'action':'preview',**request})
            sim.command({'action':'new_world',**request,'seed':c['seed'],'population':0,'epoch':sim.epoch})
            self.assertNotEqual(old_epoch,sim.epoch)
            self.assertEqual(len(list((Path(d)/'archives').glob('*.json'))),2)
            with self.assertRaises(ValueError):sim.command({'action':'new_world',**request,'seed':c['seed'],'epoch':old_epoch})

class PowersTests(unittest.TestCase):
    def setUp(self):
        self.w=World(width=24,height=20,population=0)
        self.addCleanup(self.w.engine.close)
        for t in self.w.tiles:t.update(e=.55,m=.5,f=.5,grass=.3,trees=.3,ore=.2,temp=.55,fire=0)

    def test_every_power_changes_real_state_and_reports_counts(self):
        for power in sorted(POWER_IDS):
            with self.subTest(power=power):
                for t in self.w.tiles:t.update(e=.55,m=.5,f=.5,grass=.3,trees=.3,ore=.2,temp=.55,fire=0)
                self.w.organisms=[];o=self.w.spawn('human',8,8);o.energy=40
                before=copy.deepcopy(self.w.tiles);weights=o.weights.copy()
                result=self.w.intervene(power,8,8,2,1)
                self.assertGreater(result['affected'],0)
                actual=sum(a!=b for a,b in zip(before,self.w.tiles))
                self.assertEqual(actual,result['tiles_changed'])
                if power=='heal':self.assertGreater(o.energy,40)
                if power=='mutate':self.assertNotEqual(weights,o.weights)
                if power in ('meteor','volcano','lightning','extinction'):self.assertNotIn(o,self.w.organisms)
                if power in ('human','grazer','predator'):self.assertEqual(result['spawned'],8)

    def test_water_and_population_cap_report_noop(self):
        for t in self.w.tiles:t.update(e=.2,trees=0,grass=0,tree_seed=0,grass_seed=0)
        for power in ('human','grazer','predator','forest','grass'):
            self.assertEqual(self.w.intervene(power,8,8)['affected'],0)
        self.w.tiles[self.w.idx(8,8)]['e']=.5;self.w.max_population=0
        self.assertEqual(self.w.intervene('human',8,8)['spawned'],0)

    def test_ocean_clears_vegetation_immediately_and_rain_extinguishes(self):
        self.w.intervene('ocean',8,8,1)
        t=self.w.tiles[self.w.idx(8,8)]
        self.assertEqual((t['trees'],t['grass'],t['fire']),(0,0,0))
        self.w.intervene('volcano',8,8,1);self.assertEqual(t['fire'],1)
        self.w.intervene('rain',8,8,1);self.assertEqual(t['fire'],0)

    def test_brush_and_strength_are_bounded_and_local(self):
        sim=Simulation(self.w,'/unused')
        before=copy.deepcopy(self.w.tiles)
        for bad in ({'radius':11},{'radius':True},{'strength':4},{'strength':0}):
            with self.assertRaises(ValueError):sim.command({'action':'tool','tool':'raise','x':8,'y':8,**bad})
        self.assertEqual(before,self.w.tiles)
        result=sim.command({'action':'tool','tool':'raise','x':8,'y':8,'radius':1,'strength':2})
        self.assertEqual(result['tiles_changed'],5)
        self.assertAlmostEqual(self.w.tiles[self.w.idx(8,8)]['e'],.66)
        self.assertEqual(self.w.tiles[self.w.idx(10,8)],before[self.w.idx(10,8)])

    def test_temperature_brush_changes_growth_not_only_color(self):
        self.w.intervene('freeze',8,8,1,3)
        cold=self.w.tiles[self.w.idx(8,8)]['temp']
        self.assertEqual(cold,0)
        # Match every ecological field except temperature and run the same climate phase.
        i=self.w.idx(8,8);j=self.w.idx(12,8)
        self.w.tiles[j]=self.w.tiles[i].copy();self.w.tiles[j]['temp']=.6
        self.w.tick=i%4
        self.w.climate()
        self.assertGreater(self.w.tiles[j]['grass'],self.w.tiles[i]['grass'])

    def test_v2_save_migrates_climate_without_changing_policies(self):
        import json
        o=self.w.spawn('human',8,8)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'old.json';self.w.save(path)
            data=json.loads(path.read_text());data['version']=2
            data.pop('geography');data.pop('biome')
            for t in data['tiles']:t.pop('temp')
            path.write_text(json.dumps(data))
            migrated=World.load(path);self.addCleanup(migrated.engine.close)
            self.assertEqual(migrated.organisms[0].weights,o.weights)
            self.assertTrue(all(t['temp']==.57 for t in migrated.tiles))
            migrated.step();migrated.save(path)
            self.assertEqual(json.loads(path.read_text())['version'],4)

    def test_v3_save_seeds_existing_vegetation(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'old.json';self.w.save(path)
            data=json.loads(path.read_text());data['version']=3
            for tile in data['tiles']:
                tile.pop('grass_seed');tile.pop('tree_seed')
            path.write_text(json.dumps(data))
            migrated=World.load(path);self.addCleanup(migrated.engine.close)
            self.assertTrue(all(t['grass_seed']==t['grass'] and t['tree_seed']==t['trees'] for t in migrated.tiles))

    def test_seed_dispersal_colonizes_bare_ground_but_not_water(self):
        for t in self.w.tiles:
            t.update(e=.55,m=.8,f=.8,grass=0,trees=0,grass_seed=0,tree_seed=0,fire=0)
        source=self.w.tiles[self.w.idx(8,8)]
        source.update(grass=.8,trees=.7,grass_seed=.8,tree_seed=.7)
        water=self.w.tiles[self.w.idx(8,9)];water['e']=.2
        for _ in range(40):
            self.w.tick+=1;self.w.climate()
        neighbors=[self.w.tiles[self.w.idx(8+dx,8+dy)] for dx,dy in ((1,0),(-1,0),(0,-1))]
        self.assertTrue(any(t['grass_seed']>0 and t['tree_seed']>0 for t in neighbors))
        self.assertEqual((water['grass_seed'],water['tree_seed']), (0,0))
        self.assertTrue(any(t['grass']>0 and t['trees']>0 for t in neighbors))
