import io

p = 'src/os/export_R2548.py'
t = io.open(p, encoding='utf-8', newline='').read().replace('\r\n', '\n')
old = (
 '"docs/sandbox-suite-matrix.md are now text eol=lf, after a git checkout "\n'
 '    "handed the seed writer CRLF (lf_only=False minutes after lf_only=True) "\n'
 '    "and after one matrix regeneration produced a 491/491 whole-file diff that "\n'
 '    "hid the real content delta.')
new = (
 '"docs/sandbox-suite-matrix.md are now text eol=lf, after a git checkout "\n'
 '    "handed the seed writer CRLF (lf_only=False minutes after lf_only=True, "\n'
 '    "measured by the writer own read-back) and because suite_matrix.py writes LF "\n'
 '    "while a checkout would hand the document back as CRLF and make --check "\n'
 '    "report a pure-dialect mismatch. CORRECTION made before the commit: my first "\n'
 '    "reading of the 491/491 matrix diff as line-ending churn was WRONG - it is "\n'
 '    "491 genuine per-suite timing cells - and the false reading came from my own "\n'
 '    "Out-File read-back, which had already converted the blob to CRLF.')
assert old in t, 'export anchor not found'
io.open(p, 'w', encoding='utf-8', newline='\n').write(t.replace(old, new))
print('export text corrected')

p = 'src/os/backlog.md'
t = io.open(p, encoding='utf-8', newline='').read().replace('\r\n', '\n')
old2 = ('Two line-ending pins landed (state/queue/*.md, docs/sandbox-suite-matrix.md) after '
        'a checkout handed the seed writer CRLF and one regeneration produced a 491/491 '
        'whole-file diff. Zero product points, stated rather than dressed.')
new2 = ('Two line-ending pins landed (state/queue/*.md, docs/sandbox-suite-matrix.md) after '
        'a checkout handed the seed writer CRLF back (its own read-back read lf_only=False) '
        'and because suite_matrix.py writes LF while a checkout would return CRLF. '
        'CORRECTION made before the commit: my first reading of the 491/491 matrix diff as '
        'dialect churn was wrong - it is 491 genuine per-suite timing cells, and my own '
        'Out-File read-back had produced the false reading. Zero product points, stated '
        'rather than dressed.')
assert old2 in t, 'backlog anchor not found'
io.open(p, 'w', encoding='utf-8', newline='\n').write(t.replace(old2, new2))
print('backlog corrected')