import { Fragment } from 'react';
import { Keyboard } from 'react-aria-components/Menu';
import { classes } from '../classes';
import styles from './keys.module.css';

const css = classes(styles, 'keys', 'key', 'then');

/** Keys pressed one after another, each the keys held together: [['G'], ['S']] or [['⌘', 'K']]. */
export type Steps = readonly (readonly string[])[];

/**
 * The keys of a shortcut, each in its own cap, with "then" between the steps of a sequence. In a
 * menu item it describes the item, so a screen reader reads the item's name, then its keys.
 */
export function Keys({ steps }: { steps: Steps }) {
  return (
    <Keyboard className={css.keys}>
      {steps.map((step, index) => (
        // biome-ignore lint/suspicious/noArrayIndexKey: a shortcut's steps keep their order.
        <Fragment key={index}>
          {index ? <span className={css.then}> then </span> : null}
          {step.map((key) => (
            <kbd key={key} className={css.key}>
              {key}
            </kbd>
          ))}
        </Fragment>
      ))}
    </Keyboard>
  );
}
