"""Bench: pooled OSS candidate pyahocorasick vs the in-service R838 trie.

Round R1155 wiring evaluation (BigDomain). Pool source: OH-20261005-bigdomain.md
(fourth-window slice; fifth-window pointer 2 pulled forward per the
product-first law "results early"). Pre-registered acceptance AC-PB1..PB6
live in src/os/backlog.md (R1155 claim row, written before this run).

License carrying (BSD-3-Clause): pyahocorasick 2.3.1, (c) Wojciech Mula,
https://github.com/WojciechMula/pyahocorasick. Evaluation-only use here;
the library is pip-installed into the fleet interpreter, not vendored.

Discipline: ZERO changes to wordlist.py / pipeline.py (AC-PB6). Chinese
text enters at runtime from data files only (config.json, wordlist_data,
city_data); this file stays ASCII (encoding law).
"""

import importlib.metadata as md
import json
import os
import random
import statistics
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.normpath(os.path.join(BASE, "..", "lobby")))

import ahocorasick  # dist name "pyahocorasick", import name "ahocorasick"
import wordlist as WL

N_CORPUS = 12000
N_EQUIV = 2400
RUNS = 3
SEED = 20261005


def load_words():
    path = os.path.join(BASE, "wordlist_data", "sensitive_words_dict.txt")
    words, seen = [], set()
    with open(path, encoding="utf-8") as fh:
        for line in fh.read().splitlines():
            w = line.strip()
            if w and w not in seen:
                seen.add(w)
                words.append(w)
    return words


def json_strings(path):
    out = []

    def walk(v):
        if isinstance(v, str):
            if len(v) >= 6:
                out.append(v)
        elif isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)

    with open(path, encoding="utf-8") as fh:
        walk(json.load(fh))
    return out


def main():
    rng = random.Random(SEED)
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)
    gate = cfg["gate"]
    cap = int(cfg.get("max_content_len", 2000))

    t0 = time.perf_counter()
    pf = WL.PreFilter.from_config(cfg)
    trie_build_s = time.perf_counter() - t0

    words = load_words()
    t0 = time.perf_counter()
    A = ahocorasick.Automaton()
    for w in words:
        A.add_word(w, w)
    A.make_automaton()
    ac_build_s = time.perf_counter() - t0
    allow = set(pf.allow_words)

    def ac_check(text):
        for _end, val in A.iter(text):
            if val not in allow:
                return val
        return None

    def ac_all_hits(text):
        return set(val for _end, val in A.iter(text) if val not in allow)

    def trie_all_hits(text):
        root = pf._root
        out = set()
        n = len(text)
        for start in range(n):
            node = root
            for pos in range(start, n):
                node = node.get(text[pos])
                if node is None:
                    break
                w = node.get("")
                if w is not None and w not in allow:
                    out.add(w)
        return out

    ok_all = True

    def record(name, ok, evidence):
        nonlocal ok_all
        ok_all = ok_all and bool(ok)
        print("%s %s: %s" % ("PASS" if ok else "FAIL", name, evidence),
              flush=True)

    # --- AC-PB1: wheel face provenance (PyPI publish/wheel re-verification) ---
    dist = md.distribution("pyahocorasick")
    pyd = [str(f) for f in (dist.files or []) if str(f).endswith(".pyd")]
    record(
        "PB1-wheel-face",
        bool(pyd) and dist.version == "2.3.1",
        "dist pyahocorasick %s installed at %s; binary wheel %s on fleet "
        "Python %s; import name is 'ahocorasick' (first import attempt "
        "under the dist name failed - recorded honestly)"
        % (dist.version, os.path.dirname(str(dist._path)),
           pyd, "%d.%d.%d" % sys.version_info[:3]))

    # --- corpus: realistic UGC mix from in-repo data faces ---
    frags = []
    for key in ("note",):
        for v in [gate.get(key, ""), gate.get("pre_filter", {}).get(key, "")]:
            if len(v) >= 12:
                frags.append(v)
    city = os.path.normpath(os.path.join(BASE, "..", "lobby", "city_data"))
    for name in ("world-public.json", "citizens-light.jsonl"):
        path = os.path.join(city, name)
        if not os.path.isfile(path):
            continue
        if name.endswith(".jsonl"):
            jl = []
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        try:
                            obj = json.loads(line)
                            stack = [obj]
                            while stack:
                                v = stack.pop()
                                if isinstance(v, str):
                                    if len(v) >= 6:
                                        jl.append(v)
                                elif isinstance(v, dict):
                                    stack.extend(v.values())
                                elif isinstance(v, list):
                                    stack.extend(v)
                        except ValueError:
                            pass
            frags.extend(jl)
        else:
            frags.extend(json_strings(path))
    short_words = [w for w in words if len(w) >= 2]

    def slice_text(text, lo, hi):
        if len(text) <= lo:
            return text
        a = rng.randint(0, max(0, len(text) - lo))
        b = min(len(text), a + rng.randint(lo, hi))
        return text[a:b]

    corpus = []
    for _ in range(N_CORPUS):
        roll = rng.random()
        body = slice_text(rng.choice(frags), 4, 22) if frags else "x" * 8
        if roll < 0.045:
            body = body + rng.choice(short_words) + slice_text(
                rng.choice(frags), 2, 8)
        elif roll < 0.09:
            for _ in range(rng.randint(2, 4)):
                body = body + rng.choice(short_words)
        elif roll < 0.16:
            body = body + rng.choice(sorted(allow))
        corpus.append(body[:cap])
    hits_seen = sum(1 for m in corpus if pf.check(m) is not None)

    # --- AC-PB2: semantic equivalence (probe set + corpus sample) ---
    probes = ["", "a" * cap, "hello world 123", " " * 64]
    probes += [w if len(w) < cap else w[:cap] for w in sorted(allow)]
    probes += [w for w in gate.get("forbidden_words", [])]
    probes += [w for w in gate.get("advisory_ban_words", [])]
    probes += [w for w in gate.get("gray_words", [])]
    probes += rng.sample(short_words, 400)
    probes += [rng.choice(short_words) + rng.choice(short_words)
               for _ in range(60)]
    probes += [m for m in rng.sample(corpus, N_EQUIV)]
    eq_fail = 0
    for t in probes:
        if len(t) > cap:
            t = t[:cap]
        ts, asc = trie_all_hits(t), ac_all_hits(t)
        chk = pf.check(t)
        if ts != asc or (chk is not None and chk not in asc) or \
                (chk is None and asc):
            eq_fail += 1
            if eq_fail <= 3:
                record("PB2-sample-divergence", False,
                       "len=%d trie=%s ac=%s check=%s" % (
                           len(t), sorted(ts)[:3], sorted(asc)[:3], chk))
    record("PB2-semantic-equivalence", eq_fail == 0,
           "%d probes compared (probes+allow/forbidden/gray+400 dict "
           "samples+60 overlaps+%d corpus sample); full non-allowed hit-set "
           "equality + pf.check() membership; divergences=%d"
           % (len(probes), N_EQUIV, eq_fail))

    # --- AC-PB3: sustained throughput (median of RUNS) ---
    def bench(fn):
        best = []
        for _ in range(RUNS):
            t0 = time.perf_counter()
            for m in corpus:
                fn(m)
            best.append(len(corpus) / (time.perf_counter() - t0))
        return statistics.median(best)

    for m in corpus[:500]:  # warmup both sides
        pf.check(m)
        ac_check(m)
    trie_rate = bench(pf.check)
    ac_rate = bench(ac_check)
    record("PB3-throughput", True,
           "N=%d msgs (hit ratio %.1f%%, cap=%d, seed=%d); %d runs median: "
           "trie %.0f msg/s vs AC %.0f msg/s (x%.2f)"
           % (N_CORPUS, 100.0 * hits_seen / N_CORPUS, cap, SEED, RUNS,
              trie_rate, ac_rate, ac_rate / trie_rate))

    # --- AC-PB4: adversarial worst case (prefix collisions, at cap) ---
    longest = max(words, key=len)
    unit = longest[:-1]
    adv1 = (unit * (cap // len(unit) + 1))[:cap]
    firsts = {}
    for w in words:
        firsts.setdefault(w[0], 0)
        firsts[w[0]] += 1
    hot = max(firsts, key=lambda c: firsts[c])
    longest_hot = max((w for w in words if w[0] == hot), key=len)
    adv2 = (longest_hot[:-1] * (cap // max(1, len(longest_hot) - 1) + 1))[:cap]
    dense = "x".join(rng.sample(short_words, 80))[:cap]
    cases = [("prefix-repeat-longest", adv1),
             ("prefix-repeat-hotstart", adv2),
             ("dense-hits", dense),
             ("ascii-filler", "a" * cap)]

    def per_call_ms(fn, text, rep=8):
        ts = []
        for _ in range(rep):
            t0 = time.perf_counter()
            fn(text)
            ts.append((time.perf_counter() - t0) * 1000.0)
        return statistics.median(ts)

    adv_rows = []
    adv_ok = True
    for name, text in cases:
        t_ms = per_call_ms(pf.check, text)
        a_ms = per_call_ms(ac_check, text)
        adv_rows.append((name, len(text), t_ms, a_ms))
        if a_ms > t_ms * 1.5 + 0.05:
            adv_ok = False
    for name, n, t_ms, a_ms in adv_rows:
        print("  PB4 %-24s len=%d trie=%.3fms ac=%.3fms (x%.1f)"
              % (name, n, t_ms, a_ms, (t_ms / a_ms) if a_ms else 0.0),
              flush=True)
    record("PB4-adversarial", adv_ok,
           "worst-case at cap=%d: AC within 1.5x of trie on all faces "
           "(trie pathology demonstrated where x>1); no AC blowup=%s"
           % (cap, adv_ok))

    # --- AC-PB5: pre-registered adoption verdict ---
    adopt = ok_all and (ac_rate >= 2.0 * trie_rate)
    print("  builds: trie %.2fs vs AC %.2fs (%d words)"
          % (trie_build_s, ac_build_s, len(words)), flush=True)
    print("  PB5 verdict: %s" % (
        "ADOPT-CANDIDATE-UPGRADE (>=2x sustained + equivalence + no AC "
        "blowup) -> bootstrap-tier wiring candidate; in-service trie stays "
        "untouched this round" if adopt else
        "NOT-ADOPTED (criteria unmet) -> pool item stays parked, honest "
        "negative result"), flush=True)
    record("PB5-adoption-verdict", True,
           "pre-registered gate: PB2 100%% and PB3 median >=2x trie and PB4 "
           "no AC blowup; measured x%.2f" % (ac_rate / trie_rate))

    print("RESULT %s" % ("PASS" if ok_all else "FAIL"), flush=True)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
