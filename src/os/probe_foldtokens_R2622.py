"""Extract the token set the fold predicate will demand for a given window."""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import state_fold as SF  # noqa: E402

start = int(sys.argv[1])
end = int(sys.argv[2])

data = json.loads(io.open(os.path.join(BASE, "state.json"), "rb")
                  .read().decode("utf-8"))
window = data["log"][start - 1:end]
tokens = set()
for line in window:
    tokens |= set(SF.PAT.findall(line))
print("window=%d..%d lines=%d tokens=%d" % (start, end, len(window), len(tokens)))
print(" ".join(sorted(tokens)))
