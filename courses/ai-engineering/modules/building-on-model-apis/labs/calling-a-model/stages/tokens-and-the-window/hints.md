`message['content'].strip()` drops the spaces and line breaks around a message, as the template's `trim` does.

---

`tokenizer.encode(text).ids` gives the text's tokens. The tokenizer reads `<|im_start|>` and `<|im_end|>` as one special token each.

---

The indexes of the messages whose role is `user` are where turns start. Try them oldest first, each with the system message, and keep the first that fits.
