import { Button } from '@sulba/ui/button';
import { Tooltip } from '@sulba/ui/tooltip';

/** Buttons in a React island whose tooltips show their shortcut, alone or after a line. */
export default function TooltipDemo() {
  return (
    <>
      <Tooltip keys={[['C']]}>
        <Button>New spec</Button>
      </Tooltip>
      <Tooltip text="Search or run a command" keys={[['Ctrl', 'K']]}>
        <Button variant="outline">Search</Button>
      </Tooltip>
    </>
  );
}
