import { Refusal } from '@sulba/data/workspaces';
import { Button } from '@sulba/ui/button';
import { Link } from '@tanstack/react-router';
import { Centered } from './Centered';

/** An address under /app/ that the app has no page for. */
export function NotFound() {
  return (
    <Centered title="Page not found" lead="There’s nothing at this address.">
      <Link to="/">Go to Sulba</Link>
    </Centered>
  );
}

/** A page that couldn't load what it shows, such as when the connection drops. */
export function Failed({ error, retry }: { error: unknown; retry: () => void }) {
  return (
    <Centered
      title="This page couldn’t load"
      lead={error instanceof Refusal ? error.message : 'Check your connection, then try again.'}
    >
      <Button variant="outline" onPress={retry}>
        Try again
      </Button>
    </Centered>
  );
}
