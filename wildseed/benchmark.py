"""Run repeatable full-tick throughput measurement, without browser/HTTP costs."""
import argparse
import json
import platform
import statistics
import time
from .world import World


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--ticks', type=int, default=200)
    p.add_argument('--workers', type=int, default=1)
    p.add_argument('--population', type=int, default=250)
    a = p.parse_args()
    if a.ticks < 1: p.error('ticks must be positive')
    w = World(workers=a.workers, population=a.population)
    times = []
    try:
        for _ in range(a.ticks):
            start = time.perf_counter(); w.step(); times.append(time.perf_counter() - start)
        print(json.dumps({'python':platform.python_version(), 'workers':w.engine.workers,
                          'ticks':a.ticks,'initial_population':a.population,'final_population':len(w.organisms),
                          'median_ms':round(statistics.median(times)*1000,2),
                          'p95_ms':round(sorted(times)[min(len(times)-1,int(len(times)*.95))]*1000,2),
                          'ticks_per_second':round(len(times)/sum(times),2)}, indent=2))
    finally: w.engine.close()

if __name__ == '__main__': main()
