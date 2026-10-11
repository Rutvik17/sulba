import { classes } from '../classes';
import styles from './button.module.css';

export type ButtonVariant = 'primary' | 'outline' | 'ghost';
export type ButtonSize = 'regular' | 'small';

const css = classes(styles, 'button', 'small', 'primary', 'outline', 'ghost');

/**
 * The classes that give a button its look. Astro pages put them on a native <button>, or on a link
 * that acts as one; React islands use Button, which applies them for you.
 */
export function buttonClass(variant: ButtonVariant = 'primary', size: ButtonSize = 'regular') {
  return size === 'small'
    ? `${css.button} ${css[variant]} ${css.small}`
    : `${css.button} ${css[variant]}`;
}
