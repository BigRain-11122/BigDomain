import io
import re

s = io.open(r"src\os\closeout_R2017.py",
            encoding="utf-8").read()
bad = []
for m in re.finditer(r"\\u(?![0-9a-fA-F]{4})", s):
    bad.append((m.start(), repr(s[max(0, m.start() - 25):
                                    m.start() + 35])))
print("BAD_COUNT=%d" % len(bad))
for _pos, ctx in bad[:12]:
    print(ctx)
