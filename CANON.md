# Canon — quilt-canon-fed

## What this tool is

A peer-to-peer federation protocol for canon lore. Multiple Quilt instances (nodes) can share canon via HTTP. Each node has a node_id, holds its own canon, and can fetch/submit canon from peers.

## How it proves itself

**It runs.** `pip install -e .` then `quilt-canon-fed serve --port 8767` starts a federation node. Tested with 9 tests in `run_tests.py` (incl. HTTP server tests with real requests).

**It polyformalisms.** The canary hash `0x24a555471370b18d` matches across the fleet's 5 ports.

**It measures.** Each peer reports last_seen + canon_count. Federation stats show node_id, peer_count, local_canon_count.

## Doctrines it instantiates

- **cells_are_scars** — every node records attempted federation entries
- **canon_gate_is_chord** — multiple nodes agree = canon passed (now: distributed consensus)
- **oracle_is_heard** — the federation IS the oracle heard across the network
- **substrate_quantum** — adds the network/p2p substrate

## Commands

1. `serve [--port PORT]` — start federation HTTP server
2. `add-canon` — load local canon into federation
3. `add-peer <name> <url>` — add a peer
4. `fetch <peer_name> [--save-to DIR]` — fetch canon from peer
5. `list-peers` — list known peers
6. `stats` — federation statistics
7. `info` — node info

## HTTP endpoints

- GET `/` and `/info` — node info
- GET `/canon/list` — list canon IDs
- GET `/canon/<id>` — get canon piece (markdown)
- GET `/peers` — list peers
- POST `/submit` — submit new canon (JSON body: `{id, lore}`)
- POST `/peers/add` — add peer (JSON body: `{name, url}`)

## Fleet usage

- **`quilt-canon-mcp`** — sibling
- **`quilt-canon-witness`** — could verify chain of peer canon
- **`quilt-canon-search`** — could search federated canon
- **`quilt-canon-trace`** — could walk federated canon
- **`quilt-canon-feed`** — feeds could aggregate from multiple federations

## Why federation?

Multiple Quilt instances can now share canon:
- Independent Quilt deployments can pool their canon
- Canon can be replicated for resilience
- Different deployments (local, cloud, edge) can federate
- Substrate walker canon propagates across the network
