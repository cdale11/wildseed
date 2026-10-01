"""Exercise the bounded HTTP transport locally without leaving a server running."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
import statistics
import threading
import time
import urllib.error
import urllib.request

from .server import BoundedHTTPServer, Simulation, handler_for
from .world import World


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--requests', type=int, default=200)
    parser.add_argument('--concurrency', type=int, default=32)
    parser.add_argument('--connections', type=int, default=16)
    args = parser.parse_args()
    if not 1 <= args.requests <= 5000 or not 1 <= args.concurrency <= 256 or not 1 <= args.connections <= 256:
        parser.error('requests, concurrency and connections must be positive and bounded')
    world = World(42, 32, 24, workers=1, population=80)
    simulation = Simulation(world, '/unused', token='local-load-test-token')
    handler = handler_for(simulation)
    handler.log_message = lambda *_args: None
    server = BoundedHTTPServer(('127.0.0.1', 0), handler, max_connections=args.connections)
    serving = threading.Thread(target=server.serve_forever, daemon=True)
    serving.start()
    url = f'http://127.0.0.1:{server.server_port}/api/state'

    def request(_index):
        start = time.perf_counter()
        req = urllib.request.Request(url, headers={'Authorization': 'Bearer local-load-test-token'})
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                response.read()
                code = response.status
        except urllib.error.HTTPError as error:
            code = error.code
        except OSError:
            code = 'network_error'
        return code, (time.perf_counter() - start) * 1000

    try:
        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
            results = list(pool.map(request, range(args.requests)))
        elapsed = time.perf_counter() - start
    finally:
        server.shutdown()
        serving.join()
        server.server_close()
        world.engine.close()
    latencies = sorted(latency for _, latency in results)
    print(json.dumps({'requests': args.requests, 'concurrency': args.concurrency,
                      'connection_limit': args.connections,
                      'statuses': dict(Counter(str(code) for code, _ in results)),
                      'median_ms': round(statistics.median(latencies), 2),
                      'p95_ms': round(latencies[min(len(latencies)-1, int(len(latencies)*.95))], 2),
                      'requests_per_second': round(args.requests / elapsed, 2)}, indent=2))


if __name__ == '__main__':
    main()
