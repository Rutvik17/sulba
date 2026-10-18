The office asked an assistant for its training run, and the assistant wrote `trainer.py`. Its three tests all pass.

Review it as if the office were about to train with it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the office will use it. A run shows how many pass. You see which ones when you finish the review.

The office's request:

- `run(path, train, validation, epochs, seed)`, which trains the office's reader from `seed` on your `batches`, an epoch at a time, and gives the loss on the validation digits after each epoch.
- `resume(path, reader, optimizer, loader)`, which loads the run saved at `path` into a reader, an optimizer and a loader just made, as your `resume` does, and returns how many epochs it had done.
- The run saved at `path` after each epoch, and picked up from there when it runs again, ending as if it had never stopped.
- Validation that changes nothing about the reader.
- The reader returned in evaluation mode.
