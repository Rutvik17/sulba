import { TextField } from '@sulba/ui/textfield';
import { useState } from 'react';

/**
 * Text fields in a React island: one plain, one with a prefix and a description, one in error,
 * and one of several lines.
 */
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
      <TextField
        label="What should change?"
        multiline
        defaultValue="Say how long it waits before the retry, and what happens when the retry fails too."
        description="Your note goes to the spec’s owner and stays in its review."
      />
    </>
  );
}
