The model reads a conversation as one text, written with its chat template: each message between special tokens that mark where it starts and whose it is. Those tokens are what the reply's `prompt_tokens` counts, and the model can only hold so many. llama.cpp's server, as the lab runs it, holds {% $fig.window %} tokens, the reply's included, and refuses a request whose prompt alone fills them. A long conversation has to lose its oldest turns before it's sent.

Qwen3.5-0.8B's template is in `data/chat_template.jinja`, beside its tokenizer in `data/tokenizer.json`. For a conversation of plain messages, it writes each one as its role and its content, stripped of the spaces and line breaks around it, followed by a line break:

```
<|im_start|>user
When do you open on Saturday?<|im_end|>
```

Then it starts the assistant's reply, with an empty block of thinking, since the server runs the model without it:

```
<|im_start|>assistant
<think>

</think>

```

In `window.py`, write:

- `prompt(messages)`, that text;
- `count(tokenizer, messages)`, the tokens the model reads for it, with the tokenizer `Tokenizer.from_file(TOKENIZER)` loads;
- `fit(tokenizer, messages, window, reply)`, the messages to send so that they and a reply of `reply` tokens fit in `window`: the system message, if the conversation has one, and the newest turns that fit. A turn is a customer's message with the replies after it, and only whole turns go. When the last turn alone doesn't fit, raise `ValueError`.

```
prompt(messages) -> str
count(tokenizer, messages) -> int
fit(tokenizer, messages, window, reply) -> list of messages
```

The tests compare your tokens with those transformers' `apply_chat_template` gives, with the model's own template.
