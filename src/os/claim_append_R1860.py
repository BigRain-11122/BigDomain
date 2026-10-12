"""R1860 claim-note surgery: append the pre-registered AC-SB18..SB22
criteria text to the claimed tech.md row BEFORE any product code
(honesty law: criteria registry first). Pure ASCII source; Chinese
payload lives in claim_payload_R1860.json (encoding law)."""

import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
P_PAYLOAD = os.path.join(BASE, "claim_payload_R1860.json")
P_TECH = os.path.normpath(os.path.join(
    BASE, "..", "..", "state", "queue", "tech.md"))


def detect_eol(text):
    return "\r\n" if "\r\n" in text else "\n"


def main():
    with open(P_PAYLOAD, encoding="utf-8") as fh:
        payload = json.load(fh)
    with open(P_TECH, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8")
    eol = detect_eol(text)
    lines = text.split(eol)
    prefix = payload["row_prefix"]
    hits = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    assert len(hits) == 1, "claim row expected 1 hit, got %d" % len(hits)
    idx = hits[0]
    anchor = payload["anchor_tail"]
    assert lines[idx].endswith(anchor), "row tail anchor drift"
    assert lines[idx].startswith("- [ ] "), "row not open-checkbox state"
    assert "R1860 " not in lines[idx], "claim note already present (dup)"
    lines[idx] = lines[idx] + payload["claim_note"]
    out = eol.join(lines)
    assert out.count("R1860 ") >= 1, "claim note not appended"
    with open(P_TECH, "wb") as fh:
        fh.write(out.encode("utf-8"))
    print("claim note appended: row len=%d eol=%r open_rows=%d"
          % (len(lines[idx]), eol,
             sum(1 for l in lines if l.startswith("- [ ] "))))


if __name__ == "__main__":
    main()
