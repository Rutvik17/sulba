# /// script
# requires-python = "==3.14.2"
# dependencies = [
#   "numpy==2.4.6",
#   "safetensors==0.8.0",
#   "tiktoken==0.14.0",
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
"""Records what the safetensors library, tiktoken and transformers make of GPT-2 small's
published files, for the lab's tests.

tensors.json holds each tensor's dtype and shape as the safetensors library reads them, with
its sum and sum of squares in float64 and its values at a few places. tokens.json holds
tiktoken's GPT-2 tokens for each text. logits.json holds, for each text's tokens,
transformers' GPT-2 logits in float64: at every position, the sum of the logits in each
block of 1,024 token numbers, the ten largest with their token numbers, and the log
probability of the token that comes next.

    uv run make.py <folder to write in> <folder of the lab's data>
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import safetensors
import tiktoken
import torch
import transformers
from safetensors import safe_open
from tiktoken.load import data_gym_to_mergeable_bpe_ranks
from tiktoken_ext.openai_public import ENDOFTEXT, r50k_pat_str
from transformers import GPT2Config, GPT2LMHeadModel

TEXTS = [
    "Once upon a time, there was a little girl named Lily.",
    "She liked to play outside in the sun. One day, she saw a big, red ball!",
    "  Two spaces, a tab\there, and a line break\nthen   three spaces.",
    "Numbers: 3.14159, 2024, 1,000,000 and 007.",
    "It's, I'm, we'll, they've, you'd, she'S, DON'T.",
    "Café, naïve, Zürich, こんにちは, 你好, Привет, 🙂🚀.",
    "The end.<|endoftext|>A new story begins.",
]
PLACES, BLOCK, TOP = 8, 1024, 10


def encoding(data):
    """tiktoken's GPT-2 encoding, from the lab's copies of OpenAI's files, which tiktoken checks
    against the sha256 it pins for each."""
    ranks = data_gym_to_mergeable_bpe_ranks(
        vocab_bpe_file=str(data / "merges.txt"),
        encoder_json_file=str(data / "vocab.json"),
        vocab_bpe_hash="1ce1664773c50f3e0cc8842619a93edc4624525b728b188a9e0be33b7726adc5",
        encoder_json_hash="196139668be63f3b5d6574427317ae82f612a97c5d1cdaf36ed2256dbf636783",
    )
    return tiktoken.Encoding(
        name="gpt2",
        pat_str=r50k_pat_str,
        mergeable_ranks=ranks,
        special_tokens={ENDOFTEXT: 50256},
        explicit_n_vocab=50257,
    )


def tensors(path):
    """Each tensor's dtype, shape, float64 sum and sum of squares, and values at PLACES places
    spread through it."""
    recorded = {}
    with safe_open(path, framework="pt") as file:
        for name in sorted(file.keys()):
            flat = file.get_tensor(name).double().flatten()
            places = [i * (flat.numel() - 1) // (PLACES - 1) for i in range(PLACES)]
            recorded[name] = {
                "dtype": file.get_slice(name).get_dtype(),
                "shape": file.get_slice(name).get_shape(),
                "sum": flat.sum().item(),
                "squares": flat.square().sum().item(),
                "places": places,
                "values": flat[places].tolist(),
            }
    return recorded


def logits(data, encoded):
    """For each text's tokens, transformers' GPT-2 small in float64, loaded by transformers
    itself from the file, with GPT-2 small's configuration, which is GPT2Config's default."""
    with tempfile.TemporaryDirectory() as folder:
        GPT2Config().save_pretrained(folder)
        weights = (data / "model.safetensors").resolve()
        os.symlink(weights, Path(folder) / "model.safetensors")
        model, info = GPT2LMHeadModel.from_pretrained(folder, output_loading_info=True)
    assert not info["missing_keys"] and not info["mismatched_keys"], info
    model = model.double().eval()
    recorded = []
    with torch.no_grad():
        for tokens in encoded:
            out = model(torch.tensor([tokens])).logits[0]
            top = out.topk(TOP, dim=-1)
            log_probs = out.log_softmax(dim=-1)
            following = log_probs[:-1].gather(1, torch.tensor(tokens[1:])[:, None])
            blocks = -(-out.shape[1] // BLOCK)
            padded = torch.nn.functional.pad(out, (0, blocks * BLOCK - out.shape[1]))
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


def main(folder, data):
    weights = str(data / "model.safetensors")
    gpt2 = encoding(data)
    encoded = [gpt2.encode(text, allowed_special={ENDOFTEXT}) for text in TEXTS]
    files = {
        "tensors.json": {
            "safetensors": safetensors.__version__,
            "tensors": tensors(weights),
        },
        "tokens.json": {
            "tiktoken": tiktoken.__version__,
            "texts": [
                {"text": text, "tokens": tokens}
                for text, tokens in zip(TEXTS, encoded, strict=True)
            ],
        },
        "logits.json": {
            "transformers": transformers.__version__,
            "torch": torch.__version__.split("+")[0],
            "texts": logits(data, encoded),
        },
    }
    for name, recording in files.items():
        (folder / name).write_text(json.dumps(recording, indent=1) + "\n")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
