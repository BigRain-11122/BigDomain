"""List the live state.json log items with their 1-based index and head."""

import io
import json

data = json.loads(io.open("src/os/state.json", "rb").read().decode("utf-8"))
for i, item in enumerate(data["log"], 1):
    print("%3d | %s" % (i, item[:96].replace("\r", " ").replace("\n", " ")))
