#!/usr/bin/env python3
"""Print a coarse region map of an HTFW firmware image (entropy, per-byte-lane entropy, Thumb marker density)."""
import sys, math, collections

def ent(d):
    c = collections.Counter(d); n = len(d)
    return -sum(v / n * math.log2(v / n) for v in c.values()) if n else 0.0

def main(path, win=1 << 16):
    b = open(path, 'rb').read()
    print("offset    ent  lane0 lane1 lane2 lane3  thumb-markers")
    for o in range(0, len(b), win):
        d = b[o:o + win]
        lanes = [ent(d[i::4]) for i in range(4)]
        marks = sum(1 for p in (b'\x70\x47', b'\x10\xb5', b'\xf0\xb5', b'\x70\xb5', b'\x70\xbd', b'\x10\xbd', b'\xf0\xbd')
                    for i in range(0, len(d) - 1, 2) if d[i:i + 2] == p)
        print(f"{o:08x} {ent(d):.2f} " + " ".join(f"{x:.2f}" for x in lanes) + f"  {marks}")

if __name__ == '__main__':
    main(sys.argv[1])
