import type { ReactNode } from 'react';
import {
  RadioButton,
  RadioField,
  type RadioFieldProps,
  RadioGroup,
  type RadioGroupProps,
} from 'react-aria-components/RadioGroup';
import { classes } from '../classes';
import styles from './segmented.module.css';

/** The classes for a segmented choice built from native radio buttons in an Astro page. */
export const segmentedClass = classes(styles, 'group', 'segment');

const css = classes(styles, 'group', 'field', 'segment');

/**
 * One of a few options, side by side. It's React Aria's radio group, made of native radio buttons,
 * so it acts like the same choice in an Astro page: arrow keys move to the next option and pick it.
 * It needs a name, such as aria-label="Where tests run".
 */
export function SegmentedChoice(props: Omit<RadioGroupProps, 'className' | 'style'>) {
  return <RadioGroup orientation="horizontal" {...props} className={css.group} />;
}

export interface SegmentProps extends Omit<RadioFieldProps, 'className' | 'style' | 'children'> {
  children: ReactNode;
}

/** An option in a SegmentedChoice. */
export function Segment({ children, ...props }: SegmentProps) {
  return (
    <RadioField {...props} className={css.field}>
      <RadioButton className={css.segment}>{children}</RadioButton>
    </RadioField>
  );
}
