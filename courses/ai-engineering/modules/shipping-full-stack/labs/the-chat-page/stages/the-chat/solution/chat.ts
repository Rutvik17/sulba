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

const speakers = { caller: 'You', desk: 'The desk' } as const;

/** The chat of one conversation. */
export class Chat {
  readonly #desk: Desk;
  readonly #id: string;
  readonly #elements: ChatElements;
  /** The reply that's coming, if any, and how to stop it. */
  #replying: AbortController | null = null;
  /** Open until the chat closes, which stops its listening to the form. */
  readonly #open = new AbortController();

  constructor(desk: Desk, conversation: Conversation, elements: ChatElements) {
    this.#desk = desk;
    this.#id = conversation.id;
    this.#elements = elements;
    elements.log.replaceChildren(
      ...conversation.messages.map((message) => this.#message(message.role, message.content)),
    );
    elements.form.addEventListener(
      'submit',
      (event) => {
        // The message goes to the desk from here, so the browser doesn't send the form itself.
        event.preventDefault();
        void this.send(elements.input.value);
      },
      { signal: this.#open.signal },
    );
  }

  /**
   * Sends the caller's message, and puts the reply on the page as it comes. A turn that doesn't
   * end in a reply leaves the page as it was, with the message back in the box.
   */
  async send(content: string): Promise<void> {
    const text = content.trim();
    if (text === '' || this.#replying !== null || this.#open.signal.aborted) return;
    const { log, input, send, status } = this.#elements;
    const controller = new AbortController();
    this.#replying = controller;
    const asked = this.#message('caller', text);
    const answer = this.#message('desk', '');
    const said = answer.querySelector('.text') ?? answer;
    log.append(asked, answer);
    input.value = '';
    status.textContent = '';
    send.disabled = true;
    // A screen reader waits for the whole reply, rather than reading out each piece as it comes.
    log.setAttribute('aria-busy', 'true');
    let replied = false;
    let problem: string | null = null;
    try {
      for await (const event of reply(this.#desk, this.#id, text, controller.signal)) {
        if (event.kind === 'text') said.append(event.delta);
        else if (event.kind === 'done') {
          said.textContent = event.content;
          replied = true;
        } else if (event.kind === 'error') problem = event.title;
      }
    } catch (error) {
      // A reply stopped by close() isn't a problem to show.
      if (!controller.signal.aborted) {
        problem = error instanceof ApiError ? error.message : "The message couldn't be sent.";
      }
    } finally {
      this.#replying = null;
      log.setAttribute('aria-busy', 'false');
      send.disabled = false;
    }
    if (replied) return;
    // The desk keeps no part of a turn it didn't finish, so the page doesn't either.
    asked.remove();
    answer.remove();
    if (input.value === '') input.value = text;
    if (problem !== null) status.textContent = problem;
  }

  /**
   * Stops the reply that's coming, if any, and takes no more messages from the form, as when
   * the caller opens another conversation.
   */
  close(): void {
    this.#open.abort();
    this.#replying?.abort();
  }

  /** A message's element: who said it, and what they said, as text. */
  #message(role: Message['role'], content: string): HTMLElement {
    // The log's own document makes the elements, so the chat works in any document.
    const document = this.#elements.log.ownerDocument;
    const message = document.createElement('div');
    message.className = 'message';
    message.dataset.role = role;
    const who = document.createElement('p');
    who.className = 'who';
    who.textContent = speakers[role];
    const said = document.createElement('p');
    said.className = 'text';
    said.textContent = content;
    message.append(who, said);
    return message;
  }
}
