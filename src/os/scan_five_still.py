# scan_five_still.py - five-silence content-addressed scan (LEDGER/DEC/ORD/GORD faces)
# Pure ASCII. Read-only on group files. Baseline = src/os/state.json fields.
import io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GRP = r"C:\Users\sjs20\Desktop\FluxGroup"

def rd(p):
    with io.open(p, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

TOKRE = re.compile(r"(?:P|D|C|O|T|XL)-\d{4}-\d{2}-\d{2}-\d+|O-2026\d{5}-\d+|D-\d{8}-\d+|C-\d{8}-\d+|BD-PROP-\d+|OH-\d{8}")

state = json.load(io.open(os.path.join(ROOT, "src", "os", "state.json"), "r", encoding="utf-8"))
log_text = json.dumps(state.get("log", []), ensure_ascii=False)

# [LEDGER] @BigDomain lines -> unreplied tokens
led = rd(os.path.join(GRP, "cph4", "evolution-ledger.md"))
led_lines = [l for l in led.splitlines() if "@BigDomain" in l]
led_unreplied = []
for l in led_lines:
    toks = set(TOKRE.findall(l))
    if toks and not any(t in log_text for t in toks):
        led_unreplied.append(sorted(toks))

# [DEC] group decisions token diff (content-addressed)
dec = rd(os.path.join(GRP, "docs", "decisions.md"))
dec_rows = [l for l in dec.splitlines() if l.strip()]
dec_tokens = set(re.findall(r"D-\d{8}-\d+|C-\d{8}-\d+", dec))
base_dec = set(x for x in state.get("last_dec_tokens", "").split(",") if x)
dec_new = sorted(dec_tokens - base_dec)

# [ORD] group orders: top timestamp sample + tail + @BigDomain rows
ordp = os.path.join(GRP, "docs", "orders.md")
ord_lines = [l for l in rd(ordp).splitlines() if l.strip()]
ord_top = ord_lines[:2]
ord_tail = ord_lines[-2:]
ord_atbd = [l[:120] for l in ord_lines if "@BigDomain" in l]
ts_re = re.compile(r"2026-\d{2}-\d{2}")
all_ts = []
for l in ord_lines:
    all_ts += ts_re.findall(l)
ord_max_ts = max(all_ts) if all_ts else "none"
# R2001 dual-format law (tech.md L259): group table rows migrated to the no-year
# '| MM-DD HH:MMx |' shape on 2026-10-15; a year-only regex reads stale dates.
# Extract the LAST table-row token in BOTH shapes, normalized to
# 'YYYY-MM-DD ...' with the file's newest year row (fallback: 2026).
ord_row_re = re.compile(r"^\|\s*((?:2026-)?\d{2}-\d{2}\s+\S+)")
ord_year_re = re.compile(r"^\|\s*(\d{4})-")
ord_last_tok = None
ord_year = ""
for l in ord_lines:
    m = ord_row_re.match(l)
    if m:
        ord_last_tok = m.group(1)
        ym = ord_year_re.match(l)
        if ym:
            ord_year = ym.group(1)
if ord_last_tok and re.match(r"^\d{2}-", ord_last_tok):
    ord_last_tok = (ord_year or "2026") + "-" + ord_last_tok

# [GORD] baseline rows = last_gord_tbl_rows (orders.md nonblank rows)
gord_rows = len(ord_lines)
gord_base = state.get("last_gord_tbl_rows")

# [BENCH]
bench = state.get("benchmarks_refreshed", "")

print("=== FIVE-STILL SCAN R%d BASELINE ===" % (state.get("tick", 0)))
print("[LEDGER] atbd_lines=%d unreplied_groups=%d" % (len(led_lines), len(led_unreplied)))
for g in led_unreplied[:10]:
    print("  UNREPLIED: %s" % ",".join(g))
print("[DEC] rows=%d tokens=%d new=%d" % (len(dec_rows), len(dec_tokens), len(dec_new)))
for t in dec_new[:15]:
    print("  NEW-DEC: %s" % t)
print("[ORD] rows=%d gord_base=%s max_ts=%s last_tok=%s atbd_rows=%d" % (gord_rows, gord_base, ord_max_ts, ord_last_tok, len(ord_atbd)))
for l in ord_atbd[-8:]:
    print("  ORD-ATBD: %s" % l)
print("[ORD-TOP] %s" % ord_top[0][:110] if ord_top else "")
print("[ORD-TAIL] %s" % ord_tail[-1][:110] if ord_tail else "")
print("[BENCH] refreshed=%s" % bench)
