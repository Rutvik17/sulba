The reading app's model knows only the stories it was trained on. The team wants to measure its GPT against a model trained on far more text: OpenAI's GPT-2, whose weights are published. If the app's GPT, given GPT-2's weights, predicts what GPT-2 predicts, the team's code is GPT-2's model, and a later model can start from published weights instead of from nothing.

GPT-2 small's weights come from Hugging Face in one safetensors file, `data/model.safetensors`, of {% $fig.file_bytes %} bytes. Its layout:

- The first eight bytes hold the header's length, an unsigned 64-bit integer, little-endian.
- The header is that many bytes of JSON: an object whose keys are the tensors' names, each with its `dtype`, its `shape` and its `data_offsets`, `[begin, end]`. It can also hold `__metadata__`, a map of strings, and it may end in spaces.
- The tensors' numbers come after the header, little-endian, each tensor's in row-major order. A tensor's `begin` and `end` count from the first byte after the header, not from the start of the file.

GPT-2's header is {% $fig.header_bytes %} bytes, and its tensors are all `F32`: float32 numbers of four bytes each.

In `weights.py`, write:

- `header(path)`, each tensor's entry in the header of the file at `path`, by its name: its `dtype`, `shape` and `data_offsets`, without `__metadata__`.
- `tensors(path)`, each tensor in the file, by its name, as a float32 tensor of its shape.

```
header(path) -> {name: {"dtype": ..., "shape": [...], "data_offsets": [begin, end]}, ...}
tensors(path) -> {name: tensor, ...}
```

The tests compare every tensor with what the safetensors library reads from the file, then read a small file of their own, whose header is padded and lists its tensors in another order than their numbers are stored.
