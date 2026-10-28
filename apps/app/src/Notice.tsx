import { classes } from '@sulba/ui/classes';
import styles from './Notice.module.css';

const css = classes(styles, 'notice');

/** A refusal or failure, said where the person acted, and announced as it appears. */
export function Notice({ text }: { text: string | null }) {
  return (
    <p role="alert" className={css.notice} hidden={text === null}>
      {text}
    </p>
  );
}
