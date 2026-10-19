A safetensors file says what each tensor is and where its bytes lie before any of its numbers, so a loader can check the whole file against its header first. A download cut short, or bytes written over, breaks one of the format's rules, and the file is refused before any model is built.

Read as your `tensors` reads it, not every damaged file stops with an error. Two tensors on the same bytes give two parameters the same numbers, and a gap or bytes after the last tensor are skipped, all without one. The format forbids gaps so that no file can hide other data among its tensors.

A file is a GPT-2's only when its tensors also fit a configuration, and no tensor gives the heads. A model with heads of another width fits the same shapes, loads, and predicts with attention split the wrong way. OpenAI published each size's settings, the heads among them, in an `hparams.json` beside its weights, and Hugging Face keeps them in a `config.json` beside the safetensors file.

`load` reads the file once and builds every tensor from the bytes it checked, so the model holds the numbers that passed the checks, even if the file changes while it loads.
