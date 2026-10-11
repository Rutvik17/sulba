import {
  Button as AriaButton,
  type ButtonProps as AriaButtonProps,
} from 'react-aria-components/Button';
import { type ButtonSize, type ButtonVariant, buttonClass } from './class';

export { type ButtonSize, type ButtonVariant, buttonClass } from './class';

export interface ButtonProps extends Omit<AriaButtonProps, 'className' | 'style'> {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

/** A button in a React island. React Aria handles presses alike from a mouse, touch and keys. */
export function Button({ variant = 'primary', size = 'regular', ...props }: ButtonProps) {
  return <AriaButton {...props} className={buttonClass(variant, size)} />;
}
