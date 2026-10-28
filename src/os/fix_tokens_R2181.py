"""R2181 fix: the watermark token scan needs the unboundaried regex.

python's \\b treats a preceding CJK character as a word character, so
four tokens that directly abut Chinese text were invisible to the
boundaried scan (D-20261006-05, D-20261007-04, D-20261007-05,
D-20261008-05). The set is re-anchored to the full 163 with the
unboundaried pattern, which is what the PowerShell five-silence scan
reads.
"""

import io
import json
import os
import re

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GROUP = os.path.abspath(os.path.join(BASE, "..", ".."))


def main():
    text = io.open(os.path.join(GROUP, "docs", "decisions.md"),
                   encoding="utf-8").read()
    tokens = sorted(set(re.findall(r"[DC]-\d{8}-\d+", text)))
    spath = os.path.join(BASE, "src", "os", "state.json")
    state = json.loads(open(spath, "rb").read().decode("utf-8"))
    state["last_dec_tokens"] = ",".join(tokens)
    with io.open(spath, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(state, ensure_ascii=False, indent=2))
        handle.write("\n")
    print("watermark re-anchored to %d tokens" % len(tokens))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())