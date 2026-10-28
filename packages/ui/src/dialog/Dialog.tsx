import type { ReactNode } from 'react';
import {
  Dialog as AriaDialog,
  Heading,
  Modal,
  ModalOverlay,
  type ModalOverlayProps,
} from 'react-aria-components/Modal';
import { classes } from '../classes';
import styles from './dialog.module.css';

export { DialogTrigger } from 'react-aria-components/Modal';

const css = classes(styles, 'overlay', 'modal', 'dialog', 'title', 'body', 'actions');

export interface DialogProps extends Omit<ModalOverlayProps, 'className' | 'style' | 'children'> {
  /** The dialog's heading, which also names it. */
  title: string;
  children: ReactNode;
  /** The buttons along the foot, the main one last. A button with slot="close" shuts the dialog. */
  actions: ReactNode;
}

/**
 * A dialog in the middle of a veiled page, for a choice that needs the person's attention. Put it
 * in a DialogTrigger after the button that opens it, or control it with isOpen. Escape shuts it,
 * and so does a press on the veil unless isDismissable is false.
 */
export function Dialog({ title, children, actions, isDismissable = true, ...props }: DialogProps) {
  return (
    <ModalOverlay {...props} isDismissable={isDismissable} className={css.overlay}>
      <Modal className={css.modal}>
        <AriaDialog className={css.dialog}>
          <Heading slot="title" className={css.title}>
            {title}
          </Heading>
          <div className={css.body}>{children}</div>
          <div className={css.actions}>{actions}</div>
        </AriaDialog>
      </Modal>
    </ModalOverlay>
  );
}
