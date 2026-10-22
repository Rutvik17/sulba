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
  const type = response.headers.get('Content-Type') ?? '';
  const fallback = response.statusText || `The desk answered ${response.status}.`;
  if (!/^application\/(problem\+)?json\b/.test(type)) {
    return new ApiError(response.status, fallback, null, []);
  }
  const body: unknown = await response.json().catch(() => null);
  const details =
    typeof body === 'object' && body !== null ? (body as Record<string, unknown>) : {};
  const errors = Array.isArray(details.errors) ? (details.errors as Fault[]) : [];
  return new ApiError(
    response.status,
    typeof details.title === 'string' ? details.title : fallback,
    typeof details.detail === 'string' ? details.detail : null,
    errors,
  );
}

/** The desk's API, through a fetch function: the browser's, or a test's. */
export class Desk {
  readonly #fetch: typeof fetch;

  constructor(fetcher: typeof fetch = fetch) {
    // Called as a method, the browser's fetch would get this desk as its this, which it refuses.
    this.#fetch = (input, init) => fetcher(input, init);
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
    return this.#json('GET', `/conversations/${encodeURIComponent(id)}`);
  }

  me(): Promise<Account> {
    return this.#json('GET', '/me');
  }

  /** The usage of the last days, today's included, from 1 to 90 of them. */
  usage(days = 7): Promise<Day[]> {
    if (!Number.isInteger(days) || days < 1 || days > 90) {
      return Promise.reject(new RangeError('The usage covers from 1 to 90 days.'));
    }
    return this.#json('GET', `/usage?days=${days}`);
  }

  /** Sends the caller's message, and answers with the reply's event stream. */
  async say(id: string, content: string, signal?: AbortSignal): Promise<Response> {
    const response = await this.#fetch(`/conversations/${encodeURIComponent(id)}/messages`, {
      method: 'POST',
      headers: { Accept: 'text/event-stream', 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
      ...(signal === undefined ? {} : { signal }),
    });
    if (!response.ok) throw await failure(response);
    return response;
  }

  async #json<T>(method: 'GET' | 'POST', path: string, body?: unknown): Promise<T> {
    const response = await this.#fetch(path, {
      method,
      headers:
        body === undefined
          ? { Accept: 'application/json' }
          : { Accept: 'application/json', 'Content-Type': 'application/json' },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
    if (!response.ok) throw await failure(response);
    return (await response.json()) as T;
  }
}
