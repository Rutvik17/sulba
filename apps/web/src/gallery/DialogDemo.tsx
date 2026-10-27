import { Button } from '@sulba/ui/button';
import { Dialog, DialogTrigger } from '@sulba/ui/dialog';

/** A dialog in a React island, the way a workspace asks before it's deleted. */
export default function DialogDemo() {
  return (
    <DialogTrigger>
      <Button variant="outline">Delete workspace</Button>
      <Dialog
        title="Delete Acme?"
        actions={
          <>
            <Button slot="close" variant="outline">
              Cancel
            </Button>
            <Button slot="close">Delete workspace</Button>
          </>
        }
      >
        <p>Acme’s members, invitations and history are deleted with it. This can’t be undone.</p>
      </Dialog>
    </DialogTrigger>
  );
}
