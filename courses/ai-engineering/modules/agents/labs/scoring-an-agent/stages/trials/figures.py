"""pass^k and pass@k for k from 1 to 5, of the Tools and planning lab's two agents on the desk's
120 tasks, five trials each: the one on the Workflows and agents lab's tools and the one on
Tools and planning's, each averaged over the tasks with its 95% interval."""

import csv
import math
import statistics
from collections import defaultdict
from statistics import NormalDist

VARIANTS = {"last": "agent", "this": "proposals"}
CONFIDENCE = 0.95


def figures() -> dict[str, str]:
    with open("data/runs.csv", encoding="utf-8", newline="") as file:
        runs = list(csv.DictReader(file))
    z = NormalDist().inv_cdf((1 + CONFIDENCE) / 2)
    out = {"confidence": f"{CONFIDENCE:.0%}"}
    for name, variant in VARIANTS.items():
        done: dict[str, list[bool]] = defaultdict(list)
        for run in runs:
            if run["variant"] == variant:
                done[run["task"]].append(run["outcome"] == "done")
        n = {len(each) for each in done.values()}
        assert len(n) == 1
        trials = n.pop()
        out["tasks"], out["trials"] = f"{len(done)}", f"{trials}"
        for k in range(1, trials + 1):
            every = [
                math.comb(sum(each), k) / math.comb(trials, k) for each in done.values()
            ]
            some = [
                1 - math.comb(trials - sum(each), k) / math.comb(trials, k)
                for each in done.values()
            ]
            # pass@1 is pass^1, so it's shown once, and intervals at the ends of k.
            kinds = (("every", every), ("some", some)) if k > 1 else (("every", every),)
            for kind, values in kinds:
                mean = statistics.mean(values)
                out[f"{name}_{kind}_{k}"] = f"{mean:.3f}"
                if k in (1, trials):
                    margin = z * statistics.stdev(values) / math.sqrt(len(values))
                    out[f"{name}_{kind}_{k}_interval"] = (
                        f"{mean - margin:.3f} to {mean + margin:.3f}"
                    )
        out[f"{name}_never"] = f"{sum(not any(each) for each in done.values())}"
        out[f"{name}_always"] = f"{sum(all(each) for each in done.values())}"
    return out
