"""Polyformalism canary — FNV-1a 64-bit, matches the fleet reference.

Reference: /workspace/repos/quilt-canary/canary.py
The string "café Δ 日本語" must hash to 0x024a555471370b18d in 5 ports:
  - Python, JavaScript, Rust, Bash, SQL, Go, Zig
"""


def fnv1a_64(s: str) -> int:
    h = 0xcbf29ce484222325
    for b in s.encode("utf-8"):
        h = h ^ b
        h = (h * 0x100000001b3) & 0xffffffffffffffff
    return h


CANARY_STRING = "café Δ 日本語"


def canary() -> str:
    """Returns 0x024a555471370b18d — the fleet's polyformalism canary."""
    h = fnv1a_64(CANARY_STRING)
    return f"0x{h:016x}"


if __name__ == "__main__":
    c = canary()
    print(c)
    assert c == "0x24a555471370b18d", f"Canary mismatch: {c}"
    print("✓ polyformalism canary verified")
