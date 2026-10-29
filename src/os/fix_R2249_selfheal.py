# fix_R2249_selfheal.py - one honest correction: the R2249 self-heal line
# claimed the loop task "is Running", but this window's reading was
# State=Ready (idle between its five-minute triggers). The principal fact
# (LogonType=InteractiveToken) is unchanged; only the unverified state
# word is corrected. Layout is preserved byte for byte.
import io
import json
import os

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
STATE = os.path.join(ROOT, "src", "os", "state.json")

OLD = "BigDomain-OSLoop exists and is Running, but its"
NEW = ("BigDomain-OSLoop exists and is registered (State=Ready at this "
       "reading, idle between its five-minute triggers), but its")


def main():
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        raw = handle.read()
    if raw.count(OLD) < 1:
        print("ANCHOR MISSING - refusing")
        return 2
    # every earlier round's self-heal line opens with the same words, so
    # the correction is aimed at the LAST occurrence, proved to be this
    # window's by the disclosure counter that follows it.
    idx = raw.rfind(OLD)
    tail = raw[idx:idx + 1200]
    if "nineteenth consecutive disclosure" not in tail:
        print("LAST OCCURRENCE IS NOT THIS WINDOW - refusing")
        return 2
    out = raw[:idx] + NEW + raw[idx + len(OLD):]
    data = json.loads(out)
    assert NEW in data["log"][-1]
    assert len(data["log"]) == 27
    with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
        handle.write(out)
    reread = json.loads(io.open(STATE, "r", encoding="utf-8").read())
    assert reread["log"][-1].startswith(
        "R2249 self-heal check: BigDomain-OSLoop exists and is registered")
    print("SELF-HEAL LINE CORRECTED bytes=%d tick=%d"
          % (os.path.getsize(STATE), reread["tick"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())