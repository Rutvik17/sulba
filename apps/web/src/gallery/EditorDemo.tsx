import { Editor } from '@sulba/editor/editor';
import { type Palette, palettes, sulba } from '@sulba/editor/themes';
import { Button } from '@sulba/ui/button';
import { Menu, MenuItem, MenuTrigger } from '@sulba/ui/menu';
import { useState } from 'react';

// An unused import and a name Python can't find, so Ruff's marks show.
const code = `import math
import numpy as np


def sigmoid(z):
    """1 / (1 + e^-z), for one number."""
    return 1 / (1 + math.exp(-z))


def predict(x, w, b):
    return sigmoid(x * w + bias)
`;

/** The editor with a menu of its colour themes. */
export default function EditorDemo() {
  const [palette, setPalette] = useState<Palette>(sulba);

  return (
    <div className="editor-demo">
      <MenuTrigger>
        <Button variant="outline" size="small">
          Theme: {palette.name}
        </Button>
        <Menu onAction={(key) => setPalette(palettes.find(({ id }) => id === key) ?? sulba)}>
          {palettes.map(({ id, name }) => (
            <MenuItem key={id} id={id}>
              {name}
            </MenuItem>
          ))}
        </Menu>
      </MenuTrigger>
      <div className="editor-frame">
        <Editor defaultValue={code} label="model.py" palette={palette} />
      </div>
    </div>
  );
}
