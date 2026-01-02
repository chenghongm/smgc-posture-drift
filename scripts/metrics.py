#!/usr/bin/env python3
import argparse, json, math, re
from collections import Counter, defaultdict
from itertools import combinations

PHRASES = ["我作为", "从工程角度", "作为一个", "在本回答中", "下面我们", "总体来说"]

def tokenize(t):
    # 极简：空白切词 + 去标点
    t = re.sub(r"[^\w\u4e00-\u9fff\s]", " ", t)
    return [w for w in t.split() if w]

def ngrams(tokens, n):
    return list(zip(*[tokens[i:] for i in range(n)])) if len(tokens) >= n else []

def distinct_n(tokens, n):
    ng = ngrams(tokens, n)
    return len(set(ng)) / max(1, len(ng))

def token_entropy(tokens):
    cnt = Counter(tokens)
    total = sum(cnt.values())
    H = 0.0
    for c in cnt.values():
        p = c/total
        H -= p * math.log(p + 1e-12)
    return H

# 简易 BLEU（1-4gram 平均）
def bleu(ref_tokens, hyp_tokens):
    def prec(n):
        ref_ng = Counter(ngrams(ref_tokens, n))
        hyp_ng = Counter(ngrams(hyp_tokens, n))
        if not hyp_ng: return 0.0
        overlap = sum((hyp_ng & ref_ng).values())
        return overlap / sum(hyp_ng.values())
    ps = [prec(n) for n in [1,2,3,4]]
    bp = math.exp(1 - len(ref_tokens)/len(hyp_tokens)) if len(hyp_tokens) < len(ref_tokens) else 1.0
    # 避免 log(0)
    s = sum([math.log(p+1e-12) for p in ps]) / 4.0
    return bp * math.exp(s)

def skeleton_signature(text, K=4):
    paras = [p for p in text.split("\n\n") if p.strip()]
    firsts = []
    for p in paras:
        sent = p.strip().splitlines()[0]
        toks = tokenize(sent)[:K]
        firsts.append(" ".join(toks))
    hits = [ph for ph in PHRASES if ph in text]
    return {
        "para_count": len(paras),
        "firsts": firsts,
        "hits": hits
    }

def jaccard(a, b):
    sa, sb = set(a), set(b)
    if not sa and not sb: return 1.0
    return len(sa & sb) / max(1, len(sa | sb))

def skel_sim(sa, sb):
    # 组合相似度
    s1 = 1.0 if sa["para_count"] == sb["para_count"] else 0.0
    s2 = jaccard(sa["firsts"], sb["firsts"])
    s3 = jaccard(sa["hits"], sb["hits"])
    return (s1 + s2 + s3) / 3.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = []
    with open(args.inp, "r", encoding="utf-8") as f:
        for l in f:
            if l.strip():
                rows.append(json.loads(l))

    # 逐条算 Distinct / Entropy / Skeleton
    for r in rows:
        toks = tokenize(r["text"])
        r["distinct2"] = distinct_n(toks, 2)
        r["distinct3"] = distinct_n(toks, 3)
        r["entropy"]   = token_entropy(toks)
        r["skeleton"]  = skeleton_signature(r["text"])

    # Self-BLEU & Skeleton Similarity：按 prompt_id 分组
    grouped = defaultdict(list)
    for r in rows:
        key = (r["prompt_id"], r["temp"], r["top_p"], r["adapter"])
        grouped[key].append(r)

    for key, items in grouped.items():
        # Self-BLEU
        bleus = []
        sks   = []
        for a, b in combinations(items, 2):
            ta = tokenize(a["text"])
            tb = tokenize(b["text"])
            bleus.append(bleu(ta, tb))
            sks.append(skel_sim(a["skeleton"], b["skeleton"]))
        avg_bleu = sum(bleus)/len(bleus) if bleus else 0.0
        avg_skel = sum(sks)/len(sks) if sks else 0.0
        for it in items:
            it["self_bleu"] = avg_bleu
            it["skeleton_sim"] = avg_skel

    with open(args.out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()
