"""R2757 closeout: bump the tick and append this round's two log lines.

The battery leg reconcile-battery-R2755 was settled RED by measurement and the
birth site named in that red was repaired on the committed tree. ASCII only.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state_io

REPO = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(REPO, "src", "os", "state.json")

ROUND = (
    "R2757 THE R2755 LEG WAS SETTLED RED BY MEASUREMENT AND ITS BIRTH SITE "
    "WAS REPAIRED, both measured rather than predicted. Preflight on the "
    "closed leg (pid 59236 kernel GONE, stream closing_rc=1, 676 suite rows "
    "over 676 unique names, registry 676/5032 by import, evidence 1253346B "
    "utf-8 bom=False crlf=0 lone_cr=0 nul=0, criteria recount EXACTLY 5032) "
    "read VERDICT NOT-READY gates=14 failed=2: closing-rc-zero and "
    "evidence-closing-line, because the runner ended on RUNNER FAIL (6 failed "
    "assertions) with no BATTERY rc= row. Five suites were attributed by name "
    "and every other row was clean, so zero unattributed FAIL rows. THE RED "
    "DID NOT DISSOLVE ON THE FINAL TREE, which disproves the drift-only "
    "reading: all five suites were re-run individually on HEAD fe1555d8 and "
    "still refused. ONE BIRTH SITE explains all five - export_R2431.main() "
    "exits 2 with CHECK-MISMATCH because its health term demanded "
    "back[\"outs\"][0] == latest, which R2751 D3 forbids the moment latest is "
    "a none-line above a real artifact, so every wait round or every round "
    "whose artifact filename does not carry the round id refused forever. "
    "CONFLICT RESOLVED IN ONE STATED LINE: R2751 C2 gives way. A wait round "
    "still NAMES the newest prior artifact in ceo_face.latest_artifact, but "
    "outs[0] stays governed by D3, so the health term now compares the LANDED "
    "outs list with the list this driver actually appended (written_outs). "
    "The pinned literal in test_export_driver_self_drive_health AC-EDSH5 WAS "
    "the defect and was re-pinned to the intent, with the repair disclosed in "
    "place, following the R2596 precedent. The stale export document was "
    "refreshed AFTER the tick write so its tick row and self_drive block are "
    "not stale on arrival."
)

TOKENS = (
    "R2757 tokens: local=~13k api=0 api_reason=debt window - one five-"
    "reading scan with the debt gate, one adoption preflight run over the "
    "closed leg, one byte-level leg measurement, five individual suite re-runs "
    "on the final tree, two source edits at one birth site with the pinned "
    "literal re-pinned to its intent, one state write and one export refresh; "
    "zero cloud calls and zero external API touches"
)


def main():
    with io.open(STATE, encoding="utf-8") as handle:
        payload = json.load(handle)
    payload["tick"] = int(payload.get("tick", 0)) + 1
    log = payload.get("log") or []
    log.append(ROUND)
    log.append(TOKENS)
    payload["log"] = log
    state_io.write_document(STATE, payload)
    back = json.load(io.open(STATE, encoding="utf-8"))
    print("tick=%s log_len=%d" % (back["tick"], len(back["log"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
