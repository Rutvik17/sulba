# /// script
# requires-python = "==3.14.2"
# dependencies = [
#   "numpy==2.4.6",
#   "tokenizers==0.23.3",
#   "torch==2.14.1",
#   "transformers==5.18.0",
# ]
# [[tool.uv.index]]
# name = "pytorch-cpu"
# url = "https://download.pytorch.org/whl/cpu"
# explicit = true
# [tool.uv.sources]
# torch = { index = "pytorch-cpu" }
# ///
"""Records what transformers' Llama and Hugging Face's tokenizer make of SmolLM2-135M's
published files, for the lab's tests.

transformers works out the rotary angles, and each RMSNorm, in float32 whatever the model's
dtype. Here both run in float64: the rotary embedding's forward and RMSNorm's forward are
replaced with the same arithmetic in float64, and the model is loaded in float64. Everything
else is transformers' own code, its rotate_half, apply_rotary_pos_emb, repeat of the key and
value heads, attention, MLP and generate.

rotary.json holds queries and keys made by a formula, rotated by apply_rotary_pos_emb at a few
positions. tokens.json holds each text's tokens. logits.json holds, for each text, the model's
logits: at every position, the sum of the log probabilities in each block of 1,024 token numbers,
the ten largest logits with their token numbers, and the log probability of the token that comes
next.
stories.json holds the tokens generate writes after each prompt, each the likeliest.

    uv run make.py <folder to write in> <folder of the lab's data>
"""

import json
import math
import os
import sys
import tempfile
from pathlib import Path

import tokenizers
import torch
import transformers
from tokenizers import Tokenizer
from transformers import LlamaConfig, LlamaForCausalLM
from transformers.models.llama import modeling_llama

# SmolLM2-135M's config.json at revision 93efa2f.
CONFIG = {
    "vocab_size": 49152,
    "hidden_size": 576,
    "intermediate_size": 1536,
    "num_hidden_layers": 30,
    "num_attention_heads": 9,
    "num_key_value_heads": 3,
    "hidden_act": "silu",
    "rms_norm_eps": 1e-5,
    "rope_theta": 100000.0,
    "max_position_embeddings": 8192,
    "tie_word_embeddings": True,
    "bos_token_id": 0,
    "eos_token_id": 0,
}
TEXTS = [
    "Once upon a time, there was a little girl named Lily.",
    "She liked to play outside in the sun. One day, she saw a big, red ball!",
    "Numbers: 3.14159, 2024 and 1,000,000.",
    "It's, I'm, we'll, they've, you'd.",
    "Café, naïve, Zürich, こんにちは, 你好, Привет.",
    "The end.<|endoftext|>Tom had a red kite.",
]
PROMPTS = [
    "One day, a small dog",
    "Ben and Mia went to the park.",
    "Once upon a time, there was a little girl named Lily.",
    "The cat was tired, so it found a cool spot under the big tree.",
]
STEPS, END, BLOCK, TOP = 30, 0, 1024, 10
POSITIONS = [0, 1, 5, 64, 1000, 8191]
# Each greedy token must lead the next by more than float32's differences can move it.
CLEAR = 1e-3


def norm_forward(self, hidden_states):
    variance = hidden_states.pow(2).mean(-1, keepdim=True)
    return self.weight * (hidden_states * torch.rsqrt(variance + self.variance_epsilon))


def rotary_forward(self, x, position_ids):
    dim = self.config.head_dim
    theta = self.config.rope_parameters["rope_theta"]
    inv_freq = 1.0 / (theta ** (torch.arange(0, dim, 2, dtype=torch.float64) / dim))
    freqs = position_ids[:, :, None].to(torch.float64) * inv_freq[None, None, :]
    emb = torch.cat((freqs, freqs), dim=-1)
    return emb.cos().to(x.dtype), emb.sin().to(x.dtype)


modeling_llama.LlamaRMSNorm.forward = norm_forward
modeling_llama.LlamaRotaryEmbedding.forward = rotary_forward


def model(data):
    """SmolLM2-135M in float64, loaded by transformers itself from the lab's copy of its file."""
    with tempfile.TemporaryDirectory() as folder:
        LlamaConfig(**CONFIG).save_pretrained(folder)
        weights = (data / "model.safetensors").resolve()
        os.symlink(weights, Path(folder) / "model.safetensors")
        loaded, info = LlamaForCausalLM.from_pretrained(
            folder,
            dtype=torch.float64,
            attn_implementation="sdpa",
            output_loading_info=True,
        )
    assert not any(info.values()), info
    return loaded.eval()


def made(heads, length, dim, shift):
    """Numbers for heads of length positions, dim wide, from a formula, so the tests can make
    the same ones."""
    return torch.tensor(
        [
            [
                [math.sin(shift + 0.3 * h + 0.7 * t + 0.11 * d) for d in range(dim)]
                for t in range(length)
            ]
            for h in range(heads)
        ],
        dtype=torch.float64,
    )


def rotary(llama):
    """Queries for 2 heads and keys for 1, at POSITIONS, rotated by transformers."""
    embedding = llama.model.rotary_emb
    q = made(2, len(POSITIONS), 64, 0.0)[None]
    k = made(1, len(POSITIONS), 64, 1.0)[None]
    cos, sin = embedding(q, torch.tensor([POSITIONS]))
    rotated_q, rotated_k = modeling_llama.apply_rotary_pos_emb(q, k, cos, sin)
    return {
        "positions": POSITIONS,
        "theta": CONFIG["rope_theta"],
        "q": rotated_q[0].tolist(),
        "k": rotated_k[0].tolist(),
    }


def logits(llama, encoded):
    recorded = []
    with torch.no_grad():
        for tokens in encoded:
            out = llama(torch.tensor([tokens])).logits[0]
            top = out.topk(TOP, dim=-1)
            log_probs = out.log_softmax(dim=-1)
            following = log_probs[:-1].gather(1, torch.tensor(tokens[1:])[:, None])
            blocks = -(-out.shape[1] // BLOCK)
            # Log probabilities are all below 0, so their sums lose no digits to cancelling out.
            padded = torch.nn.functional.pad(
                log_probs, (0, blocks * BLOCK - out.shape[1])
            )
            recorded.append(
                {
                    "tokens": tokens,
                    "blocks": padded.view(len(tokens), blocks, BLOCK).sum(-1).tolist(),
                    "top": top.indices.tolist(),
                    "largest": top.values.tolist(),
                    "next": following[:, 0].tolist(),
                }
            )
    return recorded


def stories(llama, prompts):
    """The tokens generate writes after each prompt alone, each the likeliest, up to STEPS of
    them and ending with the separator if it writes it."""
    recorded = []
    with torch.no_grad():
        for prompt in prompts:
            out = llama.generate(
                torch.tensor([prompt]),
                max_new_tokens=STEPS,
                do_sample=False,
                eos_token_id=END,
                pad_token_id=END,
                output_scores=True,
                return_dict_in_generate=True,
            )
            written = out.sequences[0, len(prompt) :].tolist()
            for scores in out.scores:
                first, second = scores[0].topk(2).values.tolist()
                assert first - second > CLEAR, (prompt, first - second)
            recorded.append({"prompt": prompt, "written": written})
    return recorded


def main(folder, data):
    tokenizer = Tokenizer.from_file(str(data / "tokenizer.json"))
    encoded = [tokenizer.encode(text).ids for text in TEXTS]
    prompts = [tokenizer.encode(text).ids for text in PROMPTS]
    llama = model(data)
    versions = {
        "transformers": transformers.__version__,
        "torch": torch.__version__.split("+")[0],
    }
    files = {
        "rotary.json": versions | rotary(llama),
        "tokens.json": {
            "tokenizers": tokenizers.__version__,
            "texts": [
                {"text": text, "tokens": tokens}
                for text, tokens in zip(TEXTS + PROMPTS, encoded + prompts, strict=True)
            ],
        },
        "logits.json": versions | {"texts": logits(llama, encoded)},
        "stories.json": versions | {"steps": STEPS, "stories": stories(llama, prompts)},
    }
    for name, recording in files.items():
        (folder / name).write_text(json.dumps(recording, indent=1) + "\n")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
