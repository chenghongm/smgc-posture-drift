#!/usr/bin/env python3
import argparse
import json
import re
import statistics
import subprocess
from pathlib import Path

# 你可以按需扩展/收缩这个表；它只用于 Stage-1 的“姿态/元叙事密度”对照
META_PATTERNS = [
    r"本质", r"机制", r"从.+角度", r"换句话说", r"也就是说", r"归根结底",
    r"在计算上", r"模型", r"对齐", r"语义", r"框架", r"过程", r"系统",
    r"我替换了", r"我会", r"我称为", r"你给的不是", r"这叫"
]

def load_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def sas2(text: str) -> float:
    if not text:
        return 0.0
    n = max(len(text), 1)

    bullets = len(re.findall(r"(?m)^\s*(?:\d+[\.\)、]|[-*•])\s+", text))
    colons  = text.count("：") + text.count(":")
    quotes  = text.count("“") + text.count("”") + text.count('"') + text.count("'")

    meta_hits = sum(len(re.findall(p, text)) for p in META_PATTERNS)

    # 与你之前一致的权重：可解释、可复现
    return (2.0 * meta_hits + 1.0 * bullets + 0.3 * colons + 0.1 * quotes) / n

def summarize(name: str, rows):
    lens = [len(r.get("text", "")) for r in rows]
    sas  = [sas2(r.get("text", "")) for r in rows]

    def pctl(xs, q):
        xs = sorted(xs)
        if not xs:
            return 0
        k = int(round((len(xs)-1) * q))
        return xs[k]

    return {
        "name": name,
        "n": len(rows),
        "mean_len": round(statistics.mean(lens), 1) if lens else 0.0,
        "p50_len": int(statistics.median(lens)) if lens else 0,
        "p10_len": int(pctl(lens, 0.10)) if lens else 0,
        "p90_len": int(pctl(lens, 0.90)) if lens else 0,
        "mean_sas2": round(statistics.mean(sas), 4) if sas else 0.0,
        "p50_sas2": round(statistics.median(sas), 4) if sas else 0.0,
        "max_sas2": round(max(sas), 4) if sas else 0.0,
    }

def run_metrics(metrics_py: Path, inp: Path, out: Path):
    # 直接调用你现有的 eval/scripts/metrics.py
    cmd = ["python3", str(metrics_py), "--in", str(inp), "--out", str(out)]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"metrics.py failed:\n{p.stderr}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="Path to base.neutral.clean.jsonl")
    ap.add_argument("--adapt", required=True, help="Path to A_mix_p0005.neutral.clean.jsonl")
    ap.add_argument("--with-metrics", action="store_true",
                    help="Also run eval/scripts/metrics.py to produce *.metrics.jsonl")
    args = ap.parse_args()

    base_path = Path(args.base)
    adapt_path = Path(args.adapt)

    base_rows = load_jsonl(base_path)
    adapt_rows = load_jsonl(adapt_path)

    print(summarize("base", base_rows))
    print(summarize("A_mix_p0005", adapt_rows))

    if args.with_metrics:
        metrics_py = Path(__file__).parent / "metrics.py"
        base_out = base_path.with_suffix(".metrics.jsonl")
        adapt_out = adapt_path.with_suffix(".metrics.jsonl")

        run_metrics(metrics_py, base_path, base_out)
        run_metrics(metrics_py, adapt_path, adapt_out)

        print(f"Wrote: {base_out}")
        print(f"Wrote: {adapt_out}")

if __name__ == "__main__":
    main()
