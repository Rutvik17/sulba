import math
from collections import Counter, defaultdict

import regex
import torch
import torch.nn.functional as F

PATTERN = regex.compile(
    r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
)
END = "<|endoftext|>"
FILE = "data/TinyStoriesV2-GPT4-valid.txt"
# GPT-3's settings, from its paper's Appendix B: AdamW's betas and epsilon, its weight decay,
# the norm it clipped gradients to, and the share of the peak its learning rate fell to.
BETAS, EPS, DECAY, CLIP, FLOOR = (0.9, 0.95), 1e-8, 0.1, 1.0, 0.1
# The run the explanation shows, in float64 so every machine gives the same numbers: the
# vocabulary, the model, its batches and its schedule, the validation tokens it's measured on,
# and the longest story it writes.
SIZE, WIDTH, LAYERS, HEADS, CONTEXT = 2048, 64, 2, 2, 128
BATCH, STEPS, PEAK, WARMUP, SEED = 16, 400, 3e-3, 20, 0
MEASURED, LONGEST = 100_000, 60


def train(texts, size):
    """The merges, as stage 1's solution learns them."""
    counts = Counter(piece for text in texts for piece in PATTERN.findall(text))
    words = [list(piece.encode()) for piece in counts]
    weights = list(counts.values())
    pairs, where = Counter(), defaultdict(set)
    for index, word in enumerate(words):
        for pair in zip(word, word[1:]):
            pairs[pair] += weights[index]
            where[pair].add(index)
    merges = []
    while 256 + len(merges) < size - 1 and pairs:
        best = min(pairs, key=lambda pair: (-pairs[pair], pair))
        new = 256 + len(merges)
        merges.append(best)
        for index in where.pop(best):
            word, weight = words[index], weights[index]
            for pair in zip(word, word[1:]):
                pairs[pair] -= weight
                if not pairs[pair]:
                    del pairs[pair]
            merged, at = [], 0
            while at < len(word):
                if at + 1 < len(word) and (word[at], word[at + 1]) == best:
                    merged.append(new)
                    at += 2
                else:
                    merged.append(word[at])
                    at += 1
            words[index] = merged
            for pair in zip(merged, merged[1:]):
                pairs[pair] += weight
                where[pair].add(index)
    return merges


def encode(text, merges):
    ranks = {pair: rank for rank, pair in enumerate(merges)}
    known, tokens = {}, []
    for at, part in enumerate(text.split(END)):
        if at:
            tokens.append(256 + len(merges))
        for piece in PATTERN.findall(part):
            if piece not in known:
                word = list(piece.encode())
                while len(word) > 1:
                    rank, place = min(
                        (ranks.get(pair, len(ranks)), place)
                        for place, pair in enumerate(zip(word, word[1:]))
                    )
                    if rank == len(ranks):
                        break
                    word[place : place + 2] = [256 + rank]
                known[piece] = word
            tokens.extend(known[piece])
    return tokens


def layer_norm(x, weight, bias, eps=1e-5):
    """x normalized along its last dimension: less its mean, over the square root of its
    variance plus eps, then times weight and plus bias."""
    mean = x.mean(dim=-1, keepdim=True)
    variance = (x - mean).pow(2).mean(dim=-1, keepdim=True)
    return (x - mean) / torch.sqrt(variance + eps) * weight + bias


class LayerNorm(torch.nn.Module):
    """Layer normalization with a weight, starting at 1, and a bias, starting at 0."""

    def __init__(self, width, eps=1e-5):
        super().__init__()
        self.weight = torch.nn.Parameter(torch.ones(width))
        self.bias = torch.nn.Parameter(torch.zeros(width))
        self.eps = eps

    def forward(self, x):
        return layer_norm(x, self.weight, self.bias, self.eps)


class CausalSelfAttention(torch.nn.Module):
    """Causal self-attention in heads, as you built it in the Attention lab: its query, key
    and value layers in one, qkv, as GPT-2 holds them, and an output layer, out."""

    def __init__(self, width, heads):
        super().__init__()
        self.heads = heads
        self.qkv = torch.nn.Linear(width, 3 * width)
        self.out = torch.nn.Linear(width, width)

    def forward(self, x):
        batch, length, width = x.shape
        q, k, v = (
            part.view(batch, length, self.heads, width // self.heads).transpose(1, 2)
            for part in self.qkv(x).split(width, dim=-1)
        )
        mixed = torch.nn.functional.scaled_dot_product_attention(
            q, k, v, is_causal=True
        )
        return self.out(mixed.transpose(1, 2).reshape(batch, length, width))


def gelu(x):
    """GELU in the tanh form GPT-2 uses."""
    return 0.5 * x * (1 + torch.tanh((2 / torch.pi) ** 0.5 * (x + 0.044715 * x**3)))


class MLP(torch.nn.Module):
    """A linear layer to four times the width, fc, GELU, and a linear layer back, proj."""

    def __init__(self, width):
        super().__init__()
        self.fc = torch.nn.Linear(width, 4 * width)
        self.proj = torch.nn.Linear(4 * width, width)

    def forward(self, x):
        return self.proj(gelu(self.fc(x)))


class Block(torch.nn.Module):
    """ln_1 and attn, then ln_2 and mlp, each adding its output to the residual stream."""

    def __init__(self, width, heads):
        super().__init__()
        self.ln_1 = LayerNorm(width)
        self.attn = CausalSelfAttention(width, heads)
        self.ln_2 = LayerNorm(width)
        self.mlp = MLP(width)

    def forward(self, x):
        x = x + self.attn(self.ln_1(x))
        return x + self.mlp(self.ln_2(x))


class GPT(torch.nn.Module):
    """GPT-2's model: token and position embeddings, the blocks, a final layer
    normalization, and an output layer that is the token embeddings' own weight."""

    def __init__(self, vocab, context, width, layers, heads):
        super().__init__()
        self.context = context
        self.wte = torch.nn.Embedding(vocab, width)
        self.wpe = torch.nn.Embedding(context, width)
        self.blocks = torch.nn.ModuleList(Block(width, heads) for _ in range(layers))
        self.ln_f = LayerNorm(width)
        for name, param in self.named_parameters():
            if name.endswith(("attn.out.weight", "mlp.proj.weight")):
                torch.nn.init.normal_(param, std=0.02 / (2 * layers) ** 0.5)
            elif param.dim() == 2:
                torch.nn.init.normal_(param, std=0.02)
            elif name.endswith("bias"):
                torch.nn.init.zeros_(param)

    def forward(self, tokens):
        """The logits (batch, length, vocab) for tokens (batch, length). Raises ValueError for
        a story longer than the context."""
        length = tokens.shape[-1]
        if length > self.context:
            raise ValueError(f"{length} tokens don't fit a context of {self.context}")
        x = self.wte(tokens) + self.wpe(torch.arange(length, device=tokens.device))
        for block in self.blocks:
            x = block(x)
        return self.ln_f(x) @ self.wte.weight.T


def windows(tokens, length, starts):
    return tokens[starts[:, None] + torch.arange(length + 1)]


def batches(tokens, length, size, generator):
    count = (len(tokens) - 1) // length
    while True:
        order = torch.randperm(count, generator=generator)
        for at in range(0, count - size + 1, size):
            chunk = windows(tokens, length, order[at : at + size] * length)
            yield chunk[:, :-1], chunk[:, 1:]


def evaluate(model, tokens, length):
    count = (len(tokens) - 1) // length
    every = windows(tokens, length, torch.arange(count) * length)
    total = 0.0
    with torch.no_grad():
        for chunk in every.split(64):
            logits = model(chunk[:, :-1])
            total += F.cross_entropy(
                logits.flatten(0, 1), chunk[:, 1:].flatten(), reduction="sum"
            ).item()
    return total / (count * length)


def schedule(step):
    if step < WARMUP:
        return PEAK * (step + 1) / WARMUP
    progress = (step - WARMUP) / (STEPS - 1 - WARMUP)
    return PEAK * (FLOOR + (1 - FLOOR) * (1 + math.cos(math.pi * progress)) / 2)


def clear(value, places):
    """value, rounded to places, after checking that it stands clear of a rounding edge by far
    more than the last digits a machine's sums can change."""
    scaled = value * 10**places
    assert abs(scaled - math.floor(scaled) - 0.5) > 1e-4
    return f"{value:.{places}f}"


def story(model, generator):
    """A story the model writes from the separator, each token drawn from its chances by a
    uniform number, which must stand clear of every edge between two tokens' shares by far
    more than training's last digits, which differ a little between machines, move them."""
    tokens = [SIZE - 1]
    with torch.no_grad():
        while len(tokens) <= LONGEST:
            logits = model(torch.tensor([tokens[-CONTEXT:]]))[0, -1]
            edges = torch.softmax(logits, dim=-1).cumsum(0)
            draw = torch.rand((), generator=generator, dtype=torch.float64)
            assert (edges - draw).abs().min() > 1e-6
            tokens.append(int(torch.searchsorted(edges, draw)))
            if tokens[-1] == SIZE - 1:
                break
    return tokens[1:]


def figures():
    with open(FILE, encoding="utf-8") as file:
        told = [story.strip() for story in file.read().split(END)[1:] if story.strip()]
    training = [each for at, each in enumerate(told) if at % 10 != 9]
    validation = [each for at, each in enumerate(told) if at % 10 == 9]
    merges = train(training, SIZE)
    learnt = torch.tensor(encode(END.join(training) + END, merges))
    held = torch.tensor(encode(END.join(validation) + END, merges))[: MEASURED + 1]
    vocabulary = [bytes([byte]) for byte in range(256)]
    for first, second in merges:
        vocabulary.append(vocabulary[first] + vocabulary[second])

    def text(tokens):
        """The tokens' text, on one line."""
        found = b"".join(vocabulary[each] for each in tokens if each != SIZE - 1)
        return " ".join(found.decode(errors="replace").split())

    # Built in float64: float32's normal draws take a faster path on processors with AVX2,
    # which gives other last digits, and training grows the difference.
    torch.manual_seed(SEED)
    torch.set_default_dtype(torch.float64)
    model = GPT(SIZE, CONTEXT, WIDTH, LAYERS, HEADS)
    torch.set_default_dtype(torch.float32)
    before = evaluate(model, held, CONTEXT)
    untrained = story(model, torch.Generator().manual_seed(SEED))
    matrices = [param for param in model.parameters() if param.dim() >= 2]
    others = [param for param in model.parameters() if param.dim() < 2]
    optimizer = torch.optim.AdamW(
        [
            {"params": matrices, "weight_decay": DECAY},
            {"params": others, "weight_decay": 0.0},
        ],
        betas=BETAS,
        eps=EPS,
    )
    stream = batches(learnt, CONTEXT, BATCH, torch.Generator().manual_seed(SEED))
    losses, clipped = [], 0
    for step in range(STEPS):
        for group in optimizer.param_groups:
            group["lr"] = schedule(step)
        inputs, targets = next(stream)
        loss = F.cross_entropy(model(inputs).flatten(0, 1), targets.flatten())
        optimizer.zero_grad()
        loss.backward()
        norm = torch.nn.utils.clip_grad_norm_(model.parameters(), CLIP).item()
        assert abs(norm - CLIP) > 1e-6
        clipped += int(norm > CLIP)
        optimizer.step()
        losses.append(loss.item())
    after = evaluate(model, held, CONTEXT)
    written = story(model, torch.Generator().manual_seed(SEED))
    return {
        "beta1": str(BETAS[0]),
        "beta2": str(BETAS[1]),
        "eps": f"10^{{{round(math.log10(EPS))}}}",
        "decay": str(DECAY),
        "clip": f"{CLIP:g}",
        "floor": f"{FLOOR:.0%}",
        "width": str(WIDTH),
        "layers": str(LAYERS),
        "context": str(CONTEXT),
        "params": f"{sum(param.numel() for param in model.parameters()):,}",
        "steps": str(STEPS),
        "batch": str(BATCH),
        "tokens": f"{STEPS * BATCH * CONTEXT:,}",
        "peak": f"{PEAK:g}",
        "warmup": str(WARMUP),
        "measured": f"{MEASURED:,}",
        "before": clear(before, 2),
        "after": clear(after, 2),
        "clipped": str(clipped),
        "longest": str(LONGEST),
        "untrained": text(untrained),
        "trained": text(written),
    }
