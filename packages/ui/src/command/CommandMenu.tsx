import { Autocomplete, useFilter } from 'react-aria-components/Autocomplete';
import { Collection, Header, Menu, MenuItem, MenuSection, Text } from 'react-aria-components/Menu';
import { Dialog, Modal, ModalOverlay } from 'react-aria-components/Modal';
import { Input, TextField, type TextFieldProps } from 'react-aria-components/TextField';
import { classes } from '../classes';
import { Keys, type Steps } from '../keys/Keys';
import styles from './command.module.css';

const css = classes(
  styles,
  'overlay',
  'modal',
  'dialog',
  'field',
  'input',
  'menu',
  'section',
  'header',
  'item',
  'label',
  'note',
  'empty',
);

export interface Command {
  readonly id: string;
  readonly label: string;
  /** A word or two after the label, such as "Current". */
  readonly note?: string;
  /** The shortcut that does the same thing. */
  readonly keys?: Steps;
}

export interface CommandGroup {
  readonly id: string;
  readonly title: string;
  readonly commands: readonly Command[];
}

export interface CommandMenuProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  /** Names the menu and its search field. */
  label: string;
  placeholder: string;
  groups: readonly CommandGroup[];
  /** What the search field holds, which filters the commands. */
  query: string;
  onQueryChange: (query: string) => void;
  onAction: (id: string) => void;
  /** A key pressed in the search field, before the menu acts on it. */
  onKeyDown?: NonNullable<TextFieldProps['onKeyDown']>;
}

/**
 * A search field over every command, in a card near the top of a veiled page. Typing filters the
 * commands, ignoring case and accents; the arrow keys move through them while the focus stays in
 * the field, Enter runs the highlighted one, and Escape or a press on the veil closes the menu.
 */
export function CommandMenu({
  isOpen,
  onOpenChange,
  label,
  placeholder,
  groups,
  query,
  onQueryChange,
  onAction,
  onKeyDown,
}: CommandMenuProps) {
  const { contains } = useFilter({ sensitivity: 'base' });

  return (
    <ModalOverlay isOpen={isOpen} onOpenChange={onOpenChange} isDismissable className={css.overlay}>
      <Modal className={css.modal}>
        <Dialog aria-label={label} className={css.dialog}>
          <Autocomplete filter={contains} inputValue={query} onInputChange={onQueryChange}>
            <TextField
              aria-label={label}
              autoFocus
              className={css.field}
              {...(onKeyDown ? { onKeyDown } : {})}
            >
              <Input placeholder={placeholder} className={css.input} />
            </TextField>
            <Menu
              items={groups}
              onAction={(id) => onAction(String(id))}
              renderEmptyState={() => <p className={css.empty}>No command matches.</p>}
              className={css.menu}
            >
              {(group) => (
                <MenuSection id={group.id} className={css.section}>
                  <Header className={css.header}>{group.title}</Header>
                  <Collection items={group.commands}>
                    {(command) => (
                      <MenuItem id={command.id} textValue={command.label} className={css.item}>
                        <Text slot="label" className={css.label}>
                          {command.label}
                        </Text>
                        {command.note ? <span className={css.note}>{command.note}</span> : null}
                        {command.keys ? <Keys steps={command.keys} /> : null}
                      </MenuItem>
                    )}
                  </Collection>
                </MenuSection>
              )}
            </Menu>
          </Autocomplete>
        </Dialog>
      </Modal>
    </ModalOverlay>
  );
}
