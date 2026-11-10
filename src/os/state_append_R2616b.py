"""R2616 follow-up append: the export-derivation repair found while proving
the CEO face, and the fold that keeps the file under its waterline."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "R2616 DISCLOSED rather than smoothed, and repaired at its birth site: while proving the CEO face the export read latest_artifact='none landed yet for R2619' even though FOUR artifacts really sat under qa/. MEASURED, not guessed: derive_latest matched qa names on 'R<tick>' (R2619) while every artifact in this repository is named on the ROUND (R2616), and the tick and the round have drifted apart - so the CEO artifact line has been reading 'none' and the current line has been silently falling back to the newest log item rather than this round's opening summary, for every round since the drift began (F3: a line that must be derived was effectively canned). src/os/export_R2431.py now DERIVES the round label from the newest dated log item (round_label) and asks derive_current/derive_latest with it, so the three CEO lines name what really happened: current = this round own opening item, latest = limits-matrix-reconcile-fence-rows-R2616.log (325B) + limits-matrix-reconcile-fence-rows-next-R2616.log (379B) + suite-matrix-reconcile-fence-rows-R2616.log (1824B) + suite-matrix-reconcile-fence-rows-live-R2616.log (380B), next = reconcile-battery-R2616 inside a 48h window. check_export_consistency re-read pass=21 fail=0 VERDICT PASS after the repair, so the 21 checks still hold with the derived label.",
    "R2616 tokens: local=~26k api=0 api_reason=product window plus one birth-site repair on the CEO-visible export derivation, as recorded above; zero cloud calls and zero external API touches",
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + list(LINES)
    lines = state_io._lf_lines(text)
    start, end = state_io._log_block(lines)
    item_indent = None
    for line in lines[start:end]:
        stripped = line.lstrip(" ")
        if stripped.startswith('"') and not stripped.startswith('"log"'):
            item_indent = len(line) - len(stripped)
            break
    if item_indent is None:
        print("REFUSED no item line")
        return 6
    if not lines[end - 1].strip().endswith(","):
        lines[end - 1] = lines[end - 1].rstrip() + ","
    inserted = []
    for index, item in enumerate(LINES):
        suffix = "," if index < len(LINES) - 1 else ""
        inserted.append(" " * item_indent +
                        json.dumps(item, ensure_ascii=False) + suffix)
    out = state_io.EOL.join(lines[:end] + inserted + lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2616b_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d layout_ok=%s"
          % (expected["tick"], after["bytes"], after["log_len"],
             after["layout_ok"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
