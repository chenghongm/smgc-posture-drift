#!/usr/bin/env python3
import argparse, json, subprocess, tempfile, pathlib, shlex

def load_jsonl(p):
    with open(p, 'r', encoding='utf-8') as f:
        return [json.loads(l) for l in f if l.strip()]

def run_generate(model, adapter, prompt, seed, temp, top_p, max_tokens=256):
    import subprocess

    cmd = [
        "mlx_lm.generate",
        "--model", model,
        "--prompt", prompt,
        "--seed", str(seed),
        "--temp", str(temp),
        "--top-p", str(top_p),
        "--max-tokens", str(max_tokens),
    ]
    if adapter:
        cmd += ["--adapter-path", adapter]

    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # 如果命令失败，把错误抛出来（不要静默写空/写报错当结果）
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout or "").strip())

    raw = p.stdout or ""
    lines = raw.splitlines()

    # 提取两条 ========= 之间的正文
    idx = [i for i,l in enumerate(lines) if l.strip() == "=========="]
    if len(idx) >= 2:
        body = "\n".join(lines[idx[0]+1:idx[1]]).strip()
    else:
        keep = []
        for l in lines:
            s = l.strip()
            if not s:
                continue
            if s.startswith("Prompt:") or s.startswith("Generation:") or s.startswith("Peak memory:"):
                continue
            if s == "==========":
                continue
            keep.append(l)
        body = "\n".join(keep).strip()

    return body





def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--adapter", default="")
    ap.add_argument("--eps", required=True)
    ap.add_argument("--temps", nargs="+", type=float, required=True)
    ap.add_argument("--top_ps", nargs="+", type=float, required=True)
    ap.add_argument("--seeds", nargs="+", type=int, required=True)
    ap.add_argument("--max_tokens", type=int, default=256)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    EPS = load_jsonl(args.eps)
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for item in EPS:
        pid = item.get("id","")
        prompt = item["messages"][-1]["content"]

        for temp in args.temps:
            for top_p in args.top_ps:
                for seed in args.seeds:
                    try:
                        text = run_generate(args.base, args.adapter, prompt, seed, temp, top_p, args.max_tokens)
                    except Exception as e:
                        text = f"[EVAL_ERROR] {e}"
                    rows.append({
                        "prompt_id": pid,
                        "seed": seed,
                        "temp": temp,
                        "top_p": top_p,
                        "adapter": args.adapter or "BASE",
                        "text": text
                    })

    with open(args.out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()
