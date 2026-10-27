import io, json, datetime

p = 'docs/status-export.json'
d = json.load(io.open(p, encoding='utf-8'))
d['export_ts'] = datetime.datetime.now().astimezone().isoformat(
    timespec='seconds')
d['do'] = ("R2163 R2162 R2161 the sandbox developer-API marketplace read faces "
           "(catalog, demand, months, refunds, claims, ratings) for the "
           "silicon-domain public co-creation platform - product line still "
           "pre-commercial and blocked on the physical items only.")
d['ceo_face'] = {
    "current": ("R2163 category refund months: the market can now answer "
                "whether a category's refund load this month is abnormal - "
                "per category per UTC month gross, refunds and net on a cash "
                "basis, with a refund-only month showing a negative net "
                "instead of a fake sale and two deliberately separate "
                "extremes (worst rate among months that settled something, "
                "largest refund amount over all months)"),
    "latest_artifact": ("qa/apimarket-categoryrefundmonths-R2163-a.log / "
                        "-b.log (SUITE PASS 8/8, evidence sha16 "
                        "fa87745a78b8dc7c) + src/sandbox/ledger/apimarket.py "
                        "(api_category_refund_months, written 2026-10-27)"),
    "next_milestone": ("full battery green on the committed tree plus a "
                       "truthful suite-matrix regeneration, then the next "
                       "claimable explore head (within 48h)")
}
io.open(p, 'w', encoding='utf-8', newline='\n').write(
    json.dumps(d, ensure_ascii=False, indent=2) + '\n')
print('export refreshed', d['export_ts'])