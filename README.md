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
```

## Play

Start by choosing one of eight geography styles and nine biome/climate choices, then reroll until you like the random landscape. Choose small, standard or large size and an empty or populated world. Create starts the exact previewed seed. Browser refresh/reconnection joins the running shared world rather than resetting everyone.

Select a power category and click the map. Thirty powers include terrain sculpting, oceans, mountains, rain/drought, vegetation, fertility, minerals, freeze/heat, life spawning, healing, neural mutation, extinction, wildfire, lightning, meteors, volcanoes and eight biome brushes. Brush radius (1–10) and strength (1–3) are adjustable. Every cast reports actual effect counts or explicitly reports no effect. Drag to pan; scroll to zoom; Fit world resets the camera. Inspect displays organisms' traits and learning counts. Map layers show moisture, food, minerals, and fertility. Pause/speed affect the shared server world. Save world persists state, policies, and RNG state. The browser polls at 2 Hz; the server targets 8 ticks/second at 1× speed.

## What exists

- Procedural map selection, biome palettes, shaded relief, coast foam, species sprites and forest textures.
- Seeded terrain, coastlines, erosion/deposition, seasonal moisture, vegetation growth, soil depletion, fire spread and ash fertility.
- Species-specific, three-tile directional perception of food/prey, threats/fire and human building resources, with terrain occlusion.
- Grazers, predators and humans with energy, age, reproduction, inherited size/fertility, and independently learned neural weights.
- A 20→8→7 neural policy per organism; online policy gradients through both layers with a moving reward baseline. This is actual training, not a scripted decision tree. No pretrained model or external AI API is needed.
- Human harvesting/mining, material accumulation, shelters, local food stocks, rudimentary farming and culture labels. These are settlement mechanics, not yet a deep civilization model.
- Server persistence, CPU process inference, optional CUDA batch inference, thin canvas clients and token-protected remote operation.

## What does not exist yet

Dynamic neural topology, recurrent memory, explicit plant genomes, aquatic species, sexual reproduction, diseases, language, technology invention, diplomacy, trade networks, war, full geography/hydrology, large-scale distributed simulation, and measured sustained emergence are not implemented. Current action/observation spaces are fixed. Plants are aggregate tile fields. Training is CPU-side even with CUDA inference. See [ROADMAP.md](ROADMAP.md) and [specification](docs/SPECIFICATION.md).

## Linux deployment

See [deployment guide](docs/DEPLOYMENT.md). A compute-capable virtual GPU can use CUDA if the host exposes a compatible device and drivers. A display-only virtual GPU does not provide CUDA compute. CPU mode always works without GPU packages. GPU parity/performance have not been tested on hardware in the development environment.

## Development

Work on `main` per the project owner's instruction. Read [CODEX.md](CODEX.md) before changes. Keep [CHANGELOG.md](CHANGELOG.md), [ROADMAP.md](ROADMAP.md), and [mistakes.md](mistakes.md) current. Do not represent roadmap items as shipped features.
