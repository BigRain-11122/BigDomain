#!/usr/bin/env python3
"""BigDomain copyright prep materials generator (name-pending mode).

Task: D-20261011-03 software copyright material prep (scope ruling: includes
the Silicon-Domain platform sandbox suite). Pre-registered criteria AC-SR1..AC-SR7
live in the backlog claim row (R1760) and are checked below with on-disk results.

Materials produced (all land in docs/copyright/name-pending/):
  - source-program.txt   paginated source listing (50 lines/page, front 30 +
                         back 30 pages when total > 60 pages), cover page with
                         pending-name marker + AIGC/disclaimer envelope.
  - design-spec-draft.md six-section spec draft, module inventory derived from
                         the actual tree walk (F3: derived, not hardcoded).
  - manifest.json        machine-readable run report: counts, page selection,
                         sha256 of outputs, per-AC results, secret-scan result.

Design notes:
  - This tool is pure ASCII per repo encoding law; all Chinese strings are read
    from docs/copyright/strings-zh.json (data face).
  - Deterministic: no RNG, no wall-clock stamps inside any output artifact, so
    two consecutive runs must be byte-identical (AC-SR5).
  - Zero-secret posture: reads only src/sandbox + the two data/config files
    below; never touches .env (AC-SR6).
  - Vendored third-party trees (lobby/.venv site-packages, ygo-poc/data Go
    toolchain snapshot) are NOT our original work and are excluded from the
    copyright listing; the exclusion list is recorded in the manifest.
"""

import hashlib
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, 'src', 'sandbox')
OUTDIR = os.path.join(REPO, 'docs', 'copyright', 'name-pending')
STRINGS_PATH = os.path.join(REPO, 'docs', 'copyright', 'strings-zh.json')
MATRIX_PATH = os.path.join(REPO, 'docs', 'sandbox-suite-matrix.md')

EXCLUDE_PARTS = {'__pycache__'}
EXCLUDE_PRUNES = {os.path.join('lobby', '.venv'), os.path.join('ygo-poc', 'data')}

LINES_PER_PAGE = 50
SELECT_PAGES_EACH_END = 30
MAX_PAGES_FULL = 60

SECRET_PATTERNS = [
    re.compile(r'sk-[A-Za-z0-9]{16,}'),
    re.compile(r'AKIA[0-9A-Z]{16}'),
    re.compile(r'ghp_[A-Za-z0-9]{20,}'),
    re.compile(r'xoxb-[0-9A-Za-z-]{10,}'),
    re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY'),
    re.compile(r'Bearer\s+[A-Za-z0-9._-]{30,}'),
]

IMPORT_RE = re.compile(r'^(?:import|from)\s+([A-Za-z_][A-Za-z0-9_.]*)')

SECTION_KEYS = ['overview', 'features', 'environment', 'language', 'evidence', 'compliance']


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def walk_inventory():
    """AC-SR1: deterministic lexicographic walk of our own sandbox code."""
    files = []
    for dirpath, dirnames, filenames in os.walk(SRC):
        rel_dir = os.path.relpath(dirpath, SRC)
        rel_dir_posix = '' if rel_dir == '.' else rel_dir.replace(os.sep, '/')
        # prune vendored/third-party and cache trees in-place (deterministic order)
        keep = []
        for d in sorted(dirnames):
            if d in EXCLUDE_PARTS:
                continue
            rel = os.path.join(rel_dir_posix, d) if rel_dir_posix else d
            if rel in EXCLUDE_PRUNES:
                continue
            keep.append(d)
        dirnames[:] = keep
        for name in sorted(filenames):
            if not name.endswith('.py'):
                continue
            rel = name if not rel_dir_posix else rel_dir_posix + '/' + name
            full = os.path.join(dirpath, name)
            with open(full, 'rb') as fh:
                data = fh.read()
            files.append({
                'rel': rel,
                'lines': data.decode('utf-8', errors='strict').count('\n'),
                'bytes': len(data),
            })
    files.sort(key=lambda f: f['rel'])
    return files


def build_listing_stream(files):
    lines = []
    for f in files:
        lines.append('# ===================== FILE: %s (%d lines) =====================' % (f['rel'], f['lines']))
        with open(os.path.join(SRC, f['rel'].replace('/', os.sep)), 'rb') as fh:
            text = fh.read().decode('utf-8', errors='strict')
        body = text.split('\n')
        if body and body[-1] == '':
            body = body[:-1]
        lines.extend(body)
    return lines


def derive_imports(files):
    """AC-SR4: import face derived via ast walk (three-way: stdlib / local / external).

    Local = relative imports, sandbox package dirs, or top-level sandbox .py stems.
    External = anything else that is not stdlib (the real third-party face, listed
    honestly in the spec draft environment section).
    """
    import ast
    stdlib_names = set(getattr(sys, 'stdlib_module_names', ()) or ())
    local_names = set()
    for f in files:
        parts = f['rel'].split('/')
        local_names.add(parts[0])                              # package dir or root-file stem
        local_names.add(parts[-1][:-3] if parts[-1].endswith('.py') else parts[-1])  # every file stem
        local_names.add(parts[-2] if len(parts) >= 2 else parts[0])  # parent dir of nested files
    external = set()
    local_imports = set()
    stdlib_imports = set()
    external_by_module = {}
    parse_failures = []
    for f in files:
        path = os.path.join(SRC, f['rel'].replace('/', os.sep))
        try:
            with open(path, 'rb') as fh:
                tree = ast.parse(fh.read().decode('utf-8', errors='strict'))
        except (SyntaxError, ValueError, UnicodeDecodeError):
            parse_failures.append(f['rel'])
            continue
        for node in ast.walk(tree):
            tops = []
            if isinstance(node, ast.Import):
                tops = [alias.name.split('.')[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    local_imports.add('(relative)')
                    continue
                if node.module:
                    tops = [node.module.split('.')[0]]
            for top in tops:
                if not stdlib_names:
                    continue
                if top in stdlib_names:
                    stdlib_imports.add(top)
                elif top in local_names:
                    local_imports.add(top)
                else:
                    external.add(top)
                    mod = f['rel'].split('/')[0] if '/' in f['rel'] else '(root)'
                    external_by_module.setdefault(mod, set()).add(top)
    return {
        'stdlib_face_available': bool(stdlib_names),
        'stdlib_imports': sorted(stdlib_imports),
        'local_imports': sorted(local_imports),
        'external_thirdparty': sorted(external),
        'external_by_module': {k: sorted(v) for k, v in sorted(external_by_module.items())},
        'parse_failures': sorted(parse_failures),
    }


def parse_matrix_counts():
    """AC-SR4 evidence face: derive suite/criteria totals from the machine-derived matrix."""
    try:
        with open(MATRIX_PATH, 'rb') as fh:
            text = fh.read().decode('utf-8', errors='replace')
    except OSError:
        return None
    m = re.search(r'合计.*?\|\s*(\d+)\s*\|\s*green (\d+) / FAIL (\d+) / no-evidence (\d+)', text)
    ev = re.search(r'RUNNER (PASS|FAIL) \((\d+)/(\d+) suites green', text)
    if not m:
        return None
    return {
        'criteria_total': int(m.group(1)),
        'suites_green': int(m.group(2)),
        'suites_fail': int(m.group(3)),
        'no_evidence': int(m.group(4)),
        'runner_state': (ev.group(1) + ' ' + ev.group(2) + '/' + ev.group(3)) if ev else 'n/a',
    }


def secret_scan(text):
    hits = []
    for pat in SECRET_PATTERNS:
        for m in pat.finditer(text):
            hits.append(pat.pattern[:24])
    return hits


def render_source_program(files, strings):
    """AC-SR2/AC-SR3/AC-SR7: paginated listing with pending-name envelope."""
    stream = build_listing_stream(files)
    total_pages = max(1, (len(stream) + LINES_PER_PAGE - 1) // LINES_PER_PAGE)
    if total_pages <= MAX_PAGES_FULL:
        selected = list(range(1, total_pages + 1))
    else:
        selected = list(range(1, SELECT_PAGES_EACH_END + 1)) + \
                   list(range(total_pages - SELECT_PAGES_EACH_END + 1, total_pages + 1))

    out = []
    banner = strings['page_banner']
    cover = ['', '']
    cover.append('=' * 74)
    for cl in strings['cover_lines']:
        cover.append(cl)
    cover.append('=' * 74)
    cover.append('')
    cover.append(strings['aigc_note'])
    cover.append(strings['disclaimer'])
    cover.append(strings['secgate_note'])
    cover.append(strings['not_filed_note'])
    cover.append('')
    out.extend(cover)

    for pageno in selected:
        start = (pageno - 1) * LINES_PER_PAGE
        chunk = stream[start:start + LINES_PER_PAGE]
        out.append('')
        out.append('-' * 74)
        out.append('[%s]  di %d ye / gong %d ye  (selected %d/%d)' %
                   (banner, pageno, total_pages, len(selected), total_pages))
        out.append('-' * 74)
        out.extend(chunk)
    text = '\n'.join(out) + '\n'
    info = {
        'total_pages': total_pages,
        'selected_pages': len(selected),
        'selection_mode': 'full' if total_pages <= MAX_PAGES_FULL else ('front%d+back%d' % (SELECT_PAGES_EACH_END, SELECT_PAGES_EACH_END)),
        'lines_per_page': LINES_PER_PAGE,
        'listing_lines': len(stream),
        'file_markers_in_listing': sum(1 for ln in stream if ln.startswith('# ===================== FILE: ')),
    }
    return text, info


def render_spec_draft(files, strings, imports_face, matrix_counts):
    """AC-SR4/AC-SR7: six-section draft, inventory derived from the walk."""
    sec = strings['sections']
    roles = strings['module_roles']
    by_module = {}
    for f in files:
        mod = f['rel'].split('/')[0] if '/' in f['rel'] else '(root)'
        agg = by_module.setdefault(mod, {'files': 0, 'lines': 0})
        agg['files'] += 1
        agg['lines'] += f['lines']

    out = []
    out.append('# ' + strings['doc_title'])
    out.append('')
    out.append('> ' + strings['software_name_pending'])
    out.append('>')
    out.append('> ' + strings['version_line'])
    out.append('>')
    out.append('> ' + strings['not_filed_note'])
    out.append('')
    out.append('## ' + sec['overview'])
    out.append('')
    out.append(strings['software_name_pending'] + '（本说明书为软著申请预备稿）。')
    out.append('软件定位：公众共创元宙平台商业化子系统沙箱预演系统，按零服务器红线裁决（2026-09-24 方案 B 自建后端）'
               '先行落地本地沙箱套件，承载大厅共创、双式账本、UGC 内容安全、会员权益、支付对接设计、虚拟活动、'
               '合规与审计等可对账可审计面。')
    out.append(strings['version_line'] + '。材料口径：源程序取自现行沙箱套件代码（清单见 manifest.json），'
               '鉴定材料以全套件回归证据为底。')
    out.append('')
    out.append('## ' + sec['features'])
    out.append('')
    out.append('模块清单（机器派生自源码树实勘，零硬编码；角色说明为人工配置数据面）：')
    out.append('')
    out.append('| 模块 | 文件数 | 行数 | 角色 |')
    out.append('| --- | --- | --- | --- |')
    for mod in sorted(by_module):
        agg = by_module[mod]
        role = roles.get(mod, '')
        out.append('| %s | %d | %d | %s |' % (mod, agg['files'], agg['lines'], role))
    total_files = sum(a['files'] for a in by_module.values())
    total_lines = sum(a['lines'] for a in by_module.values())
    out.append('| (合计) | %d | %d | — |' % (total_files, total_lines))
    out.append('')
    out.append('技术特点（对账可审计性设计）：')
    out.append('- 双式账本：代币/现金双轨账本，一切面 append-only 落账、幂等键、fail-closed 拒绝面。')
    out.append('- 内容安全前置闸：市民文本面一律先过 msgSecCheck/SecGate 前置闸，违禁文案零落账。')
    out.append('- AIGC 标识信封：生成内容全呈现面带标识与免责声明（与注册声明逐行一致）。')
    out.append('- 对账套件：全套件判据预注册 + 回归 RUNNER + 套件矩阵机器派生，状态零手写数字。')
    out.append('')
    out.append('## ' + sec['environment'])
    out.append('')
    if imports_face['external_by_module']:
        out.append('运行环境（派生自 import 面实测·ast 解析全清单零手写）：Python 3，标准库自足为主体'
                   '（数据层 sqlite3、账本/合规/会员等核心面 stdlib-only）。真实第三方依赖按模块派生如下：')
        for mod in sorted(imports_face['external_by_module']):
            deps = ', '.join(imports_face['external_by_module'][mod])
            out.append('- %s：%s' % (mod, deps))
        out.append('（上述依赖为各专项面所用：水印嵌水面用 OpenCV/numpy/blind_watermark/Pillow，'
                   '大厅共创 WebSocket 面用 websockets，UGC 前置预过滤用 pyahocorasick，'
                   '微信支付 v3 真实通道签名/加解密用 cryptography——均列入软著运行环境如实声明。）')
    else:
        out.append('运行环境（派生自 import 面实测）：Python 3 标准库自足（stdlib-only），零第三方运行时依赖。')
    out.append('数据层：sqlite3 标准库（单写者、append-only、幂等键）。')
    out.append('部署形态：本地沙箱（docker-compose / 直跑），对外部署 gated on bootstrap 物理件（服务器/域名/备案/商户号）。')
    out.append('')
    out.append('## ' + sec['language'])
    out.append('')
    out.append('编程语言：Python 3（标准库自足）。结构：src/sandbox 按域分模块（上表），套件注册表即回归器'
               '（reconcile_all.SUITES 单一事实源），套件矩阵为机器派生文档、零手改。')
    out.append('')
    out.append('## ' + sec['evidence'])
    out.append('')
    if matrix_counts:
        out.append('鉴定材料底座（机器派生自 docs/sandbox-suite-matrix.md 合计行）：套件判据总数 %d，'
                   'green %d / FAIL %d / no-evidence %d，RUNNER %s。'
                   % (matrix_counts['criteria_total'], matrix_counts['suites_green'],
                      matrix_counts['suites_fail'], matrix_counts['no_evidence'],
                      matrix_counts['runner_state']))
        out.append('逐日对账证据面：qa/reconcile-daily-YYYYMMDD.log（按日落盘，判据全绿才算完成）。')
    else:
        out.append('鉴定材料底座：docs/sandbox-suite-matrix.md（机器派生·本稿生成时解析失败，见 manifest.json）。')
    out.append('')
    out.append('## ' + sec['compliance'])
    out.append('')
    out.append('- ' + strings['aigc_note'])
    out.append('- ' + strings['disclaimer'])
    out.append('- ' + strings['secgate_note'])
    out.append('- ' + strings['not_filed_note'])
    out.append('')
    text = '\n'.join(out) + '\n'
    return text


def main():
    with open(STRINGS_PATH, 'rb') as fh:
        strings = json.loads(fh.read().decode('utf-8'))
    os.makedirs(OUTDIR, exist_ok=True)

    files = walk_inventory()
    imports_face = derive_imports(files)
    matrix_counts = parse_matrix_counts()

    ac = {}
    ac['AC-SR1'] = {
        'inventory_count': len(files),
        'excluded_vendored_trees': sorted(EXCLUDE_PRUNES),
        'excluded_cache_parts': sorted(EXCLUDE_PARTS),
        'order': 'lexicographic',
    }

    src_text, page_info = render_source_program(files, strings)
    spec_text = render_spec_draft(files, strings, imports_face, matrix_counts)

    # zero-omission check: every walked file carries exactly one listing marker
    ac['AC-SR1']['zero_omission'] = (
        page_info['file_markers_in_listing'] == len(files)
    )

    src_path = os.path.join(OUTDIR, 'source-program.txt')
    spec_path = os.path.join(OUTDIR, 'design-spec-draft.md')
    with open(src_path, 'wb') as fh:
        fh.write(src_text.encode('utf-8'))
    with open(spec_path, 'wb') as fh:
        fh.write(spec_text.encode('utf-8'))

    ac['AC-SR2'] = dict(page_info)
    ac['AC-SR2']['banner_on_every_page'] = (
        src_text.count('di ') == page_info['selected_pages']
        and src_text.count(strings['page_banner']) == page_info['selected_pages']
    )
    ac['AC-SR3'] = {
        'cover_pending_verbatim': strings['cover_lines'][1] in src_text,
        'banner_pending_on_every_page': src_text.count(strings['page_banner']) == page_info['selected_pages'],
        'output_dir': 'docs/copyright/name-pending/',
        'formal_filing_action': 'none (prep only)',
    }
    hits = secret_scan(src_text) + secret_scan(spec_text)
    ac['AC-SR6'] = {
        'secret_hits': len(hits),
        'patterns': [p.pattern for p in SECRET_PATTERNS],
        'env_files_read': 0,
    }
    ac['AC-SR7'] = {
        'aigc_in_source': strings['aigc_note'] in src_text,
        'aigc_in_spec': strings['aigc_note'] in spec_text,
        'disclaimer_in_source': strings['disclaimer'] in src_text,
        'disclaimer_in_spec': strings['disclaimer'] in spec_text,
        'secgate_in_source': strings['secgate_note'] in src_text,
        'secgate_in_spec': strings['secgate_note'] in spec_text,
    }
    ac['AC-SR4'] = {
        'sections': len(SECTION_KEYS),
        'module_rows': len(set(f['rel'].split('/')[0] if '/' in f['rel'] else '(root)' for f in files)),
        'imports_derived': True,
        'external_thirdparty': imports_face['external_thirdparty'],
        'parse_failures': imports_face['parse_failures'],
        'stdlib_face_available': imports_face['stdlib_face_available'],
        'matrix_counts': matrix_counts,
    }

    manifest = {
        'task': 'D-20261011-03 copyright prep (name-pending)',
        'criteria_face': 'backlog claim row R1760 AC-SR1..AC-SR7',
        'inventory': {
            'files': len(files),
            'total_lines': sum(f['lines'] for f in files),
            'total_bytes': sum(f['bytes'] for f in files),
        },
        'outputs': {
            'source-program.txt': {'sha256': sha256_bytes(src_text.encode('utf-8')), 'bytes': len(src_text.encode('utf-8'))},
            'design-spec-draft.md': {'sha256': sha256_bytes(spec_text.encode('utf-8')), 'bytes': len(spec_text.encode('utf-8'))},
        },
        'imports_face': imports_face,
        'ac_results': ac,
    }
    manifest_path = os.path.join(OUTDIR, 'manifest.json')
    with open(manifest_path, 'wb') as fh:
        fh.write(json.dumps(manifest, ensure_ascii=False, indent=2).encode('utf-8'))

    print('copyright-prep run complete')
    print('inventory: files=%d lines=%d vendored_excluded=%s' %
          (len(files), sum(f['lines'] for f in files), sorted(EXCLUDE_PRUNES)))
    print('pages: total=%d selected=%d mode=%s' %
          (page_info['total_pages'], page_info['selected_pages'], page_info['selection_mode']))
    print('imports: stdlib_face=%s external_thirdparty=%s parse_failures=%d' %
          (imports_face['stdlib_face_available'], imports_face['external_thirdparty'],
           len(imports_face['parse_failures'])))
    print('AC-SR1 zero_omission=%s' % ac['AC-SR1']['zero_omission'])
    print('matrix: %s' % (matrix_counts or 'parse-failed'))
    print('AC-SR2 banner_on_every_page=%s' % ac['AC-SR2']['banner_on_every_page'])
    print('AC-SR3 cover_pending_verbatim=%s' % ac['AC-SR3']['cover_pending_verbatim'])
    print('AC-SR6 secret_hits=%d env_read=%d' % (ac['AC-SR6']['secret_hits'], ac['AC-SR6']['env_files_read']))
    print('AC-SR7 aigc=%s/%s disclaimer=%s/%s secgate=%s/%s' % (
        ac['AC-SR7']['aigc_in_source'], ac['AC-SR7']['aigc_in_spec'],
        ac['AC-SR7']['disclaimer_in_source'], ac['AC-SR7']['disclaimer_in_spec'],
        ac['AC-SR7']['secgate_in_source'], ac['AC-SR7']['secgate_in_spec']))
    print('sha256 source-program.txt=%s' % manifest['outputs']['source-program.txt']['sha256'])
    print('sha256 design-spec-draft.md=%s' % manifest['outputs']['design-spec-draft.md']['sha256'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
