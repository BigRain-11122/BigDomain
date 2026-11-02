# live_R2401.py - read-only live capture for ledger_line_shape_guard.
# Writes ONE file: qa/ledger-line-shape-guard-live-R2401.log
import hashlib
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import ledger_line_shape_guard as LLSG  # noqa: E402

STATE = os.path.join(BASE, "state.json")
MODULE = os.path.join(BASE, "ledger_line_shape_guard.py")
RUNNER = os.path.join(REPO, "src", "sandbox", "reconcile_all.py")
OUT = os.path.join(REPO, "qa", "ledger-line-shape-guard-live-R2401.log")

DATED = ("2026-11-02 R2392 tokens: local=~38k api=0 api_reason=the exact "
         "shape R2392 wrote and the law refuses")


def digest(path):
    with io.open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()[:16]


def main():
    lines = []
    before = digest(MODULE)
    payload = json.loads(io.open(STATE, "r", encoding="utf-8").read())
    ledger = [item for item in payload["log"]
              if isinstance(item, str) and item.startswith("R")]
    last = ledger[-1] if ledger else ""

    real = LLSG.check_candidate(last)
    dated = LLSG.check_candidate(DATED)
    dry = LLSG.append_ledger_line(STATE, last + " (guard probe, not landed)",
                                  execute=False)
    text = io.open(STATE, "r", encoding="utf-8", newline="").read()
    out = dict((k, real.get(k)) for k in LLSG.JSON_KEYS)
    json_a = json.dumps(out, sort_keys=True)
    json_b = json.dumps(dict((k, LLSG.check_candidate(last).get(k))
                             for k in LLSG.JSON_KEYS), sort_keys=True)

    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    registry = runner.count('    ("os-')
    after = digest(MODULE)

    lines.append("ledger_line_shape_guard live capture R2401 (real tree, "
                 "read-only)")
    lines.append("state=%s bytes=%d log_items=%d ledger_items=%d"
                 % (os.path.basename(STATE), os.path.getsize(STATE),
                    len(payload["log"]), len(ledger)))
    lines.append("last_real_ledger_round=%s verdict=%s code=%s round=%s "
                 "local=%s api=%s"
                 % (last.split(" tokens:")[0] if last else "-",
                    real["verdict"], real["code"], real["round"],
                    real["local_value"], real["api"]))
    lines.append("dated_candidate verdict=%s code=%s token=%s"
                 % (dated["verdict"], dated["code"], dated["token"]))
    lines.append("dry_run_same_line predicted_bytes=%s wrote=%s "
                 "state_bytes_now=%d"
                 % (dry["predicted_bytes"], dry["wrote"],
                    len(text.encode("utf-8"))))
    lines.append("json_stable=%s keys=%s"
                 % (json_a == json_b, ",".join(LLSG.JSON_KEYS)))
    lines.append("registry_rows=%d module_digest=%s/%s unchanged=%s"
                 % (registry, before, after, before == after))
    body = "\n".join(lines) + "\n"
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    print(body, end="")
    print("WROTE %s bytes=%d" % (OUT, len(body.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())