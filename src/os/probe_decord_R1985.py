# probe_decord_R1985.py - five-silence external-face probe for the
# takeover closeout: DEC token set-diff vs state.json last_dec_tokens
# (content-addressing law) + ORD new-order-lines scan (lines dated
# 2026-10-15/16 = new since the R1984 consumed-tail state
# "10-14 16:2x") + LEDGER @BigDomain unacknowledged-row tail check.
# Pure stdlib, read-only on group files, zero writes.
import json
import re

G_DEC = (r"C:\Users\sjs20\Desktop\FluxGroup\docs\decisions.md")
G_ORD = (r"C:\Users\sjs20\Desktop\FluxGroup\docs\orders.md")
G_LED = (r"C:\Users\sjs20\Desktop\FluxGroup\cph4\evolution-ledger.md")
STATE = r"src\os\state.json"


def main():
    with open(STATE, encoding="utf-8") as h:
        st = json.load(h)
    known = set(st.get("last_dec_tokens", "").split(","))

    with open(G_DEC, encoding="utf-8") as h:
        dec = h.read()
    toks = set(re.findall(r"[DC]-\d{8}-\d+", dec))
    new_dec = sorted(toks - known)
    print("DEC total-tokens=%d known=%d NEW=%d"
          % (len(toks), len(known), len(new_dec)))
    for t in new_dec[:20]:
        print("  NEW-DEC %s" % t)

    with open(G_ORD, encoding="utf-8") as h:
        ord_lines = h.read().splitlines()
    new_ord = [ln for ln in ord_lines if "2026-10-15" in ln
               or "2026-10-16" in ln]
    print("ORD lines-dated-1015/16=%d" % len(new_ord))
    for ln in new_ord[:8]:
        print("  ORD: %s" % ln[:140])

    with open(G_LED, encoding="utf-8") as h:
        led = h.read().splitlines()
    atbd = [ln for ln in led if "BigDomain" in ln]
    print("LEDGER @BigDomain rows=%d tail-dates:" % len(atbd))
    for ln in atbd[-3:]:
        m = re.search(r"2026-10-\d\d", ln)
        print("  tail-date=%s" % (m.group(0) if m else "?"))

    verdict_flat = (len(new_dec) == 0 and len(new_ord) == 0)
    print("FIVE-SILENCE-EXTERNAL=%s"
          % ("FLAT" if verdict_flat else "HAS-NEW"))
    return 0


if __name__ == "__main__":
    main()
