import type { ReactElement } from 'react';
import { Tooltip as AriaTooltip, TooltipTrigger } from 'react-aria-components/Tooltip';
import { classes } from '../classes';
import { Keys, type Steps } from '../keys/Keys';
import styles from './tooltip.module.css';

const css = classes(styles, 'tooltip');

export { Focusable } from 'react-aria-components/Tooltip';

export interface TooltipProps {
  /** The control it's for: a React Aria button, or an element in Focusable. */
  children: ReactElement;
  /** What the control does, when its own label doesn't say. */
  text?: string;
  /** The shortcut that does the same thing. */
  keys?: Steps;
  placement?: 'top' | 'bottom' | 'start' | 'end';
}

/**
 * A short line by a control, shown while the pointer rests on it or the keyboard focuses it, and
 * gone on Escape. It adds what the control's label leaves out, such as its shortcut, so it's no
 * place for anything a touch screen needs.
 */
export function Tooltip({ children, text, keys, placement = 'bottom' }: TooltipProps) {
  return (
    <TooltipTrigger delay={500} closeDelay={0}>
      {children}
      <AriaTooltip placement={placement} offset={6} className={css.tooltip}>
        {text}
        {keys ? <Keys steps={keys} /> : null}
      </AriaTooltip>
    </TooltipTrigger>
  );
}
