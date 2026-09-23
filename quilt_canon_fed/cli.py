"""CLI for quilt-canon-fed."""
import argparse
import json
import sys
from pathlib import Path

from .protocol import CanonFederation
from .server import start_server
from .loader import load_canon


def cmd_add_canon(args):
    fed = CanonFederation(args.name, args.url)
    pieces = load_canon()
    for p in pieces:
        lore = f"# {p.title}\n\n{p.body}"
        fed.add_local_canon(p.name, lore)
    print(f"✓ Added {len(pieces)} canon pieces to local federation")
    print(f"  Node: {fed.node_id}")
    print(f"  URL: {args.url}")


def cmd_serve(args):
    fed = CanonFederation(args.name, args.url)
    pieces = load_canon()
    for p in pieces:
        lore = f"# {p.title}\n\n{p.body}"
        fed.add_local_canon(p.name, lore)
    print(f"Loaded {len(pieces)} canon pieces")
    thread, server = start_server(fed, port=args.port)
    print(f"✓ Federation node serving on http://localhost:{args.port}/")
    print(f"  Endpoints: /, /info, /canon/list, /canon/<id>, /peers, /submit, /peers/add")
    print(f"  Press Ctrl+C to stop")
    try:
        thread.join()
    except KeyboardInterrupt:
        print("Shutting down...")


def cmd_add_peer(args):
    fed = CanonFederation(args.name, args.url)
    peer = fed.add_peer(args.peer_name, args.peer_url)
    print(f"✓ Added peer {peer.name} ({peer.node_id}) at {peer.url}")


def cmd_list_peers(args):
    fed = CanonFederation(args.name, args.url)
    peers = fed.list_peers()
    print(f"Peers ({len(peers)}):")
    for p in peers:
        print(f"  {p.name:30s} {p.url:40s} canon={p.canon_count}")


def cmd_fetch(args):
    """Fetch canon from a peer."""
    fed = CanonFederation(args.name, args.url)
    peer = None
    for p in fed.list_peers():
        if p.name == args.peer_name or p.node_id == args.peer_name:
            peer = p
            break
    if peer is None:
        print(f"Unknown peer: {args.peer_name}")
        return
    print(f"Fetching canon from {peer.name} at {peer.url}...")
    canon = fed.fetch_peer_canon(peer)
    if "_error" in canon:
        print(f"Error: {canon['_error']}")
        return
    print(f"✓ Fetched {len(canon)} canon pieces")
    if args.save_to:
        out_dir = Path(args.save_to)
        out_dir.mkdir(parents=True, exist_ok=True)
        for cid, lore in canon.items():
            (out_dir / f"{cid}.md").write_text(lore)
        print(f"  Saved to {out_dir}")


def cmd_stats(args):
    fed = CanonFederation(args.name, args.url)
    print(json.dumps(fed.stats(), indent=2))


def cmd_info(args):
    """Show this node's info (for federation discovery)."""
    fed = CanonFederation(args.name, args.url)
    pieces = load_canon()
    for p in pieces:
        lore = f"# {p.title}\n\n{p.body}"
        fed.add_local_canon(p.name, lore)
    print(json.dumps({
        "node_id": fed.node_id,
        "name": fed.name,
        "url": fed.url,
        "local_canon_count": len(fed.state.canon),
        "endpoints": ["/", "/info", "/canon/list", "/canon/<id>", "/peers", "/submit", "/peers/add"],
    }, indent=2))


def main():
    p = argparse.ArgumentParser(description="quilt-canon-fed — peer-to-peer canon federation")
    p.add_argument("--name", default="local-node", help="Friendly name for this node")
    p.add_argument("--url", default="http://localhost:8767", help="Base URL for this node")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("info", help="Show node info").set_defaults(func=cmd_info)
    sub.add_parser("add-canon", help="Add local canon to federation").set_defaults(func=cmd_add_canon)
    sub.add_parser("stats", help="Show federation stats").set_defaults(func=cmd_stats)
    sub.add_parser("list-peers", help="List known peers").set_defaults(func=cmd_list_peers)

    p_serve = sub.add_parser("serve", help="Start federation HTTP server")
    p_serve.add_argument("--port", type=int, default=8767)
    p_serve.set_defaults(func=cmd_serve)

    p_ap = sub.add_parser("add-peer", help="Add a peer")
    p_ap.add_argument("peer_name")
    p_ap.add_argument("peer_url")
    p_ap.set_defaults(func=cmd_add_peer)

    p_f = sub.add_parser("fetch", help="Fetch canon from a peer")
    p_f.add_argument("peer_name", help="Peer name or node_id")
    p_f.add_argument("--save-to", help="Directory to save fetched canon")
    p_f.set_defaults(func=cmd_fetch)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
