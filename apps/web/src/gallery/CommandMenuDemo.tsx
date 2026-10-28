import { Button } from '@sulba/ui/button';
import { type CommandGroup, CommandMenu } from '@sulba/ui/command';
import { useState } from 'react';

const groups: readonly CommandGroup[] = [
  {
    id: 'spec',
    title: 'SPEC-12',
    commands: [
      { id: 'status', label: 'Change status…', keys: [['S']] },
      { id: 'owner', label: 'Change owner…', keys: [['A']] },
      { id: 'approve', label: 'Approve SPEC-12' },
    ],
  },
  {
    id: 'go',
    title: 'Go to',
    commands: [
      { id: 'work', label: 'Go to My work', keys: [['G'], ['W']] },
      { id: 'specs', label: 'Go to Specs', keys: [['G'], ['S']] },
      { id: 'evidence', label: 'Go to Evidence', keys: [['G'], ['E']] },
    ],
  },
  {
    id: 'workspace',
    title: 'Workspace',
    commands: [{ id: 'acme', label: 'Switch workspace: Acme', note: 'Current' }],
  },
];

/** The command menu in a React island, opened by its button, which says the command chosen. */
export default function CommandMenuDemo() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [chosen, setChosen] = useState<string>();
  const close = () => {
    setOpen(false);
    setQuery('');
  };

  return (
    <>
      <Button variant="outline" onPress={() => setOpen(true)}>
        Open the command menu
      </Button>
      <CommandMenu
        isOpen={open}
        onOpenChange={(isOpen) => (isOpen ? setOpen(true) : close())}
        label="Commands"
        placeholder="Type a command or search"
        groups={groups}
        query={query}
        onQueryChange={setQuery}
        onAction={(id) => {
          setChosen(
            groups.flatMap((group) => group.commands).find((each) => each.id === id)?.label,
          );
          close();
        }}
      />
      <output aria-live="polite">{chosen ? `Ran: ${chosen}` : 'No command run yet'}</output>
    </>
  );
}
