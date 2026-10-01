# Wildseed

A server-authoritative, procedural god simulation inspired by the sandbox genre. Original code and procedural visuals; no WorldBox assets or code.

**Status: runnable early prototype, not a complete WorldBox replacement.** Organisms have individual neural policies that learn during play and mutate through inheritance. Ecosystems can collapse; sustained open-ended evolution and sophisticated civilizations are research goals, not implemented guarantees.

## Run

Python 3.11+; no dependencies for CPU mode. From this repository:

```sh
python3 -m wildseed.server
```

Open http://127.0.0.1:8080. The headless server advances the world independently of clients. CPU workers default to the process's available CPU affinity. For a small machine or debugging, use `--workers 1`. Saves are written every minute to `data/world.json` but are **not automatically loaded on restart**. Startup opens world selection with a fresh random preview. Use `--load data/world.json` only when explicitly resuming an old world. Ctrl+C saves before exit.

```sh
python3 -m unittest discover -s tests -v
python3 -m wildseed.benchmark --ticks 200 --workers 1
python3 -m wildseed.branch data/world.json data/control.json --ticks 100
python3 -m wildseed.backup data/world.json /mnt/wildseed-backups
```

## Play

Start by choosing one of eight geography styles and nine biome/climate choices, then reroll until you like the random landscape. Choose small, standard or large size and an empty or populated world. Create starts the exact previewed seed. Browser refresh/reconnection joins the running shared world rather than resetting everyone.

Select a power category and click the map. Thirty powers include terrain sculpting, oceans, mountains, rain/drought, vegetation, fertility, minerals, freeze/heat, life spawning, healing, neural mutation, extinction, wildfire, lightning, meteors, volcanoes and eight biome brushes. Brush radius (1–10) and strength (1–3) are adjustable. Every cast reports actual effect counts or explicitly reports no effect. Drag to pan; scroll to zoom; Fit world resets the camera. Inspect displays organisms' traits and learning counts. Map layers show moisture, food, minerals, and fertility. Pause/speed affect the shared server world. Save world persists state, policies, and RNG state. The browser polls at 2 Hz; the server targets 8 ticks/second at 1× speed.

## What exists

- Procedural map selection, biome palettes, shaded relief, coast foam, species sprites and forest textures.
- Seeded terrain, coastlines, erosion/deposition, seasonal moisture, vegetation growth, soil depletion, fire spread and ash fertility.
- Species-specific, three-tile directional perception of food/prey, threats/fire and human building resources, with terrain occlusion.
- Grass and tree cohorts with inherited climate preferences, local seed dispersal and competition; bounded soil nutrient/litter recycling, local runoff, sediment transport and cooling lava.
- Grazers, predators and humans with energy, age, optional two-parent reproduction, ancestry, inherited traits and independently learned neural weights.
- A recurrent 28→8→7 neural policy per organism; online one-step policy-gradient training with eight hidden-state memory values. No pretrained model or external AI API is needed.
- Households, scarcity-driven jobs, houses, traffic-made roads and route-based barter caravans. These remain early society mechanics.
- Server persistence, CPU process inference, optional CUDA batch inference, administrator/spectator access, bounded HTTP connections and thin canvas clients.
- Reproducible save branches with optional interventions and experiment manifests; see [experiments](docs/EXPERIMENTS.md).

## What does not exist yet

Dynamic neural topology, aquatic species, diseases, language, technology invention, diplomacy, war, watershed hydrology, large-scale distributed simulation and measured sustained emergence are not implemented. Current action/observation spaces are fixed. Plants are represented as local cohorts, not individual organisms. Training is CPU-side even with CUDA inference. See [ROADMAP.md](ROADMAP.md) and [specification](docs/SPECIFICATION.md).

## Linux deployment

See [deployment guide](docs/DEPLOYMENT.md). A compute-capable virtual GPU can use CUDA if the host exposes a compatible device and drivers. A display-only virtual GPU does not provide CUDA compute. CPU mode always works without GPU packages. GPU parity/performance have not been tested on hardware in the development environment.

## Development

Work on `main` per the project owner's instruction. Read [CODEX.md](CODEX.md) before changes. Keep [CHANGELOG.md](CHANGELOG.md), [ROADMAP.md](ROADMAP.md), and [mistakes.md](mistakes.md) current. Do not represent roadmap items as shipped features.
