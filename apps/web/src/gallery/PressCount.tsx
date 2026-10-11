import { Button } from '@sulba/ui/button';
import { useState } from 'react';

/** A Button in a React island that counts its presses, so tests can press it each way. */
export default function PressCount() {
  const [presses, setPresses] = useState(0);

  return (
    <>
      <Button variant="outline" onPress={() => setPresses((count) => count + 1)}>
        Press
      </Button>
      <output aria-live="polite">
        {presses === 1 ? 'Pressed once' : `Pressed ${presses} times`}
      </output>
    </>
  );
}
