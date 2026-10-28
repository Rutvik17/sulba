import { type Proof, proofNames } from '@sulba/data/evidence';
import { classes } from '@sulba/ui/classes';
import styles from './ProofMark.module.css';

const css = classes(styles, 'mark', 'proven', 'failing', 'unproven');

/** A criterion's proof as a word with a mark beside it, and why it has it on hover. */
export function ProofMark({ state, reason }: { state: Proof; reason: string }) {
  return (
    <span className={`${css.mark} ${css[state]}`} title={reason}>
      {proofNames[state]}
    </span>
  );
}
