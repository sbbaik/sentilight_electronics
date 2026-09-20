"""Vocabulary series (V): train ByteLevel-BPE tokenizers of several sizes on the clean pretraining
corpus, encode the corpus for each, and measure SFT sequence lengths so block_size 256 is known to
be sufficient before any model is trained.

Tokenizer recipe mirrors backend/models/compact_llm/tokenizer/tokenizer.json:
  normalizer NFKC -> pre-tokenizer ByteLevel(add_prefix_space=False) -> BPE -> ByteLevel decoder,
  special tokens at ids 0..9: <pad> <unk> <bos> <eos> <|system|> <|user|> <|assistant|>
  <|sentilight|> <|json|> <|tasmota|>.
The original 24k tokenizer was trained on an unknown (pre-audit) corpus; V24k here is retrained on
the clean corpus so that "vocabulary size" and "tokenizer provenance" can be separated.

Outputs: backend/models/compact_llm/tokenizer_vocab_series/<V>/{tokenizer.json,tokenizer_config.json,
         pretrain_tokens.npy, mixed_pretrain_token_report.json}
         backend/reports/scale_grid_vocab/vocab_series_build.{json,md}
Usage: python tools/build_vocab_series.py [--sizes 4000 8000 16000 24000]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import statistics as st
import subprocess
import sys
from pathlib import Path

from tokenizers import Tokenizer, decoders, models, normalizers, pre_tokenizers, processors, trainers

REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = REPO_ROOT / "backend" / "models" / "compact_llm"
sys.path.insert(0, str(REPO_ROOT / "backend" / "models"))
from compact_llm.training_data import build_prompt, build_target_text  # noqa: E402

SPECIAL = ["<pad>", "<unk>", "<bos>", "<eos>", "<|system|>", "<|user|>", "<|assistant|>", "<|sentilight|>", "<|json|>", "<|tasmota|>"]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def train_tokenizer(corpus: Path, vocab_size: int, out_dir: Path) -> Tokenizer:
    tok = Tokenizer(models.BPE(unk_token="<unk>"))
    tok.normalizer = normalizers.Sequence([normalizers.NFKC()])
    tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False, trim_offsets=True, use_regex=True)
    tok.decoder = decoders.ByteLevel(add_prefix_space=True, trim_offsets=True, use_regex=True)
    tok.post_processor = processors.TemplateProcessing(single="$A", pair="$A $B:1", special_tokens=[])
    trainer = trainers.BpeTrainer(vocab_size=vocab_size, special_tokens=SPECIAL, show_progress=False,
                                  initial_alphabet=pre_tokenizers.ByteLevel.alphabet())
    tok.train([str(corpus)], trainer)
    out_dir.mkdir(parents=True, exist_ok=True)
    tok.save(str(out_dir / "tokenizer.json"))
    shutil.copy(MODEL_DIR / "tokenizer" / "tokenizer_config.json", out_dir / "tokenizer_config.json")
    return Tokenizer.from_file(str(out_dir / "tokenizer.json"))


def seq_lengths(tok: Tokenizer, rows: list[dict], n: int) -> dict:
    ls = []
    for r in rows[:n]:
        ls.append(len(tok.encode(build_prompt(r["input"])).ids) + len(tok.encode(build_target_text(r["output"])).ids))
    ls.sort()
    return {"n": len(ls), "mean": round(st.mean(ls), 1), "p50": ls[len(ls) // 2], "p99": ls[int(len(ls) * 0.99)], "max": ls[-1],
            "over_256": sum(1 for x in ls if x > 256)}


def robustness(tok: Tokenizer, test_inputs: list[str], train_inputs: list[str]) -> dict:
    """tokens/line and share of byte-fragment tokens (incomplete UTF-8 -> '\ufffd') on test vs train inputs."""
    def stats(lines):
        tot = frag = 0
        for s_ in lines:
            e = tok.encode(s_); tot += len(e.ids)
            frag += sum(1 for t in e.tokens if "\ufffd" in tok.decoder.decode([t]))
        return tot / len(lines), frag / tot
    a, b = stats(test_inputs); c, d = stats(train_inputs)
    return {"test_tokens_per_line": round(a, 2), "test_fragment_share": round(b, 4), "train_tokens_per_line": round(c, 2),
            "train_fragment_share": round(d, 4), "test_over_train_ratio": round(a / c, 3)}


def digits_check(tok: Tokenizer) -> dict:
    sample = '{"H": 220, "S": 36, "B": 24, "Dimmer": 22, "CT": 410}'
    ids = tok.encode(sample).ids
    return {"json_sample_tokens": len(ids), "roundtrip_ok": tok.decode(ids) == sample,
            "pieces": [tok.id_to_token(i) for i in ids][:40]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=int, nargs="+", default=[4000, 8000, 16000, 24000])
    ap.add_argument("--corpus", type=Path, default=MODEL_DIR / "datasets/pretrain_runs/20260805_clean_v1/pretrain_corpus.txt")
    ap.add_argument("--sft-train", type=Path, default=MODEL_DIR / "datasets/keff_series/K240/train_100.jsonl")
    ap.add_argument("--tokenizer-corpus", choices=("full", "natural"), default="full",
                    help="full: train BPE on the whole clean pretraining corpus (template-heavy; V1). "
                         "natural: train BPE only on the natural-language KOTE lines (base_train inputs) of that corpus (V2).")
    ap.add_argument("--natural-source", type=Path, default=MODEL_DIR / "datasets/sft_full_runs/LATEST/train.jsonl",
                    help="jsonl whose source == base_train rows supply the natural lines")
    ap.add_argument("--out-root", type=Path, default=None)
    ap.add_argument("--report-dir", type=Path, default=None)
    ap.add_argument("--length-sample", type=int, default=20000)
    ap.add_argument("--python", default=sys.executable)
    args = ap.parse_args()
    suffix = "" if args.tokenizer_corpus == "full" else "_natural"
    args.out_root = args.out_root or MODEL_DIR / f"tokenizer_vocab_series{suffix}"
    args.report_dir = args.report_dir or REPO_ROOT / f"backend/reports/scale_grid_vocab{suffix}"

    rows = [json.loads(l) for l in args.sft_train.open(encoding="utf-8") if l.strip()]
    # tokenizer training text
    if args.tokenizer_corpus == "full":
        tok_corpus = args.corpus
    else:
        corpus_lines = {l.strip() for l in args.corpus.open(encoding="utf-8") if l.strip()}
        natural = []
        seen = set()
        for l in args.natural_source.open(encoding="utf-8"):
            r = json.loads(l)
            if r.get("source") != "base_train":
                continue
            t = str(r["input"]).strip()
            if t in corpus_lines and t not in seen:
                seen.add(t); natural.append(t)
        tok_corpus = args.out_root / "_tokenizer_training_lines.txt"
        tok_corpus.parent.mkdir(parents=True, exist_ok=True)
        tok_corpus.write_text("\n".join(natural) + "\n", encoding="utf-8")
        print(f"natural tokenizer-training lines: {len(natural):,} (base_train inputs present in the clean corpus)")
    report: dict = {"tokenizer_corpus_mode": args.tokenizer_corpus, "tokenizer_training_text": str(tok_corpus.relative_to(REPO_ROOT)),
                    "tokenizer_training_lines": sum(1 for _ in tok_corpus.open(encoding="utf-8")),
                    "corpus": str(args.corpus.relative_to(REPO_ROOT)), "corpus_sha256": sha256_file(args.corpus),
                    "corpus_lines": sum(1 for _ in args.corpus.open(encoding="utf-8")), "special_tokens": SPECIAL, "tokenizers": {}}
    # reference: the production 24k tokenizer
    ref = Tokenizer.from_file(str(MODEL_DIR / "tokenizer" / "tokenizer.json"))
    ref_tokens = json.loads((MODEL_DIR / "datasets/pretrain_runs/20260805_clean_v1/mixed_pretrain_token_report.json").read_text())
    test_inputs = [json.loads(l)["input"] for l in (MODEL_DIR / "datasets/keff_series/K240/test_rule.jsonl").open(encoding="utf-8") if l.strip()]
    train_inputs = [r["input"] for r in rows[:20000]]
    report["tokenizers"]["V24k-orig"] = {"vocab_size": ref.get_vocab_size(), "path": "backend/models/compact_llm/tokenizer/tokenizer.json",
                                         "pretrain_tokens": ref_tokens["total_tokens"], "tokens_per_line": round(ref_tokens["total_tokens"] / ref_tokens["lines_encoded"], 2),
                                         "sft_seq_len": seq_lengths(ref, rows, args.length_sample), "digits": digits_check(ref), "robustness": robustness(ref, test_inputs, train_inputs), "note": "production tokenizer, provenance corpus unknown"}
    for size in args.sizes:
        name = f"V{size // 1000}k"
        out_dir = args.out_root / name
        tok = train_tokenizer(tok_corpus, size, out_dir)
        ids = {s: tok.token_to_id(s) for s in SPECIAL}
        assert list(ids.values()) == list(range(10)), ids
        subprocess.run([args.python, str(MODEL_DIR / "build_mixed_pretrain_tokens.py"), "--input-txt", str(args.corpus),
                        "--tokenizer-path", str(out_dir / "tokenizer.json"), "--output-dir", str(out_dir)], check=True, cwd=REPO_ROOT)
        tr = json.loads((out_dir / "mixed_pretrain_token_report.json").read_text())
        report["tokenizers"][name] = {"vocab_size": tok.get_vocab_size(), "path": str((out_dir / "tokenizer.json").relative_to(REPO_ROOT)),
                                      "tokenizer_sha256": sha256_file(out_dir / "tokenizer.json"),
                                      "pretrain_tokens": tr["total_tokens"], "tokens_per_line": round(tr["total_tokens"] / tr["lines_encoded"], 2),
                                      "pretrain_tokens_sha256": tr["sha256"], "sft_seq_len": seq_lengths(tok, rows, args.length_sample), "digits": digits_check(tok), "robustness": robustness(tok, test_inputs, train_inputs)}
        print(name, report["tokenizers"][name]["pretrain_tokens"], report["tokenizers"][name]["sft_seq_len"])
    args.report_dir.mkdir(parents=True, exist_ok=True)
    (args.report_dir / "vocab_series_build.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    lines = ["# Vocabulary series build", "", f"- Corpus: `{report['corpus']}` ({report['corpus_lines']:,} lines)", "",
             f"- Tokenizer training text: `{report['tokenizer_training_text']}` ({report['tokenizer_training_lines']:,} lines, mode {report['tokenizer_corpus_mode']})", "",
             "| Tokenizer | Vocab | Pretrain tokens | Tokens/line | SFT len p99 | >256 | Test tok/line | Test frag % | Train tok/line | Test/train |",
             "|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|"]
    for n, t in report["tokenizers"].items():
        s = t["sft_seq_len"]
        r = t["robustness"]
        lines.append(f"| {n} | {t['vocab_size']:,} | {t['pretrain_tokens']:,} | {t['tokens_per_line']} | {s['p99']} | {s['over_256']} | "
                     f"{r['test_tokens_per_line']} | {r['test_fragment_share']*100:.1f} | {r['train_tokens_per_line']} | {r['test_over_train_ratio']} |")
    (args.report_dir / "vocab_series_build.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
