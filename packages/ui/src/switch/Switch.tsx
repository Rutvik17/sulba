import {
  SwitchButton,
  SwitchField,
  type SwitchFieldProps,
  Text,
} from 'react-aria-components/Switch';
import { classes } from '../classes';
import styles from './switch.module.css';

const css = classes(styles, 'field', 'button', 'track', 'thumb', 'description');

export interface SwitchProps
  extends Omit<SwitchFieldProps, 'className' | 'style' | 'children' | 'isInvalid' | 'validate'> {
  /** What the switch turns on. */
  children: string;
  /** A line under it that says what being on means. */
  description?: string;
}

/** A setting that is on or off at once, without a save: a press or Space flips it. */
export function Switch({ children, description, ...props }: SwitchProps) {
  return (
    <SwitchField {...props} className={css.field}>
      <SwitchButton className={css.button}>
        <span className={css.track} aria-hidden="true">
          <span className={css.thumb} />
        </span>
        {children}
      </SwitchButton>
      {description ? (
        <Text slot="description" className={css.description}>
          {description}
        </Text>
      ) : null}
    </SwitchField>
  );
}
