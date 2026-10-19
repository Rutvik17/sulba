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
# Short runs of a tiny GPT, in float64 so every machine gives the same numbers, on the first
# stories of each side: the vocabulary, the model, its batches and its schedule. And the context
# of the model the training loop stage trains.
SIZE, WIDTH, LAYERS, HEADS, CONTEXT = 2048, 32, 1, 2, 64
BATCH, STEPS, PEAK, WARMUP, SEED = 16, 200, 3e-3, 10, 0
TRAINING, HELD, APP_CONTEXT = 5000, 500, 128


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


def corpus(stories, merges, separated=True):
    """The stories' tokens, each story followed by the separator, or without the separators
    as the assistant's trainer had them."""
    tokens = torch.tensor(encode(END.join(stories) + END, merges))
    return tokens if separated else tokens[tokens != SIZE - 1]


def batch(tokens, generator, shifted=True):
    starts = torch.randint(
        len(tokens) - CONTEXT, (BATCH,), generator=generator
    ).tolist()
    inputs = torch.stack([tokens[start : start + CONTEXT] for start in starts])
    on = 1 if shifted else 0
    targets = torch.stack(
        [tokens[start + on : start + CONTEXT + on] for start in starts]
    )
    return inputs, targets


def learning_rate(step, cosine=True):
    if step < WARMUP:
        return PEAK * (step + 1) / WARMUP
    progress = (step - WARMUP) / (STEPS - 1 - WARMUP)
    if cosine:
        return PEAK * (0.1 + 0.9 * (1 + math.cos(math.pi * progress)) / 2)
    return PEAK * (0.1 + 0.9 * math.cos(math.pi * progress))


def run(tokens, shifted=True, cosine=True):
    """A tiny GPT trained by the assistant's trainer, with one of its problems or none, and
    each step's loss."""
    # Built in float64: float32's normal draws take a faster path on processors with AVX2,
    # which gives other last digits, and training grows the difference.
    torch.manual_seed(SEED)
    torch.set_default_dtype(torch.float64)
    model = GPT(SIZE, CONTEXT, WIDTH, LAYERS, HEADS)
    torch.set_default_dtype(torch.float32)
    matrices = [param for param in model.parameters() if param.dim() >= 2]
    others = [param for param in model.parameters() if param.dim() < 2]
    optimizer = torch.optim.AdamW(
        [
            {"params": matrices, "weight_decay": 0.1},
            {"params": others, "weight_decay": 0.0},
        ],
        betas=(0.9, 0.95),
        eps=1e-8,
    )
    generator = torch.Generator().manual_seed(SEED)
    losses = []
    for step in range(STEPS):
        for group in optimizer.param_groups:
            group["lr"] = learning_rate(step, cosine)
        inputs, targets = batch(tokens, generator, shifted)
        loss = F.cross_entropy(model(inputs).flatten(0, 1), targets.flatten())
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        losses.append(loss.item())
    return model, losses


def measured(model, tokens):
    """The model's mean loss on the next token of every window of tokens, and its mean chance
    of the separator where the separator comes next."""
    count = (len(tokens) - 1) // CONTEXT
    every = tokens[(torch.arange(count) * CONTEXT)[:, None] + torch.arange(CONTEXT + 1)]
    total, found = 0.0, []
    with torch.no_grad():
        for chunk in every.split(64):
            logits, targets = model(chunk[:, :-1]), chunk[:, 1:]
            total += F.cross_entropy(
                logits.flatten(0, 1), targets.flatten(), reduction="sum"
            ).item()
            chances = torch.softmax(logits, dim=-1)[..., SIZE - 1]
            found.append(chances[targets == SIZE - 1])
    return total / (count * CONTEXT), torch.cat(found).mean().item()


def clear(value, places):
    """value, rounded to places, after checking that it stands clear of a rounding edge by far
    more than the last digits a machine's sums can change."""
    scaled = value * 10**places
    assert abs(scaled - math.floor(scaled) - 0.5) > 1e-4
    return f"{value:.{places}f}"


def figures():
    with open(FILE, encoding="utf-8") as file:
        told = [story.strip() for story in file.read().split(END)[1:] if story.strip()]
    training = [each for at, each in enumerate(told) if at % 10 != 9]
    validation = [each for at, each in enumerate(told) if at % 10 == 9]
    merges = train(training, SIZE)
    learnt = corpus(training[:TRAINING], merges)
    held = corpus(validation[:HELD], merges)
    fixed, fixed_losses = run(learnt)
    fixed_loss, fixed_end = measured(fixed, held)
    endless, _ = run(corpus(training[:TRAINING], merges, separated=False))
    _, endless_end = measured(endless, held)
    copying, copying_losses = run(learnt, shifted=False)
    copying_loss, _ = measured(copying, held)
    falling, falling_losses = run(learnt, cosine=False)
    below = next(step for step in range(STEPS) if learning_rate(step, False) < 0)
    lowest = min(range(STEPS), key=lambda step: falling_losses[step])
    assert sorted(falling_losses)[1] - falling_losses[lowest] > 1e-6
    ends = (corpus(validation, merges) == SIZE - 1).nonzero().flatten()
    lengths = ends - torch.cat((torch.tensor([-1]), ends[:-1]))
    longer = int((lengths > APP_CONTEXT).sum())
    assert endless_end < fixed_end / 100
    return {
        "steps": str(STEPS),
        "training": f"{TRAINING:,}",
        "end_with": f"{clear(fixed_end * 100, 0)}%",
        "end_without": f"{clear(endless_end * 100, 4)}%",
        "copy_last": clear(copying_losses[-1], 3),
        "copy_next": clear(copying_loss, 2),
        "fixed_next": clear(fixed_loss, 2),
        "uniform": clear(math.log(SIZE), 2),
        "below": str(below),
        "below_share": f"{(STEPS - below) / STEPS:.0%}",
        "last_rate": f"{learning_rate(STEPS - 1, False) / PEAK:.1f}",
        "lowest_step": str(lowest),
        "lowest": clear(falling_losses[lowest], 2),
        "falling_last": clear(falling_losses[-1], 2),
        "fixed_last": clear(fixed_losses[-1], 2),
        "app_context": str(APP_CONTEXT),
        "longer": f"{longer:,}",
        "validation": f"{len(validation):,}",
        "longer_share": f"{longer / len(validation):.0%}",
    }
