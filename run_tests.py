"""Test runner for quilt-canon-fed (no pytest dep)."""
import sys
import json
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, "/workspace/repos/quilt-canon-fed")

from quilt_canon_fed.canary import canary
from quilt_canon_fed.protocol import CanonFederation, node_id_from_name, short_id
from quilt_canon_fed.server import start_server, FederationHTTPHandler

results = []
failures = []


def test(name, func):
    try:
        func()
        results.append((name, "PASS"))
    except AssertionError as e:
        results.append((name, f"FAIL: {e}"))
        failures.append(name)
    except Exception as e:
        results.append((name, f"ERROR: {type(e).__name__}: {e}"))
        failures.append(name)


def t_canary():
    assert canary() == "0x24a555471370b18d"


def t_node_id_from_name():
    id1 = node_id_from_name("node1")
    id2 = node_id_from_name("node2")
    assert id1.startswith("node_")
    assert id1 != id2


def test_federation_basic(tmp):
    fed = CanonFederation("node1", "http://localhost:9999", state_path=tmp / "s.json")
    assert fed.node_id.startswith("node_")
    assert len(fed.state.peers) == 0
    assert len(fed.state.canon) == 0


def test_federation_add_peer(tmp):
    fed = CanonFederation("node1", "http://localhost:9999", state_path=tmp / "s.json")
    peer = fed.add_peer("alice", "http://localhost:9001")
    assert peer.name == "alice"
    assert peer.url == "http://localhost:9001"
    assert len(fed.list_peers()) == 1


def test_federation_add_canon(tmp):
    fed = CanonFederation("node1", "http://localhost:9999", state_path=tmp / "s.json")
    fed.add_local_canon("test_lore", "The substrate walker walks cells.")
    assert "test_lore" in fed.state.canon


def test_federation_persistence():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "s.json"
        fed1 = CanonFederation("node1", "http://localhost:9999", state_path=path)
        fed1.add_local_canon("test", "lore")
        fed1.add_peer("alice", "http://x:8001")

        fed2 = CanonFederation("node1", "http://localhost:9999", state_path=path)
        assert "test" in fed2.state.canon
        assert len(fed2.list_peers()) == 1


def test_federation_stats():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        fed = CanonFederation("node1", "http://localhost:9999", state_path=Path(td) / "s.json")
        fed.add_local_canon("a", "lore a")
        fed.add_local_canon("b", "lore b")
        fed.add_peer("alice", "http://x:8001")
        stats = fed.stats()
        assert stats["local_canon_count"] == 2
        assert stats["peer_count"] == 1


def _free_port():
    import socket
    s = socket.socket()
    s.bind(("", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def test_server_endpoints():
    """Test that the HTTP server exposes canon and accepts peers."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        port = _free_port()
        fed = CanonFederation("test-node", f"http://localhost:{port}", state_path=Path(td) / "s.json")
        fed.add_local_canon("hello", "# Hello\n\nWorld")
        fed.add_local_canon("bye", "# Bye\n\nWorld")

        thread, server = start_server(fed, port=port)
        time.sleep(0.5)  # Let server start

        try:
            with urllib.request.urlopen(f"http://localhost:{port}/info", timeout=5) as r:
                data = json.loads(r.read().decode())
                assert data["info"]["name"] == "test-node"
                assert data["info"]["local_canon_count"] == 2

            with urllib.request.urlopen(f"http://localhost:{port}/canon/list", timeout=5) as r:
                data = json.loads(r.read().decode())
                assert set(data["canon"]) == {"hello", "bye"}

            with urllib.request.urlopen(f"http://localhost:{port}/canon/hello", timeout=5) as r:
                content = r.read().decode()
                assert "Hello" in content

            req = urllib.request.Request(
                f"http://localhost:{port}/peers/add",
                data=json.dumps({"name": "bob", "url": "http://bob:8001"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read().decode())
                assert data["added"]["name"] == "bob"
        finally:
            server.shutdown()
            server.server_close()


def test_server_submit():
    """Test that /submit accepts new canon."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        port = _free_port()
        fed = CanonFederation("test-node", f"http://localhost:{port}", state_path=Path(td) / "s.json")

        thread, server = start_server(fed, port=port)
        time.sleep(0.5)

        try:
            req = urllib.request.Request(
                f"http://localhost:{port}/submit",
                data=json.dumps({"id": "from-peer", "lore": "# Test\n\nbody"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read().decode())
                assert data["admitted"] is True

            with urllib.request.urlopen(f"http://localhost:{port}/canon/from-peer", timeout=5) as r:
                content = r.read().decode()
                assert "Test" in content
        finally:
            server.shutdown()
            server.server_close()


with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    test("test_canary", t_canary)
    test("test_node_id_from_name", t_node_id_from_name)
    test("test_federation_basic", lambda: test_federation_basic(tmp))
    test("test_federation_add_peer", lambda: test_federation_add_peer(tmp))
    test("test_federation_add_canon", lambda: test_federation_add_canon(tmp))
    test("test_federation_persistence", test_federation_persistence)
    test("test_federation_stats", test_federation_stats)
    test("test_server_endpoints", test_server_endpoints)
    test("test_server_submit", test_server_submit)

print("\n=== quilt-canon-fed test results ===")
for name, status in results:
    print(f"  {status:60} {name}")

print(f"\n{len(results) - len(failures)}/{len(results)} passed")
if failures:
    sys.exit(1)
