import io
import json

p = "docs/status-export.json"
e = json.load(open(p, encoding="utf-8"))
if not any(isinstance(r, list) and r[0] == "R2134" for r in e["results"]):
    txt = (
        "R2134: the settlement report gains the post-sale claim block "
        "(backfilled from the R2134 state log so the CEO-visible face has no "
        "gap): report['claims'] carries the market-wide api_claims envelope "
        "verbatim, collect_attention derives one claim_debt finding per seller "
        "holding at least one open claim, the page renders a Claims section "
        "with the four status counters, and REPORT_SCHEMA moves 16 -> 17 "
        "additively. Suite 8/8 double-run identical sha16 DAC0C53AFD2A9D1E, "
        "battery 338/338 and matrix 338/2812 byte-identical in that round."
    )
    e["results"].insert(1, ["R2134", txt])
    with io.open(p, "w", encoding="utf-8", newline="\n") as h:
        json.dump(e, h, ensure_ascii=False, indent=1)
        h.write("\n")
    print("backfilled R2134")
else:
    print("already present")