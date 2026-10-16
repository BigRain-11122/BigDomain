# closeout_R2007.py - R2007 (honorcert yearbooks_combined
# multi-year read window) closeout driver. Consumes
# closeout_payload_R2007.json (CJK data file law): (1) state.json
# byte-surgical tick bump + two-line log append (CRLF, 16-space
# indent, no whole-file re-serialization), (2) explore.md claim
# row flip + done note + family reseed row, (3) heartbeat line,
# (4) status-export refresh (export_ts / ceo_face three rows /
# results row / self_drive recompute via the canonical caliber).
# Script logic is ASCII; Chinese content lives in the payload.
import io
import json
import os
import sys
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

P_PAYLOAD = os.path.join(HERE, "closeout_payload_R2007.json")
P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_EXPLORE = os.path.join(ROOT, "state", "queue", "explore.md")
P_HEART = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")

PAY = json.loads(io.open(P_PAYLOAD, encoding="utf-8").read())


def jdump_line(text):
    return json.dumps(text, ensure_ascii=False)


def main():
    # -- (1) state.json byte-surgical tick + log append ----------
    raw = io.open(P_STATE, "rb").read()
    old_tick = b'"tick": 2006,'
    new_tick = b'"tick": 2007,'
    assert raw.count(old_tick) == 1, "tick anchor not unique"
    raw = raw.replace(old_tick, new_tick)
    assert raw.endswith(b'"\r\n    ]\r\n}\r\n'), "state tail shape"
    add = (b'"\r\n                '
           + jdump_line(PAY["round_line"]).encode("utf-8")
           + b',\r\n                '
           + jdump_line(PAY["tokens_line"]).encode("utf-8")
           + b'\r\n    ]\r\n}')
    raw = raw[:-len(b'"\r\n    ]\r\n}\r\n')] + add + b'\r\n'
    with io.open(P_STATE, "wb") as fh:
        fh.write(raw)
    st = json.loads(io.open(P_STATE, encoding="utf-8").read())
    assert st["tick"] == 2007, "tick bump failed"
    assert len(st["log"]) == 19, "log append shape wrong"
    assert all(ln.startswith("2026-10-17 R2007")
               for ln in st["log"][-2:][:1]), "round line head"
    print("state ok tick=2007 log-items=%d bytes=%d"
          % (len(st["log"]), os.path.getsize(P_STATE)))

    # -- (2) explore.md claim flip + done note + reseed ----------
    text = io.open(P_EXPLORE, encoding="utf-8").read()
    anchor_open = PAY["claim_row_open_anchor"]
    assert text.count(anchor_open) == 1, "claim row anchor"
    text = text.replace(anchor_open,
                        "- [x] 荣誉年册多年并读窗读面探索"
                        "（honor_yearbook 后继")
    done_anchor = PAY["claim_row_done_anchor"]
    assert text.count(done_anchor) == 1, "done anchor"
    text = text.replace(done_anchor,
                        done_anchor + PAY["done_note"])
    assert text.count(PAY["reseed_row"]) == 0, "reseed exists"
    if not text.endswith("\n"):
        text += "\n"
    text += PAY["reseed_row"] + "\n"
    with io.open(P_EXPLORE, "w", encoding="utf-8",
                 newline="") as fh:
        fh.write(text)
    print("explore ok: row flipped, done note, reseed appended")

    # -- (3) heartbeat line --------------------------------------
    now = datetime.now(timezone(timedelta(hours=8)))
    stamp = now.strftime("%Y-%m-%d %H:%M") + " +08:00"
    hb_line = (stamp + " | BigDomain OSLoop alive | tick 2007 | "
               + PAY["heartbeat_line"] + "\n")
    with io.open(P_HEART, "a", encoding="utf-8",
                 newline="") as fh:
        fh.write(hb_line)
    print("heartbeat ok")

    # -- (4) status-export refresh -------------------------------
    import check_export_consistency as CEC
    derived, _state, exp, _pat = CEC.recompute()
    exp["export_ts"] = now.isoformat(timespec="seconds")
    exp["ceo_face"]["current"] = PAY["ceo_current"]
    exp["ceo_face"]["latest_artifact"] = PAY["ceo_artifact"]
    exp["ceo_face"]["next_milestone"] = PAY["ceo_milestone"]
    exp["results"].append([PAY["results_row_tick"],
                           PAY["results_row_label"]])
    derived["method"] = ("machine-derived from state.json log"
                        " per BD-PROP-001 caliber"
                        " (check_export_consistency.recompute)")
    exp["self_drive"] = derived
    with io.open(P_EXPORT, "w", encoding="utf-8",
                 newline="") as fh:
        json.dump(exp, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("export ok ts=%s self_drive window=%s W=%d sub=%d"
          " explore_open=%d"
          % (exp["export_ts"], derived["window"],
             derived["log_lines_in_window"],
             derived["substantive_non_idle_mention_lines"],
             derived.get("queue_explore_open", -1)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
