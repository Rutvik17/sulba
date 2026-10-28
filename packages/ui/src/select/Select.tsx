import {
  Select as AriaSelect,
  Button,
  Label,
  ListBox,
  ListBoxItem,
  Popover,
  SelectValue,
  Text,
} from 'react-aria-components/Select';
import { classes } from '../classes';
import styles from './select.module.css';

const css = classes(
  styles,
  'field',
  'label',
  'trigger',
  'small',
  'value',
  'chevron',
  'popover',
  'list',
  'option',
  'text',
  'name',
  'description',
  'check',
);

export interface SelectOption<T extends string> {
  readonly id: T;
  readonly name: string;
  /** A line under the name, in the list only. */
  readonly description?: string;
}

export interface SelectProps<T extends string> {
  label: string;
  /** Leaves the label unseen, for a select whose place says what it is, as in a table's row. */
  hideLabel?: boolean;
  options: readonly SelectOption<T>[];
  value: T;
  onChange: (value: T) => void;
  isDisabled?: boolean;
  size?: 'regular' | 'small';
}

/**
 * One choice from a short list, which opens under the button. Arrow keys move through the
 * options, typing jumps to one, Enter or a press chooses it, and Escape closes the list.
 */
export function Select<T extends string>({
  label,
  hideLabel = false,
  options,
  value,
  onChange,
  isDisabled = false,
  size = 'regular',
}: SelectProps<T>) {
  return (
    <AriaSelect
      {...(hideLabel ? { 'aria-label': label } : {})}
      selectedKey={value}
      onSelectionChange={(key) => {
        const chosen = options.find(({ id }) => id === key);
        if (chosen) onChange(chosen.id);
      }}
      isDisabled={isDisabled}
      className={css.field}
    >
      {hideLabel ? null : <Label className={css.label}>{label}</Label>}
      <Button className={size === 'small' ? `${css.trigger} ${css.small}` : css.trigger}>
        <SelectValue className={css.value}>{({ selectedText }) => selectedText}</SelectValue>
        <svg className={css.chevron} viewBox="0 0 12 12" aria-hidden="true">
          <path d="M3 4.5 6 7.5 9 4.5" />
        </svg>
      </Button>
      <Popover placement="bottom start" offset={4} className={css.popover}>
        <ListBox items={options} className={css.list}>
          {(option) => (
            <ListBoxItem id={option.id} textValue={option.name} className={css.option}>
              {({ isSelected }) => (
                <>
                  <span className={css.text}>
                    <span className={css.name}>{option.name}</span>
                    {option.description ? (
                      <Text slot="description" className={css.description}>
                        {option.description}
                      </Text>
                    ) : null}
                  </span>
                  {isSelected ? (
                    <svg className={css.check} viewBox="0 0 12 12" aria-hidden="true">
                      <path d="M2.5 6.5 5 9l4.5-6" />
                    </svg>
                  ) : null}
                </>
              )}
            </ListBoxItem>
          )}
        </ListBox>
      </Popover>
    </AriaSelect>
  );
}
