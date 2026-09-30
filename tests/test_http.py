import json
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from wildseed.server import Simulation, handler_for
from wildseed.world import World

class HttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.world = World(width=16, height=16, population=5)
        self.sim = Simulation(self.world, Path(self.temp.name)/'world.json', 'test-secret')
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), handler_for(self.sim))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = 'http://127.0.0.1:' + str(self.server.server_port)

    def tearDown(self):
        self.server.shutdown(); self.thread.join(); self.server.server_close()
        self.world.engine.close(); self.temp.cleanup()

    def request(self, path, data=None, token='test-secret', origin=None):
        headers={'Authorization':'Bearer '+token, 'Content-Type':'application/json'}
        if origin: headers['Origin']=origin
        req=urllib.request.Request(self.url+path, data=json.dumps(data).encode() if data is not None else None, headers=headers)
        try:
            with urllib.request.urlopen(req) as r: return r.status, r.read()
        except urllib.error.HTTPError as e: return e.code, e.read()

    def test_authentication_and_static_allowlist(self):
        self.assertEqual(self.request('/api/state', token='wrong')[0],401)
        self.assertEqual(self.request('/api/state')[0],200)
        self.assertEqual(self.request('/../wildseed/server.py')[0],404)
        self.assertEqual(self.request('/')[0],200)

    def test_cross_origin_and_save(self):
        self.assertEqual(self.request('/api/command', {'action':'pause','value':True}, origin='https://other.example')[0],403)
        self.assertFalse(self.sim.paused)
        self.assertEqual(self.request('/api/command', {'action':'pause','value':True})[0],200)
        self.assertTrue(self.sim.paused)
        self.assertEqual(self.request('/api/command', {'action':'save'})[0],200)
        self.assertTrue(self.sim.save_path.exists())
