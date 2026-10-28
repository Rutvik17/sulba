import {
  TextField as AriaTextField,
  type TextFieldProps as AriaTextFieldProps,
  FieldError,
  Input,
  Label,
  Text,
  TextArea,
} from 'react-aria-components/TextField';
import { classes } from '../classes';
import styles from './textfield.module.css';

const css = classes(
  styles,
  'field',
  'label',
  'control',
  'multiline',
  'prefix',
  'input',
  'note',
  'error',
);

export interface TextFieldProps
  extends Omit<AriaTextFieldProps, 'className' | 'style' | 'children' | 'isInvalid'> {
  label: string;
  /** A line under the field that says what goes in it. */
  description?: string;
  /** What's wrong with the value, shown in the description's place; null while nothing is. */
  error?: string | null;
  /** Fixed text before the value, such as the start of an address. Screen readers skip it, so
      the description should say the whole of what it means. */
  prefix?: string;
  placeholder?: string;
  /** Several lines, for text such as a note, which grows the box to 4 lines before it scrolls. */
  multiline?: boolean;
}

/** A labelled text input. Its error, when it has one, is announced with the field. */
export function TextField({
  label,
  description,
  error = null,
  prefix,
  placeholder,
  multiline = false,
  ...props
}: TextFieldProps) {
  return (
    <AriaTextField {...props} isInvalid={error !== null} className={css.field}>
      <Label className={css.label}>{label}</Label>
      <div className={multiline ? `${css.control} ${css.multiline}` : css.control}>
        {prefix ? (
          <span className={css.prefix} aria-hidden="true">
            {prefix}
          </span>
        ) : null}
        {multiline ? (
          <TextArea className={css.input} rows={4} {...(placeholder ? { placeholder } : {})} />
        ) : (
          <Input className={css.input} {...(placeholder ? { placeholder } : {})} />
        )}
      </div>
      {error !== null ? (
        <FieldError className={css.error}>{error}</FieldError>
      ) : description ? (
        <Text slot="description" className={css.note}>
          {description}
        </Text>
      ) : null}
    </AriaTextField>
  );
}
