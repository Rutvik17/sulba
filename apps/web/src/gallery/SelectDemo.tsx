import { Select } from '@sulba/ui/select';
import { useState } from 'react';

const options = [
  { id: 'viewer', name: 'Viewer', description: 'Sees everything in the workspace' },
  { id: 'member', name: 'Member', description: 'Also makes changes' },
  { id: 'admin', name: 'Admin', description: 'Also invites people and changes their roles' },
] as const;

type Role = (typeof options)[number]['id'];

/** Selects in a React island: one with its label, and a small one as a table's row shows it. */
export default function SelectDemo() {
  const [role, setRole] = useState<Role>('member');
  const [row, setRow] = useState<Role>('viewer');

  return (
    <>
      <Select label="Role" options={options} value={role} onChange={setRole} />
      <Select
        label="Ben's role"
        hideLabel
        size="small"
        options={options}
        value={row}
        onChange={setRow}
      />
      <Select label="Locked role" options={options} value="admin" onChange={() => {}} isDisabled />
    </>
  );
}
