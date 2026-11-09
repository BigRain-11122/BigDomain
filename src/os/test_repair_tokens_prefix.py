"""Suite for src/os/repair_tokens_prefix_R2597.py (AC-RTP1..AC-RTP6).

Every case runs against a private temporary state document, never the live
one, so a green suite can never be papered over by touching the real tree.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import ledger_lines as LL
import repair_tokens_prefix_R2597 as R


def doc(lines):
    return json.dumps({'tick': 1, 'log': list(lines)}, ensure_ascii=False,
                      indent=1)


class RepairTokensPrefixCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix='rtp-')
        self.path = os.path.join(self.dir, 'state.json')

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def write(self, lines):
        text = doc(lines)
        with open(self.path, 'wb') as fh:
            fh.write(text.encode('utf-8'))
        return text

    def test_ac_rtp1_check_reads_dirty_and_writes_nothing(self):
        lines = ['2026-11-09 R2596 PRODUCT window did a thing.',
                 'tokens: local=1 api=0 api_reason=none']
        text = self.write(lines)
        code, report = R.check(self.path)
        self.assertEqual(code, 2)
        self.assertEqual(report['verdict'], 'DIRTY')
        self.assertEqual([f['round'] for f in report['detail']], ['2596'])
        self.assertEqual(open(self.path, 'rb').read().decode('utf-8'), text)
        clean = self.write(['2026-11-09 R2596 PRODUCT window did a thing.',
                            'R2596 tokens: local=1 api=0'])
        code2, report2 = R.check(self.path)
        self.assertEqual((code2, report2['verdict']), (0, 'CLEAN'))
        self.assertEqual(open(self.path, 'rb').read().decode('utf-8'), clean)

    def test_ac_rtp2_only_an_unlabelled_tokens_line_is_labelled(self):
        lines = ['2026-11-09 R2596 PRODUCT window did a thing.',
                 'tokens: local=1 api=0 api_reason=none']
        self.write(lines)
        out = R.apply(self.path)
        self.assertEqual(out['verdict'], 'REPAIRED')
        payload = json.loads(open(self.path, 'rb').read().decode('utf-8'))
        self.assertEqual(payload['log'][1][:7], 'R2596 t')
        self.assertEqual(LL.classify(payload['log'][1]), 'ledger')
        # a narrative line that merely mentions tokens is never rewritten
        bad = ['2026-11-09 R2596 PRODUCT window did a thing.',
               'R2596 the tokens: line was missing']
        self.write(bad)
        self.assertEqual(R.check(self.path)[0], 2)
        with self.assertRaises(R.RepairError):
            R.apply(self.path)

    def test_ac_rtp3_second_apply_is_a_no_byte_no_op(self):
        self.write(['2026-11-09 R2596 PRODUCT window did a thing.',
                    'tokens: local=1 api=0'])
        R.apply(self.path)
        first = open(self.path, 'rb').read()
        again = R.apply(self.path)
        self.assertEqual(again['verdict'], 'CLEAN')
        self.assertEqual(open(self.path, 'rb').read(), first)

    def test_ac_rtp4_payload_proof_and_layout_preserved(self):
        lines = ['2026-11-09 R2596 PRODUCT window did a thing.',
                 'tokens: local=1 api=0', '2026-11-09 R2596 other line.']
        before_text = self.write(lines)
        before = json.loads(before_text)
        R.apply(self.path)
        after_text = open(self.path, 'rb').read().decode('utf-8')
        after = json.loads(after_text)
        self.assertEqual(len(before_text) + len('R2596 '), len(after_text))
        self.assertEqual(before_text.replace(json.dumps(lines[1]), '', 1),
                         after_text.replace(json.dumps(after['log'][1]), '', 1))
        for key in before:
            if key != 'log':
                self.assertEqual(before[key], after[key])
        self.assertEqual([x for i, x in enumerate(after['log']) if i != 1],
                         [x for i, x in enumerate(before['log']) if i != 1])

    def test_ac_rtp5_ambiguous_and_already_ledger_refuse(self):
        self.write(['2026-11-09 R2596 PRODUCT window did a thing.',
                    'tokens: local=1 api=0', 'tokens: local=2 api=0'])
        with self.assertRaises(R.RepairError) as ctx:
            R.apply(self.path)
        self.assertEqual(ctx.exception.code, 'E_RTP_AMBIGUOUS')

    def test_ac_rtp6_source_is_ascii_and_stdlib_only(self):
        src = open(os.path.join(HERE, 'repair_tokens_prefix_R2597.py'),
                   'rb').read()
        self.assertEqual(src.count(b'\x00'), 0)
        src.decode('ascii')
        for banned in ('requests', 'urllib', 'socket', 'http'):
            self.assertNotIn('import ' + banned, src.decode('ascii'))
        self.assertIn('--check', src.decode('ascii'))
        self.assertIn('--apply', src.decode('ascii'))


if __name__ == '__main__':
    unittest.main(verbosity=2)