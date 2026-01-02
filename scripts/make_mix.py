#!/usr/bin/env python3
import argparse, json, random, pathlib

def load_jsonl(p):
    with open(p, 'r', encoding='utf-8') as f:
        return [json.loads(l) for l in f if l.strip()]

def dump_jsonl(rows, out):
    with open(out, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--d00", required=True)
    ap.add_argument("--d10", required=True)
    # ap.add_argument("--p", type=float, required=True, help="framing ratio, e.g. 0.005 for 0.5%")
    ap.add_argument("--p", type=float, required=True, help="framing ratio, e.g. 0.005 for 0.5%%")

    ap.add_argument("--total_N", type=int, required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--mode", choices=["repeat","once"], default="repeat")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    random.seed(args.seed)
    D00 = load_jsonl(args.d00)
    D10 = load_jsonl(args.d10)

    n_f = max(1, int(args.total_N * args.p))
    n_c = args.total_N - n_f

    # sample clean
    clean = random.sample(D00, n_c) if len(D00) >= n_c else [random.choice(D00) for _ in range(n_c)]

    # sample framing
    if args.mode == "repeat":
        base = random.sample(D10, min(len(D10), n_f))
        framing = []
        while len(framing) < n_f:
            framing.extend(base)
        framing = framing[:n_f]
    else:  # once
        framing = random.sample(D10, n_f) if len(D10) >= n_f else [random.choice(D10) for _ in range(n_f)]

    mix = clean + framing
    random.shuffle(mix)
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    dump_jsonl(mix, args.out)

if __name__ == "__main__":
    main()
