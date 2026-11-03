import io
import json

P = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain\src\os\state.json"
BAD = '6/6.' + chr(34) + '), wired'
GOOD = '6/6), wired'

with io.open(P, "r", encoding="utf-8", newline="") as handle:
    text = handle.read()
print("hits", text.count(BAD))
text = text.replace(BAD, GOOD)
with io.open(P, "w", encoding="utf-8", newline="") as handle:
    handle.write(text)
with io.open(P, "r", encoding="utf-8") as handle:
    data = json.load(handle)
print("tick", data["tick"], "lines", len(data["log"]))