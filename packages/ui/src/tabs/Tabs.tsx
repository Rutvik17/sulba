import {
  Tab as AriaTab,
  TabList as AriaTabList,
  TabPanel as AriaTabPanel,
  Tabs as AriaTabs,
  type TabListProps,
  type TabPanelProps,
  type TabProps,
  type TabsProps,
} from 'react-aria-components/Tabs';
import { classes } from '../classes';
import styles from './tabs.module.css';

const css = classes(styles, 'tabs', 'list', 'tab', 'panel');

type Unstyled<Props> = Omit<Props, 'className' | 'style'>;

/**
 * Tabs, built on React Aria's: arrow keys move between tabs and show each one's panel, and Home
 * and End reach the first and last.
 */
export function Tabs(props: Unstyled<TabsProps>) {
  return <AriaTabs {...props} className={css.tabs} />;
}

/** The row of tabs. It needs a name, such as aria-label="Session". */
export function TabList<T extends object>(props: Unstyled<TabListProps<T>>) {
  return <AriaTabList {...props} className={css.list} />;
}

export function Tab(props: Unstyled<TabProps>) {
  return <AriaTab {...props} className={css.tab} />;
}

export function TabPanel(props: Unstyled<TabPanelProps>) {
  return <AriaTabPanel {...props} className={css.panel} />;
}
