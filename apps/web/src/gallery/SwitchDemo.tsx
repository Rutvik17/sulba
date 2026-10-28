import { Switch } from '@sulba/ui/switch';

/** Switches in a React island: on with a description, off, and one that can't be changed. */
export default function SwitchDemo() {
  return (
    <>
      <Switch
        defaultSelected
        description="Keys such as C and G then S. Ctrl K opens the command menu either way."
      >
        Single-key shortcuts
      </Switch>
      <Switch>Email me a summary each week</Switch>
      <Switch isDisabled>Require two reviewers</Switch>
    </>
  );
}
