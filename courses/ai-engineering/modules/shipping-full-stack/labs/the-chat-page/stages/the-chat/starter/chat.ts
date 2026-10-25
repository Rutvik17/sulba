// The chat: a conversation's messages on the page, the caller's message sent from the form, and
// the desk's reply put on the page as it comes, in a way a screen reader can follow.
import { ApiError, type Conversation, type Desk, type Message } from './api.ts';
import { reply } from './stream.ts';

/** The parts of the page the chat works with. */
export interface ChatElements {
  /** The messages: a log, which a screen reader reads out as messages join it. */
  readonly log: HTMLElement;
  readonly form: HTMLFormElement;
  readonly input: HTMLTextAreaElement;
  readonly send: HTMLButtonElement;
  /** A status, which a screen reader reads out when its text changes. */
  readonly status: HTMLElement;
}

/** The chat of one conversation. */
export class Chat {
  constructor(desk: Desk, conversation: Conversation, elements: ChatElements) {
    throw new Error('Chat is not written yet.');
  }

  /**
   * Sends the caller's message, and puts the reply on the page as it comes. A turn that doesn't
   * end in a reply leaves the page as it was, with the message back in the box.
   */
  async send(content: string): Promise<void> {
    throw new Error('send() is not written yet.');
  }

  /**
   * Stops the reply that's coming, if any, and takes no more messages from the form, as when
   * the caller opens another conversation.
   */
  close(): void {
    throw new Error('close() is not written yet.');
  }
}
