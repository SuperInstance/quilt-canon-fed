# quilt-canon-fed

**Peer-to-peer canon federation — network substrate.**

## Quick start

```bash
pip install -e .

# Start a federation node (serves local canon on HTTP)
quilt-canon-fed --name alice --url http://localhost:8767 serve --port 8767

# In another terminal, add a peer
quilt-canon-fed --name bob --url http://localhost:8768 add-peer alice http://localhost:8767

# Fetch canon from a peer
quilt-canon-fed --name bob --url http://localhost:8768 fetch alice --save-to ./alice-canon

# Submit canon to a peer
quilt-canon-fed --name bob --url http://localhost:8768 submit alice canon_id "lore text..."

# Node info
quilt-canon-fed info

# Federation stats
quilt-canon-fed --name alice stats
```

## Endpoints (HTTP)

When you run `serve`, the federation node exposes:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Node info |
| `/info` | GET | Full federation stats |
| `/canon/list` | GET | List of canon IDs |
| `/canon/<id>` | GET | Get a canon piece (markdown) |
| `/peers` | GET | List known peers |
| `/submit` | POST | Submit a canon piece (JSON body) |
| `/peers/add` | POST | Add a peer (JSON body) |

## How it works

1. Each instance has a **node_id** (derived from name + URL via SHA-256)
2. The node holds its own canon + a list of peers
3. **Canon sharing**: any node can fetch canon from any peer
4. **Canon submission**: any node can submit canon to a peer
5. **Verified by witness chain**: each peer can verify the witness chain (compatible with `quilt-canon-witness`)

This is **federation** (not decentralization): nodes trust each other to some degree, but the protocol allows multiple independent federations to merge.

## Fleet integration

- **`quilt-canon-mcp`** — exposes canon as MCP tools; could expose federation
- **`quilt-canon-witness`** — can verify chain integrity of peer-submitted canon
- **`quilt-canon-search`** — could search federated canon
- **`quilt-canon-trace`** — could walk federated canon graph
- **`quilt-canon-feed`** — feeds could aggregate from multiple federations

## The 5 bedrock doctrines

1. `cells_are_scars` — every cell records an attempted entry
2. `witness_log_is_prediction` — the log IS the prediction
3. `canon_gate_is_chord` — canon passes when multiple agents agree (now: multiple nodes)
4. `oracle_is_heard` — JEV probes canon with multi-model consensus
5. `substrate_quantum` — the substrate is the walker; canon is substrate-aware

## Polyformalism canary

```bash
python -m quilt_canon_fed.canary
# → 0x24a555471370b18d
```

## License

MIT
