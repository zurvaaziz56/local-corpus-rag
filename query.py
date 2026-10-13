#!/usr/bin/env python3
"""Hybrid search over the corpus: semantic (bge-m3 via Ollama) + lexical, with metadata filters.

Usage:
  python3 query.py "Over to You task" --client education-publisher --status final -n 5
  python3 query.py "security page copy" --client ai-startup
Filters: --client --outcome --status --min-words --lexical-only
"""
import argparse, json, math, re, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IDX  = ROOT / ".obsidian-semantic-index.json"
OLLAMA, MODEL = "http://localhost:11434", "bge-m3"

def embed(text):
    body = json.dumps({"model": MODEL, "prompt": text, "keep_alive": "15m"}).encode()
    req = urllib.request.Request(f"{OLLAMA}/api/embeddings", body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["embedding"]

def cos(a, b):
    d = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a)); nb = math.sqrt(sum(y*y for y in b))
    return 0.0 if not na or not nb else d/(na*nb)

def meta(p):
    try: t = (ROOT/p).read_text(encoding="utf-8")[:1200]
    except Exception: return {}, ""
    m = {}
    for k in ("client","outcome","status","type","words","gig","lesson","asset","title"):
        r = re.search(rf'^{k}:\s*"?([^"\n]+)"?', t, re.M)
        if r: m[k] = r.group(1).strip()
    return m, t

def snippet(p, terms):
    try: body = (ROOT/p).read_text(encoding="utf-8").split("\n---\n",1)[-1]
    except Exception: return ""
    def ok(l):
        s = l.strip()
        return len(s.split()) > 10 and not s.startswith((">", "#", "---", "Original"))
    cands = [l for l in body.split("\n") if ok(l)]
    best, bs = "", -1
    for l in cands:
        sc = sum(l.lower().count(t) for t in terms)
        if sc > bs: best, bs = l, sc
    return best.strip()[:170] if bs > 0 else (cands[0].strip()[:170] if cands else "")

ap = argparse.ArgumentParser()
ap.add_argument("query"); ap.add_argument("-n","--limit",type=int,default=6)
ap.add_argument("--client"); ap.add_argument("--outcome"); ap.add_argument("--status")
ap.add_argument("--min-words",type=int,default=0); ap.add_argument("--lexical-only",action="store_true")
a = ap.parse_args()

idx = json.loads(IDX.read_text())
terms = [w for w in re.findall(r'\w+', a.query.lower()) if len(w) > 3]
qv = None if a.lexical_only else embed(a.query)

rows = []
for path, rec in idx.get("notes", {}).items():
    m, head = meta(path)
    if a.client  and a.client.lower()  not in m.get("client","").lower():  continue
    if a.outcome and a.outcome.lower() != m.get("outcome","").lower():     continue
    if a.status  and a.status.lower()  != m.get("status","").lower():      continue
    if a.min_words and int(m.get("words",0) or 0) < a.min_words:           continue
    vecs = rec.get("vecs") or rec.get("vectors") or []
    sem  = max((cos(qv,v) for v in vecs), default=0.0) if qv else 0.0
    try: full = (ROOT/path).read_text(encoding="utf-8").lower()
    except Exception: full = ""
    hits = sum(full.count(t) for t in terms)
    lex  = min(hits/12.0, 1.0)
    score = lex if a.lexical_only else 0.72*sem + 0.28*lex
    rows.append((score, sem, lex, path, m))

rows.sort(reverse=True, key=lambda r: r[0])
if not rows: print("No matches for those filters."); sys.exit(0)
print(f'query: "{a.query}"' + (f"  [filters: {' '.join(f'{k}={v}' for k,v in vars(a).items() if v and k not in ('query','limit'))}]" if any([a.client,a.outcome,a.status]) else ""))
print("-"*100)
for i,(s,sem,lex,p,m) in enumerate(rows[:a.limit],1):
    tag = " ".join(f"{k}={m[k]}" for k in ("client","outcome","status","gig","lesson") if k in m)
    print(f"{i}. {s:.3f} (sem {sem:.2f} lex {lex:.2f})  {p}")
    if tag: print(f"   [{tag}]")
    sn = snippet(p, terms)
    if sn: print(f"   \"{sn}\"")
