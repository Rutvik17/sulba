import type { ReactNode } from 'react';
import {
  Dialog,
  Heading,
  Modal,
  ModalOverlay,
  type ModalOverlayProps,
} from 'react-aria-components/Modal';
import { Button } from '../button/Button';
import { classes } from '../classes';
import styles from './panel.module.css';

export { DialogTrigger } from 'react-aria-components/Modal';

const css = classes(styles, 'overlay', 'panel', 'dialog', 'header', 'title');

export interface SidePanelProps
  extends Omit<ModalOverlayProps, 'className' | 'style' | 'children' | 'isDismissable'> {
  /** The panel's heading, which also names the dialog. */
  title: string;
  children: ReactNode;
}

/**
 * A dialog that slides in from the right. Put it in a DialogTrigger after the button that opens
 * it. Escape, a press on the veiled page, or Close shuts it.
 */
export function SidePanel({ title, children, ...props }: SidePanelProps) {
  return (
    <ModalOverlay {...props} isDismissable className={css.overlay}>
      <Modal className={css.panel}>
        <Dialog className={css.dialog}>
          <header className={css.header}>
            <Heading slot="title" className={css.title}>
              {title}
            </Heading>
            <Button slot="close" variant="ghost" size="small">
              Close
            </Button>
          </header>
          {children}
        </Dialog>
      </Modal>
    </ModalOverlay>
  );
}
