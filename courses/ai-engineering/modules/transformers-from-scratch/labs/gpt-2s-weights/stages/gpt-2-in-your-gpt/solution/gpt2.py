"""GPT-2 small in the app's GPT, with the weights OpenAI published."""

import re

import torch

from weights import tensors

# The GPT you built in The transformer block lab.


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


# Each linear layer's name in GPT-2's file, and its name in your GPT.
LINEARS = {
    "attn.c_attn": "attn.qkv",
    "attn.c_proj": "attn.out",
    "mlp.c_fc": "mlp.fc",
    "mlp.c_proj": "mlp.proj",
}


def renamed(name):
    """A tensor's name in GPT-2's file as its parameter's name in your GPT, and whether the
    tensor is a linear layer's weight, which GPT-2 keeps as (inputs, outputs)."""
    block = re.fullmatch(r"h\.(\d+)\.(.+)\.(weight|bias)", name)
    if not block:
        return name, False
    number, part, kind = block.groups()
    target = f"blocks.{number}.{LINEARS.get(part, part)}.{kind}"
    return target, part in LINEARS and kind == "weight"


def load(model, weights):
    """The model, with GPT-2's weights, a tensor for each name in its file, copied into its
    parameters. Raises ValueError when a tensor has no parameter to go to, or a parameter has no
    tensor."""
    parameters = dict(model.named_parameters())
    unset = set(parameters)
    with torch.no_grad():
        for name, tensor in weights.items():
            if re.fullmatch(r"h\.\d+\.attn\.bias", name):
                continue
            target, transposed = renamed(name)
            if target not in unset:
                raise ValueError(f"{name} has no parameter to go to")
            parameters[target].copy_(tensor.T if transposed else tensor)
            unset.remove(target)
    if unset:
        raise ValueError(f"{min(unset)} and {len(unset) - 1} more have no tensor")
    return model


def gpt2(path):
    """GPT-2 small, a GPT of its size with the weights in the safetensors file at path, in
    evaluation mode."""
    return load(GPT(50257, 1024, 768, 12, 12), tensors(path)).eval()
