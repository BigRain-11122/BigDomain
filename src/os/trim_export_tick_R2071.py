"""Trim the stale 2070 tick row so exactly one tick row remains
(the export checker law: exactly one tick-labelled results row)."""
import io
import json
import re
import sys

PATH = 'docs/status-export.json'
with io.open(PATH, 'r', encoding='utf-8', newline='') as f:
    text = f.read()
NL = '\r\n' if '\r\n' in text else '\n'
before = json.loads(text)

pat = (r'\[' + NL + '      "2070",' + NL +
       r'      "OSLoop [^"]*"' + NL +
       r'    \],' + NL)
text, n = re.subn(pat, '', text, count=1)
if n != 1:
    sys.exit('FATAL: 2070 tick row anchor hit %d' % n)

after = json.loads(text)
ids = [r[0] for r in after['results']]
tick_rows = [r for r in after['results'] if r[1] == 'OSLoop 执行 tick']
if len(tick_rows) != 1 or tick_rows[0][0] != '2071':
    sys.exit('FATAL: tick rows %r' % ([r[0] for r in tick_rows],))
if len(after['results']) != len(before['results']) - 1:
    sys.exit('FATAL: results count drift')
if ids[:3] != ['R2071', '2071', 'R2070']:
    sys.exit('FATAL: head order %r' % (ids[:3],))
with io.open(PATH, 'w', encoding='utf-8', newline='') as f:
    f.write(text)
print('tick row trimmed; remaining tick row=%s' % tick_rows[0][0])