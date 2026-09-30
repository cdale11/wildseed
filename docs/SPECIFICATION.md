# Implementation specification

## System

One Linux process owns a world; it advances at a fixed logical timestep independently of wall time and connected browsers. A single simulation lock serializes commands, ticks and saves. Background process workers perform pure neural inference; the parent owns learning, mutation and action RNG. Threaded HTTP serves read snapshots and validated commands. This simple initial transport should be replaced or bounded behind a production proxy for larger deployments.

The initial world is a 96×64 periodic grid with elevation, moisture, fertility, grass, trees, ore and fire fields. Scalar waves generate initial geography. Rain-dependent local sediment transfer conserves transferred elevation mass. The biome renderer derives colors and tiny tree sprites from state/coordinates. There are no downloaded assets. The periodic coordinate indexing is not yet matched by periodic initial noise or settlement distance calculations: seams are a known prototype limitation.

## Organisms

Each organism has ID, species, position, energy, age, generation, size, fertility, culture, materials, reward baseline and 152 neural weights. Observations: bias, energy, age, local grass/trees/moisture/fire, season and four adjacent food/water indicators. Network: 12 inputs, 8 tanh hidden units, 7 softmax actions. Actions: four cardinal movements, eat, reproduce, species-dependent work/rest. The action set and network topology are fixed in this version. Predators need richer prey perception in Phase 1.

Training: immediate energy delta and reproduction/construction bonuses feed a bounded advantage against an exponential moving baseline. REINFORCE updates both layers. Weights are clipped to [-4,4]. Children inherit weights plus Gaussian mutation and bounded size/fertility mutations. Inheritance currently includes learned weights (Lamarckian design choice); document future alternatives. Delayed credit, recurrent memory, topology evolution and controlled adaptation experiments remain outstanding.

## Ecology and humans

Vegetation grows from moisture/soil, feeding drains biomass and fertility, death returns nutrients, fire consumes vegetation and enriches soil, and erosion changes land availability. Humans harvest timber and minerals, build settlements after sufficient wood, and gain food near occupied settlements. Culture labels transmit through inheritance and local influence. There is no sophisticated language, politics or civilization intelligence yet.

## Persistence and API

Schema version 1 JSON stores full precision state, neural weights and Python RNG state. Write-to-temporary + fsync + atomic rename protects the last completed save from partial writes. Only trusted server-owned saves are loaded. `/api/state` is a rendering snapshot and is not a save. `/api/command` accepts pause, speed, save, tool. `/health` reports simulation failure. Browser remote access uses a bearer token entered by the user; tokens remain in JS memory and are not put in URLs/storage. Commands reject cross-origin Origin headers and non-JSON bodies. Remote bind requires a 24+ character token. Terminate TLS at a reverse proxy; do not expose this development HTTP server directly to the internet.

## Scaling

0 workers selects process affinity CPUs; inference parallelizes when batches justify overhead. Tiny worlds run scalar inference. All rule application and gradient training currently remain serial, so more workers do not guarantee faster ticks. Optional PyTorch CUDA inference batches distinct policies with bmm; CPU/GPU floating-point differences can change sampled histories. A compute-enabled vGPU must expose CUDA; virtual display adapters cannot substitute. GPU training/vectorized state are roadmap items. The browser only renders and sends commands.
