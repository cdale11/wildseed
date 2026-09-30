# Headless Linux deployment

## CPU container

Install Docker/Compose on the future server, clone this repository, and set an access token in the shell (do not commit it):

```sh
export WILDSEED_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
docker compose up --build -d
```

The host port binds to 127.0.0.1:8080. Reach it through an SSH tunnel (`ssh -L 8080:127.0.0.1:8080 your-server`) or a TLS reverse proxy. Enter the token under Server access in the browser. The named volume stores data/world.json. Maintain independent backups. Graceful Ctrl+C in native mode saves immediately; container autosaves every minute, so abrupt termination can lose the last minute. SIGTERM handling is a follow-up reliability item.

## Native Linux

```sh
python3 -m wildseed.server --host 127.0.0.1 --workers 0
```

If binding a non-loopback interface, set WILDSEED_TOKEN (at least 24 characters). Use a firewall and authenticated TLS proxy for remote browser access. Enforce connection/request limits at that proxy. This initial stdlib server is intended for private deployments, not untrusted public multi-tenant hosting.

## Optional compute GPU

Install a compatible PyTorch build for the host's drivers using the official PyTorch installation guidance. Then run:

```sh
python3 -m wildseed.server --device cuda --workers 0
```

CUDA inference is optional. Training/rules remain CPU-side. If CUDA is unavailable, explicit CUDA selection fails rather than pretending to accelerate. A cloud vGPU needs a compute-capable profile, host drivers and device exposure; a software display GPU will not work. The CPU Docker image does not include PyTorch or configure GPU passthrough. Validate numerical agreement, throughput and memory on the target host before recommending GPU mode.

No remote server has been provisioned or deployed as of 2026-10-01.
