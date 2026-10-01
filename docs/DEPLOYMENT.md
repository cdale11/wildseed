# Headless Linux deployment

## CPU container

Install Docker/Compose on the future server, clone this repository, and set an access token in the shell (do not commit it):

```sh
export WILDSEED_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
# Optional read-only spectator access:
export WILDSEED_VIEW_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
docker compose up --build -d
```

The host port binds to 127.0.0.1:8080. Reach it through an SSH tunnel (`ssh -L 8080:127.0.0.1:8080 your-server`) or a TLS reverse proxy. Enter the administrator token to create worlds and cast powers, or the optional spectator token to watch. The named volume stores data/world.json. Maintain independent backups. Graceful Ctrl+C and SIGTERM save the current world before exit. Abrupt termination or power loss can lose changes since the last minute's autosave.

## Native Linux

```sh
python3 -m wildseed.server --host 127.0.0.1 --workers 0
```

If binding a non-loopback interface, set WILDSEED_TOKEN (at least 24 characters). WILDSEED_VIEW_TOKEN is optional, distinct and at least 24 characters. The server caps active connections at 64 and API requests per peer at 120 per ten seconds; `/api/metrics` requires the administrator token. Use a firewall and authenticated TLS proxy for remote browser access. Enforce connection/request limits at that proxy too. This stdlib server is intended for private deployments, not untrusted public multi-tenant hosting.

Run the local transport load check with `python3 -m wildseed.loadtest --requests 200 --concurrency 32 --connections 16`. It starts and stops its own loopback server.

## Optional compute GPU

Install a compatible PyTorch build for the host's drivers using the official PyTorch installation guidance. Then run:

```sh
python3 -m wildseed.server --device cuda --workers 0
```

CUDA inference is optional. Training/rules remain CPU-side. If CUDA is unavailable, explicit CUDA selection fails rather than pretending to accelerate. A cloud vGPU needs a compute-capable profile, host drivers and device exposure; a software display GPU will not work. The CPU Docker image does not include PyTorch or configure GPU passthrough. Hardware validation is deferred at the owner's request.

No remote server has been provisioned or deployed as of 2026-10-01.

## Startup behavior (0.3.0+)

Every normal server start waits for browser world selection with a fresh random seed. Saves are not auto-resumed. To deliberately resume, add `--load data/world.json`. Browser refreshes join the current shared world. New world creation archives prior state under data/archives before replacing it. Keep volume backups and monitor archive disk usage.
