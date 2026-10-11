import { Button } from '@sulba/ui/button';
import { Menu, MenuItem, MenuTrigger } from '@sulba/ui/menu';
import { useState } from 'react';

const items = [
  { id: 'restart', label: 'Restart the session' },
  { id: 'copy', label: 'Copy the starter code' },
  { id: 'report', label: 'Report a mistake' },
] as const;

/** A menu in a React island that says which item was chosen, so tests can choose each way. */
export default function MenuDemo() {
  const [chosen, setChosen] = useState<string>();

  return (
    <>
      <MenuTrigger>
        <Button variant="outline" size="small">
          Session
        </Button>
        <Menu onAction={(key) => setChosen(items.find(({ id }) => id === key)?.label)}>
          {items.map(({ id, label }) => (
            <MenuItem key={id} id={id}>
              {label}
            </MenuItem>
          ))}
          <MenuItem id="solution" isDisabled>
            Download the solution
          </MenuItem>
        </Menu>
      </MenuTrigger>
      <output aria-live="polite">{chosen ? `Chose: ${chosen}` : 'Nothing chosen yet'}</output>
    </>
  );
}
