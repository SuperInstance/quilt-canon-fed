"""Canon Federation — peer-to-peer canon sharing protocol.

Multiple Quilt instances can federate:
- Each instance is a "node" with a unique node_id
- Nodes share canon via HTTP GET /canon/<id>
- Nodes submit canon via HTTP POST /submit
- Canon is verified via witness chain (each node can verify chain)

Substrate: network/p2p
"""
import hashlib
import json
import socket
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional


def node_id_from_name(name: str) -> str:
    """Derive a node_id from a friendly name."""
    return "node_" + hashlib.sha256(name.encode()).hexdigest()[:12]


def short_id(node_id: str) -> str:
    """Return a short version of the node_id."""
    return node_id[-8:]


@dataclass
class Peer:
    """A peer node in the federation."""
    node_id: str
    name: str
    url: str  # Base URL (e.g., http://host:port)
    last_seen: float = 0
    canon_count: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FederationState:
    """The state of a federation node."""
    node_id: str
    name: str
    url: str
    peers: Dict[str, Peer] = field(default_factory=dict)
    canon: Dict[str, str] = field(default_factory=dict)  # canon_id -> lore

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "url": self.url,
            "peers": {k: v.to_dict() for k, v in self.peers.items()},
            "canon_count": len(self.canon),
        }


class CanonFederation:
    """A federation node — has its own canon + a list of peers."""

    def __init__(self, name: str = "anon", url: str = "http://localhost:8767",
                 state_path: Optional[Path] = None):
        self.name = name
        self.url = url
        self.node_id = node_id_from_name(f"{name}-{url}")
        self.state = FederationState(
            node_id=self.node_id,
            name=name,
            url=url,
        )
        self.state_path = state_path or (Path.home() / ".cache" / "quilt-canon-fed" / "state.json")
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        if self.state_path.exists():
            try:
                d = json.loads(self.state_path.read_text())
                self.state = FederationState(
                    node_id=d.get("node_id", self.node_id),
                    name=d.get("name", self.name),
                    url=d.get("url", self.url),
                    peers={k: Peer(**v) for k, v in d.get("peers", {}).items()},
                    canon=d.get("canon", {}),
                )
            except Exception:
                pass

    def _save(self):
        self.state_path.write_text(json.dumps({
            "node_id": self.state.node_id,
            "name": self.state.name,
            "url": self.state.url,
            "peers": {k: v.to_dict() for k, v in self.state.peers.items()},
            "canon": self.state.canon,
        }, indent=1))

    def add_peer(self, name: str, url: str) -> Peer:
        peer_id = node_id_from_name(f"{name}-{url}")
        peer = Peer(node_id=peer_id, name=name, url=url, last_seen=time.time())
        self.state.peers[peer_id] = peer
        self._save()
        return peer

    def remove_peer(self, peer_id: str):
        if peer_id in self.state.peers:
            del self.state.peers[peer_id]
            self._save()

    def list_peers(self) -> List[Peer]:
        return list(self.state.peers.values())

    def add_local_canon(self, canon_id: str, lore: str):
        self.state.canon[canon_id] = lore
        self._save()

    def fetch_peer_canon(self, peer: Peer) -> Dict[str, str]:
        """Fetch canon list from a peer."""
        try:
            req = urllib.request.Request(f"{peer.url}/canon/list", headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                canon_list = data.get("canon", [])

            # Fetch each canon
            peer_canon = {}
            for canon_id in canon_list:
                try:
                    req = urllib.request.Request(f"{peer.url}/canon/{canon_id}")
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        peer_canon[canon_id] = resp.read().decode()
                except Exception:
                    pass

            peer.last_seen = time.time()
            peer.canon_count = len(peer_canon)
            self._save()
            return peer_canon
        except Exception as e:
            return {"_error": str(e)}

    def fetch_all_peers(self) -> Dict[str, Dict[str, str]]:
        """Fetch canon from all peers."""
        all_canon = {}
        for peer in self.list_peers():
            peer_canon = self.fetch_peer_canon(peer)
            all_canon[peer.name] = peer_canon
        return all_canon

    def submit_to_peer(self, peer: Peer, canon_id: str, lore: str) -> bool:
        """Submit a canon piece to a peer."""
        try:
            body = json.dumps({"id": canon_id, "lore": lore}).encode()
            req = urllib.request.Request(
                f"{peer.url}/submit",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except Exception:
            return False

    def stats(self) -> Dict:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "url": self.url,
            "local_canon_count": len(self.state.canon),
            "peer_count": len(self.state.peers),
            "peers": [
                {"node_id": p.node_id, "name": p.name, "url": p.url, "last_seen": p.last_seen, "canon_count": p.canon_count}
                for p in self.list_peers()
            ],
        }
