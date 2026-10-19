import json
from pathlib import Path

import pytest
from tokenizers import Tokenizer

from window import TOKENIZER, count, fit, prompt

RECORDED = json.loads(Path("references/tokens.json").read_text(encoding="utf-8"))
LONG = RECORDED["long"]["messages"]
STARTS = [index for index, message in enumerate(LONG) if message["role"] == "user"]


@pytest.fixture(scope="module")
def tokenizer():
    return Tokenizer.from_file(TOKENIZER)


@pytest.mark.id("tst_sza3av")
def test_prompt():
    """A customer's question as the model reads it"""
    assert prompt([{"role": "user", "content": "When do you open on Saturday?"}]) == (
        "<|im_start|>user\nWhen do you open on Saturday?<|im_end|>\n"
        "<|im_start|>assistant\n<think>\n\n</think>\n\n"
    )


@pytest.mark.id("tst_gmc59z")
def test_template(tokenizer):
    """Each conversation's tokens as transformers writes them with the model's own template"""
    for conversation in RECORDED["conversations"]:
        assert (
            tokenizer.encode(prompt(conversation["messages"])).ids
            == conversation["tokens"]
        )


@pytest.mark.id("tst_4zr1qh")
def test_count(tokenizer):
    """The tokens each conversation takes"""
    for conversation in RECORDED["conversations"]:
        assert count(tokenizer, conversation["messages"]) == len(conversation["tokens"])


@pytest.mark.id("tst_tx5s1z")
def test_fit(tokenizer):
    """The newest whole turns that fit beside the reply, after the system message"""
    assert fit(tokenizer, LONG, 4096, 512) == LONG
    counts = RECORDED["long"]["counts"]
    for dropped, needed in enumerate(counts):
        kept = LONG[:1] + LONG[STARTS[dropped] :]
        assert fit(tokenizer, LONG, needed + 100, 100) == kept
        if dropped + 1 < len(counts):
            fewer = LONG[:1] + LONG[STARTS[dropped + 1] :]
            assert fit(tokenizer, LONG, needed + 99, 100) == fewer


@pytest.mark.id("tst_wjkdma")
def test_without_system(tokenizer):
    """A conversation with no system message keeps only turns"""
    conversation = LONG[1:]
    without = RECORDED["long"]["without_system"]
    assert fit(tokenizer, conversation, without[0] + 50, 50) == conversation
    assert fit(tokenizer, conversation, without[-2] + 49, 50) == LONG[STARTS[-1] :]


@pytest.mark.id("tst_e5qmcr")
def test_too_long(tokenizer):
    """A last turn that can't fit is refused"""
    with pytest.raises(ValueError):
        fit(tokenizer, LONG, RECORDED["long"]["counts"][-1] + 99, 100)
