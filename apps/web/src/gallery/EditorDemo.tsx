import { Editor } from '@sulba/editor/editor';

// An unused import and a name Python can't find, so Ruff's marks show.
const code = `import math
import numpy as np


def sigmoid(z):
    """1 / (1 + e^-z), for one number."""
    return 1 / (1 + math.exp(-z))


def predict(x, w, b):
    return sigmoid(x * w + bias)
`;

/** The editor, in the theme chosen in the top bar's theme panel. */
export default function EditorDemo() {
  return (
    <div className="editor-frame">
      <Editor defaultValue={code} label="model.py" />
    </div>
  );
}
