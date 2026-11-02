import io

p = 'src/sandbox/reconcile_all.py'
t = io.open(p, encoding='utf-8').read()
anchor = ('    ("os-export-publish-from-import-law",\n'
          '     os.path.join("..", "os", "test_export_publish_from_import_law.py"), 6),\n')
assert t.count(anchor) == 1, t.count(anchor)
row = ('    # R2393: the ledger law was LEDGER_PREFIX_RE = ^R(\\d{3,5}) tokens: and\n'
       '    # nothing asked it BEFORE a line was appended, so the R2392 closeout\n'
       '    # wrote a date-prefixed ledger line and four suites went red a window\n'
       '    # later. One door now asks the law at the write path.\n'
       '    # (AC-LLSG1..AC-LLSG6 were pinned in state/queue/tech.md:470 as the\n'
       '    # R2393 seed row BEFORE the code.)\n'
       '    ("os-ledger-line-shape-guard",\n'
       '     os.path.join("..", "os", "test_ledger_line_shape_guard.py"), 6),\n')
t = t.replace(anchor, anchor + row, 1)
io.open(p, 'w', encoding='utf-8', newline='').write(t)
print('wired', t.count('os-ledger-line-shape-guard'))