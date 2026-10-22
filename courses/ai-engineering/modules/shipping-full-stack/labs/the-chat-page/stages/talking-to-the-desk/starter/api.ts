// The desk's API, as the chat page calls it: each request, the shape of its answer, and an
// answer that isn't a success as the problem details it carries (RFC 9457).

export type Page = 'ssa' | 'va' | 'studentaid' | 'dmv';

/** A message of a conversation: the caller's, or the desk's reply. */
export interface Message {
  readonly role: 'caller' | 'desk';
  readonly content: string;
}

export interface Conversation {
  readonly id: string;
  readonly page: Page | null;
  readonly messages: readonly Message[];
}

/** A conversation in the list of the person's own, newest first. */
export interface Summary {
  readonly id: string;
  readonly page: Page | null;
  readonly started_at: string;
}

/** The person signed in. */
export interface Account {
  readonly id: number;
  readonly email: string | null;
  readonly name: string | null;
}

/** A day's turns, in UTC, as the dashboard shows them. */
export interface Day {
  readonly day: string;
  readonly turns: number;
  readonly done: number;
  readonly prompt_tokens: number;
  readonly completion_tokens: number;
  readonly p50_seconds: number;
  readonly p90_seconds: number;
}

/** One thing wrong with a request's body, and where, as a JSON Pointer. */
export interface Fault {
  readonly detail: string;
  readonly pointer: string;
}

/** An answer that isn't a success: its status, and the problem details it gives, if any. */
export class ApiError extends Error {
  readonly status: number;
  readonly title: string;
  readonly detail: string | null;
  readonly errors: readonly Fault[];

  constructor(status: number, title: string, detail: string | null, errors: readonly Fault[]) {
    super(detail ?? title);
    this.name = 'ApiError';
    this.status = status;
    this.title = title;
    this.detail = detail;
    this.errors = errors;
  }
}

/** The error an answer that isn't a success stands for, from its problem details if it has them. */
export async function failure(response: Response): Promise<ApiError> {
  return new ApiError(response.status, response.statusText, null, []);
}

/** The desk's API, through a fetch function: the browser's, or a test's. */
export class Desk {
  readonly #fetch: typeof fetch;

  constructor(fetcher: typeof fetch = fetch) {
    this.#fetch = fetcher;
  }

  /** A new conversation, from the help pages it's opened on, if any. */
  start(page: Page | null = null): Promise<Conversation> {
    return this.#json('POST', '/conversations', { page });
  }

  /** The person's conversations, newest first. */
  conversations(): Promise<Summary[]> {
    return this.#json('GET', '/conversations');
  }

  conversation(id: string): Promise<Conversation> {
    return this.#json('GET', `/conversations/${id}`);
  }

  me(): Promise<Account> {
    return this.#json('GET', '/me');
  }

  /** The usage of the last days, today's included, from 1 to 90 of them. */
  usage(days = 7): Promise<Day[]> {
    return this.#json('GET', `/usage?days=${days}`);
  }

  /** Sends the caller's message, and answers with the reply's event stream. */
  say(id: string, content: string, signal?: AbortSignal): Promise<Response> {
    throw new Error(`Sending ${content} to ${id} isn't written yet${signal ? '.' : ''}`);
  }

  async #json<T>(method: 'GET' | 'POST', path: string, body?: unknown): Promise<T> {
    const response = await this.#fetch(path, { method, body: JSON.stringify(body) });
    return (await response.json()) as T;
  }
}
