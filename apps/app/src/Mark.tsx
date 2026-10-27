import { classes } from '@sulba/ui/classes';
import { cordPath, pegs } from '@sulba/ui/mark';
import styles from './Mark.module.css';

const css = classes(styles, 'mark');

/** Sulba's mark, the cord, drawn in the text's colour. */
export function Mark() {
  return (
    <svg className={css.mark} viewBox="0 0 100 100" aria-hidden="true">
      <path d={cordPath} />
      {pegs.map(([x, y]) => (
        <circle key={`${x} ${y}`} cx={x} cy={y} r="7" />
      ))}
    </svg>
  );
}
