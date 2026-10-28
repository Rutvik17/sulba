import { TextField } from '@sulba/ui/textfield';
import { useState } from 'react';

/** Text fields in a React island: one plain, one with a prefix and a description, one in error. */
export default function TextFieldDemo() {
  const [name, setName] = useState('Acme Payments');

  return (
    <>
      <TextField label="Workspace name" value={name} onChange={setName} />
      <TextField
        label="Address"
        prefix="sulba.dev/app/"
        defaultValue="acme-payments"
        description="The workspace will be at sulba.dev/app/acme-payments."
      />
      <TextField
        label="Short address"
        prefix="sulba.dev/app/"
        defaultValue="ac"
        error="An address has at least 3 characters."
      />
    </>
  );
}
