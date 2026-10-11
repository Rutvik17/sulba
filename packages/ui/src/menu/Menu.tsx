import {
  Menu as AriaMenu,
  MenuItem as AriaMenuItem,
  type MenuItemProps,
  type MenuProps,
} from 'react-aria-components/Menu';
import { Popover } from 'react-aria-components/Popover';
import { classes } from '../classes';
import styles from './menu.module.css';

export { MenuTrigger } from 'react-aria-components/Menu';

const css = classes(styles, 'popover', 'menu', 'item');

/**
 * A menu of actions. Put it in a MenuTrigger after the button that opens it: arrow keys move
 * through the items, Enter or a press chooses one and closes the menu, and Escape closes it.
 */
export function Menu<T extends object>(props: Omit<MenuProps<T>, 'className' | 'style'>) {
  return (
    <Popover placement="bottom start" offset={8} className={css.popover}>
      <AriaMenu {...props} className={css.menu} />
    </Popover>
  );
}

export function MenuItem<T extends object>(props: Omit<MenuItemProps<T>, 'className' | 'style'>) {
  return <AriaMenuItem {...props} className={css.item} />;
}
