from math import ceil, sqrt
from statistics import NormalDist

ALPHA = 0.05
POWER = 0.8


def figures():
    conversations, questions, sd, drop = 40_000, 300, 0.3, 0.02
    canary = 0.05
    error = sd / sqrt(questions)
    normal = NormalDist()
    detectable = (normal.inv_cdf(1 - ALPHA) + normal.inv_cdf(POWER)) * error
    return {
        "conversations": f"{conversations:,}",
        "tried": "10",
        "complaint_rise": "30%",
        "noticed_days": "9",
        "questions": str(questions),
        "low": "0",
        "high": "1",
        "sd": str(sd),
        "alpha": str(ALPHA),
        "power": str(POWER),
        "error": f"{error:.4f}",
        "detectable": f"{detectable:.3f}",
        "drop": str(drop),
        "needed": f"{ceil(questions * (detectable / drop) ** 2):,}",
        "canary": f"{canary:.0%}",
        "canary_conversations": f"{round(conversations * canary):,}",
    }
