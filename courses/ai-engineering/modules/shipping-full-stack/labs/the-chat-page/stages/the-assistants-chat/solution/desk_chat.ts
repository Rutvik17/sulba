// The chat, as the assistant wrote it: a conversation's messages, the caller's message sent from
// the form, and the desk's reply as it comes, with its formatting.
import { ApiError, type Conversation, type Desk, type Message } from './api.ts';
import type { ChatElements } from './chat.ts';
import { reply } from './stream.ts';

const speakers = { caller: 'You', desk: 'The desk' } as const;

/** The chat of one conversation. */
export class Chat {
  readonly #desk: Desk;
  readonly #id: string;
  readonly #elements: ChatElements;
  #replying: AbortController | null = null;
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
        event.preventDefault();
        void this.send(elements.input.value);
      },
      { signal: this.#open.signal },
    );
  }

  /** Sends the caller's message, and puts the reply on the page as it comes. */
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
      if (!controller.signal.aborted) {
        problem = error instanceof ApiError ? error.message : "The message couldn't be sent.";
      }
    } finally {
      this.#replying = null;
      log.setAttribute('aria-busy', 'false');
      send.disabled = false;
    }
    if (replied) return;
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

  #message(role: Message['role'], content: string): HTMLElement {
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
