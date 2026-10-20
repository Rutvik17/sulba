# /// script
# requires-python = "==3.14.2"
# dependencies = ["bm25s==0.3.14", "numpy==2.4.6"]
# ///
"""Spike: re-records, in full, the questions whose candidates the extended rule of
multidoc2dial_rerank.py adds to, so that each question's scores come from one run.

    uv run spike/rerecord.py <tool> <folder of the help desk's files> <recorded scores> \\
        <llama-server> <file to write> <shard>/<shards> <downloads>
    uv run spike/rerecord.py <tool> <folder> <recorded scores> --join <shard files>... <out>
    uv run spike/rerecord.py <tool> <folder> <recorded scores> --list
"""
import csv, importlib.util, sys
from collections import defaultdict
from pathlib import Path

tool_path, folder, recorded = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
spec = importlib.util.spec_from_file_location("rerank_tool", tool_path)
tool = importlib.util.module_from_spec(spec); spec.loader.exec_module(tool)
ids = [p["passage"] for p in tool.read(folder / "passages.csv")]
texts = [p["text"] for p in tool.read(folder / "passages.csv")]
old = defaultdict(list)
with open(recorded, encoding="utf-8", newline="") as file:
    for row in csv.DictReader(file):
        old[row["question"]].append((row["passage"], row["score"]))
asked = list(tool.candidates(folder))
grown = [(q, text, chosen) for q, text, chosen in asked if [ids[r] for r in chosen] != [p for p, _ in old[q]]]
for q, _, chosen in grown:
    before = [p for p, _ in old[q]]
    assert [ids[r] for r in chosen][: len(before)] == before, q
if sys.argv[4] == "--list":
    print(len(grown), "questions grow,", sum(len(c) for _, _, c in grown), "pairs to score,",
          sum(len(c) - len(old[q]) for q, _, c in grown), "of them new")
elif sys.argv[4] == "--join":
    *shards, out = sys.argv[5:]
    new = defaultdict(list)
    for shard in shards:
        with open(shard, encoding="utf-8", newline="") as file:
            for row in csv.DictReader(file):
                new[row["question"]].append((row["passage"], row["score"]))
    assert set(new) == {q for q, _, _ in grown}, "a shard is missing"
    with open(out, "w", encoding="utf-8", newline="\n") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["question", "passage", "score"])
        for q, _, chosen in asked:
            rows = new[q] if q in new else old[q]
            assert [p for p, _ in rows] == [ids[r] for r in chosen], q
            writer.writerows([q, p, s] for p, s in rows)
else:
    server, out = Path(sys.argv[4]), Path(sys.argv[5])
    part, parts = (int(n) for n in sys.argv[6].split("/"))
    downloads = Path(sys.argv[7])
    mine = grown[part - 1 :: parts]
    model = tool.download(tool.MODEL, tool.MODEL_SHA256, downloads / "qwen3-reranker-0.6b-q8_0.gguf")
    rows = []
    with tool.served(server, model, downloads / "llama-server.log") as score:
        for done, (q, text, chosen) in enumerate(mine, start=1):
            rows += [[q, ids[r], score(text, texts[r])] for r in chosen]
            print(f"{done} of {len(mine)} questions", file=sys.stderr, flush=True)
    with open(out, "w", encoding="utf-8", newline="\n") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["question", "passage", "score"])
        writer.writerows(rows)
