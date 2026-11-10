"""Read-back of the state.json log indents this closeout actually wrote."""

import io

data = io.open("src/os/state.json", "rb").read().decode("utf-8")
lines = data.split("\r\n")
tail = lines[-16:]
for line in tail:
    indent = len(line) - len(line.lstrip(" "))
    print("%2d %s" % (indent, line.strip()[:70]))
