"""Authoritative single-world server. Browser clients never advance simulation."""
import argparse
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import secrets
import shutil
import signal
from pathlib import Path
import threading
import time
from urllib.parse import urlsplit
from .world import World
from .geography import generate, options, GEOGRAPHIES, BIOMES, SIZES, BIOME_NAMES, classify
from .powers import POWER_IDS, POWER_INFO

WEB = Path(__file__).resolve().parent.parent / 'web'
TOOLS = POWER_IDS


class Simulation:
    def __init__(self, world, save_path, token='', workers=0, device='cpu'):
        self.world, self.save_path, self.token = world, save_path, token
        self.workers, self.device = workers, device
        self.previews = {}
        self.epoch = secrets.token_hex(8)
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.paused = False
        self.speed = 1
        self.ms = 0
        self.error = None

    def run(self):
        last_save = time.monotonic()
        try:
            while not self.stop.is_set():
                start = time.monotonic()
                with self.lock:
                    if self.world is not None and not self.paused:
                        self.world.step()
                    self.ms = (time.monotonic() - start) * 1000
                    if self.world is not None and time.monotonic() - last_save >= 60:
                        self.world.save(self.save_path)
                        last_save = time.monotonic()
                self.stop.wait(max(.001, 1 / (8 * self.speed) - (time.monotonic() - start)))
        except Exception as exc:
            self.error = str(exc)
            self.stop.set()
            raise

    def command(self, data):
        if not isinstance(data, dict):
            raise ValueError('Expected an object')
        action = data.get('action')
        with self.lock:
            if action in ('preview', 'new_world'):
                config = {key: data.get(key, default) for key,default in
                          (('geography','continents'),('biome','mixed'),('size','standard'))}
                if any(not isinstance(v,str) for v in config.values()):
                    raise ValueError('Invalid world options')
                if config['geography'] not in GEOGRAPHIES or config['biome'] not in {*BIOMES,'mixed'} or config['size'] not in SIZES:
                    raise ValueError('Unknown world options')
                width,height = SIZES[config['size']]
                if action == 'preview':
                    seed=secrets.randbits(32)
                    self.previews[seed]=config
                    if len(self.previews)>16: self.previews.pop(next(iter(self.previews)))
                    tiles=generate(seed,width,height,config['geography'],config['biome'])
                    return {'seed':seed,'width':width,'height':height,**config,
                            'tiles':[[round(t[k],3) for k in ('e','m','grass','trees','ore','fire','f','temp')]+[BIOME_NAMES.index(classify(t))] for t in tiles]}
                seed=data.get('seed')
                if type(seed) is not int or self.previews.get(seed)!=config:
                    raise ValueError('Preview this world before creating it')
                if data.get('epoch')!=self.epoch:
                    raise ValueError('The shared world changed. Refresh before replacing it.')
                population=data.get('population',250)
                if type(population) is not int or population not in (0,100,250,500):
                    raise ValueError('Invalid starting population')
                new=World(seed,width,height,self.workers,self.device,population,config['geography'],config['biome'])
                old=self.world
                try:
                    if old:
                        archive=Path(self.save_path).parent/'archives'/f'{old.seed}-{old.tick}-{time.time_ns()}.json'
                        old.save(archive)
                    elif Path(self.save_path).exists():
                        archive=Path(self.save_path).parent/'archives'/f'previous-{time.time_ns()}.json'
                        archive.parent.mkdir(parents=True,exist_ok=True)
                        shutil.copy2(self.save_path,archive)
                except Exception:
                    new.engine.close()
                    raise
                self.world=new;self.paused=False;self.epoch=secrets.token_hex(8);self.previews.clear()
                if old: old.engine.close()
                return {'seed':seed,'epoch':self.epoch}
            if self.world is None:
                raise ValueError('Choose a world first')
            if action == 'pause':
                if type(data.get('value')) is not bool:
                    raise ValueError('Pause value must be boolean')
                self.paused = data['value']
            elif action == 'speed':
                if type(data.get('value')) is not int or data['value'] not in (1, 2, 4):
                    raise ValueError('Speed must be 1, 2 or 4')
                self.speed = data['value']
            elif action == 'save':
                self.world.save(self.save_path)
            elif action == 'tool':
                tool, x, y = data.get('tool'), data.get('x'), data.get('y')
                if not isinstance(tool, str) or tool not in TOOLS:
                    raise ValueError('Unknown tool')
                if type(x) is not int or type(y) is not int or not (0 <= x < self.world.width and 0 <= y < self.world.height):
                    raise ValueError('Invalid coordinates')
                radius,strength=data.get('radius',3),data.get('strength',1)
                if type(radius) is not int or not 1<=radius<=10 or type(strength) is not int or not 1<=strength<=3:
                    raise ValueError('Invalid brush radius or strength')
                return self.world.intervene(tool, x, y, radius, strength)
            else:
                raise ValueError('Unknown action')


def handler_for(sim):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def reply(self, code, data, content='application/json'):
            body = json.dumps(data, separators=(',', ':')).encode() if content == 'application/json' else data
            self.send_response(code)
            self.send_header('Content-Type', content)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def authenticated(self):
            return not sim.token or hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + sim.token)

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == '/health':
                self.reply(503 if sim.error else 200, {'ok': not bool(sim.error)})
            elif path == '/api/state':
                if not self.authenticated():
                    return self.reply(401, {'error': 'Enter the server access token'})
                with sim.lock:
                    state = sim.world.snapshot() if sim.world else {}
                    state.update(setup_required=sim.world is None, epoch=sim.epoch, options=options(),
                                 powers=[{'id':p[0],'icon':p[1],'name':p[2],'group':p[3]} for p in POWER_INFO])
                    state['runtime'] = {'paused': sim.paused, 'speed': sim.speed, 'tick_ms': round(sim.ms, 2),
                                        'workers': sim.world.engine.workers if sim.world else sim.workers, 'device': sim.device,
                                        'error': sim.error}
                self.reply(200, state)
            elif path in ('/', '/app.js', '/renderer.js', '/style.css'):
                file = WEB / ('index.html' if path == '/' else path[1:])
                mime = 'text/html' if path == '/' else 'text/javascript' if path.endswith('.js') else 'text/css'
                self.reply(200, file.read_bytes(), mime + '; charset=utf-8')
            else:
                self.reply(404, {'error': 'Not found'})

        def do_POST(self):
            if urlsplit(self.path).path != '/api/command':
                return self.reply(404, {'error': 'Not found'})
            if not self.authenticated():
                return self.reply(401, {'error': 'Unauthorized'})
            # Reject cross-origin browser commands, including localhost CSRF.
            origin = self.headers.get('Origin')
            if origin and urlsplit(origin).netloc != self.headers.get('Host'):
                return self.reply(403, {'error': 'Cross-origin commands are not allowed'})
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                return self.reply(415, {'error': 'Use application/json'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 4096:
                    raise ValueError('Invalid body size')
                result = sim.command(json.loads(self.rfile.read(length)))
            except (ValueError, TypeError, UnicodeError) as exc:
                return self.reply(400, {'error': str(exc)})
            except (OSError, RuntimeError, ImportError) as exc:
                return self.reply(503, {'error': f'World operation failed: {exc}'})
            self.reply(200, {'ok': True, 'result': result})

        def log_message(self, format, *args):
            if args and str(args[1]) not in ('200',):
                super().log_message(format, *args)
    return Handler


def main():
    parser = argparse.ArgumentParser(description='Wildseed headless simulation server')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--load', help='Explicitly resume a saved world; default is fresh world selection')
    parser.add_argument('--workers', type=int, default=0, help='0 = all available CPUs')
    parser.add_argument('--device', choices=('cpu', 'cuda'), default='cpu')
    parser.add_argument('--save', default='data/world.json')
    args = parser.parse_args()
    if args.workers < 0:
        parser.error('workers must be nonnegative')
    token = os.environ.get('WILDSEED_TOKEN', '')
    if args.host not in ('127.0.0.1', 'localhost', '::1') and len(token) < 24:
        parser.error('Remote binding requires WILDSEED_TOKEN of at least 24 characters')
    world = World.load(args.load, args.workers, args.device) if args.load else None
    sim = Simulation(world, args.save, token, args.workers, args.device)
    server = ThreadingHTTPServer((args.host, args.port), handler_for(sim))
    worker = threading.Thread(target=sim.run, daemon=True)
    worker.start()
    def terminate(_signum, _frame):
        # serve_forever's shutdown must run outside its main serving thread.
        threading.Thread(target=server.shutdown, daemon=True).start()
    previous_sigterm = signal.signal(signal.SIGTERM, terminate)
    print(f"Wildseed: http://{args.host}:{args.port} | {args.workers or 'auto'} CPU workers | {args.device}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        signal.signal(signal.SIGTERM, previous_sigterm)
        sim.stop.set()
        worker.join()
        with sim.lock:
            if sim.world: sim.world.save(args.save)
        server.server_close()
        if sim.world: sim.world.engine.close()


if __name__ == '__main__':
    main()
