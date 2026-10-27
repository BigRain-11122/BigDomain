"""Prepend the R2171 pre-registration row to the explore queue (UTF-8, LF)."""

import io
import os

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
QUEUE = os.path.join(BASE, "state", "queue", "explore.md")
SEED = os.path.join(BASE, "state", "queue", "_seed_R2171.md")


def main():
    with io.open(SEED, "r", encoding="utf-8") as handle:
        seed = handle.read().strip()
    with io.open(QUEUE, "r", encoding="utf-8") as handle:
        body = handle.read()
    if seed.split("\n")[0][:40] in body:
        print("ALREADY-PRESENT")
        return 1
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(seed + "\n" + body)
    os.remove(SEED)
    print("PREPENDED bytes=%d" % len(seed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())