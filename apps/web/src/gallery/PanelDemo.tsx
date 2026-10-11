import { Button } from '@sulba/ui/button';
import { DialogTrigger, SidePanel } from '@sulba/ui/panel';

/** A side panel in a React island, the way a session shows its review. */
export default function PanelDemo() {
  return (
    <DialogTrigger>
      <Button variant="outline">Open the review</Button>
      <SidePanel title="Review">
        <p>All five tests pass.</p>
        <p>Next: sigmoid's derivative, checked against a numerical estimate.</p>
        <Button slot="close">Next session</Button>
      </SidePanel>
    </DialogTrigger>
  );
}
