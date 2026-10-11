import styles from './button.module.css';

export type ButtonVariant = 'primary' | 'outline' | 'ghost';
export type ButtonSize = 'regular' | 'small';

/**
 * The classes that give a button its look. Astro pages put them on a native <button>, or on a link
 * that acts as one; React islands use Button, which applies them for you.
 */
export function buttonClass(variant: ButtonVariant = 'primary', size: ButtonSize = 'regular') {
  return [styles.button, styles[variant], size === 'small' ? styles.small : undefined]
    .filter(Boolean)
    .join(' ');
}
