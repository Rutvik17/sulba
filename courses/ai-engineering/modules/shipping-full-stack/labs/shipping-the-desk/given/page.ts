// The desk's page: who's signed in, their conversations, the chat of the one open and the
// dashboard of their usage. `uv run sulba.py build` compiles it, with the files it imports, into
// static/, where the desk serves it.
import { type Account, ApiError, Desk } from './api.ts';
import { Chat } from './chat.ts';
import { Dashboard } from './dashboard.ts';

function byId<T extends HTMLElement>(id: string): T {
  const found = document.getElementById(id);
  if (found === null) throw new Error(`The page has no #${id}.`);
  return found as T;
}

const desk = new Desk();
const status = byId('status');
const chatElements = {
  log: byId('log'),
  form: byId<HTMLFormElement>('ask'),
  input: byId<HTMLTextAreaElement>('content'),
  send: byId<HTMLButtonElement>('send'),
  status,
};
const started = new Intl.DateTimeFormat('en-US', { dateStyle: 'medium', timeStyle: 'short' });
let chat: Chat | null = null;

function shown(error: unknown): void {
  status.textContent = error instanceof ApiError ? error.message : 'Something went wrong.';
}

/** Lists the person's conversations, the one open marked. */
async function list(open: string): Promise<void> {
  const summaries = await desk.conversations();
  byId('yours').replaceChildren(
    ...summaries.map((summary) => {
      const item = document.createElement('li');
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = started.format(new Date(summary.started_at));
      if (summary.id === open) button.setAttribute('aria-current', 'true');
      button.addEventListener('click', () => {
        openConversation(summary.id).catch(shown);
      });
      item.append(button);
      return item;
    }),
  );
}

/** Opens a conversation of the person's, or a new one, in place of the one open. */
async function openConversation(id: string | null): Promise<void> {
  const conversation = id === null ? await desk.start() : await desk.conversation(id);
  chat?.close();
  chat = new Chat(desk, conversation, chatElements);
  history.replaceState(null, '', `/?c=${encodeURIComponent(conversation.id)}`);
  await list(conversation.id);
}

async function main(): Promise<void> {
  let account: Account;
  try {
    account = await desk.me();
  } catch (error) {
    if (error instanceof ApiError && error.status === 403) {
      byId('sign-in').hidden = false;
      return;
    }
    throw error;
  }
  byId('who').textContent = account.name ?? account.email ?? '';
  const signOut = byId<HTMLButtonElement>('sign-out');
  signOut.hidden = false;
  signOut.addEventListener('click', () => {
    fetch('/auth/sign-out', { method: 'POST' }).then(() => location.assign('/'), shown);
  });
  byId('desk').hidden = false;
  byId('new').addEventListener('click', () => {
    openConversation(null).catch(shown);
  });
  const asked = new URLSearchParams(location.search).get('c');
  const newest = asked === null ? (await desk.conversations())[0]?.id : undefined;
  await openConversation(asked ?? newest ?? null);
  const prices = {
    prompt: Number(document.body.dataset.promptPrice ?? 0),
    completion: Number(document.body.dataset.completionPrice ?? 0),
  };
  const dashboard = new Dashboard(desk, prices, {
    place: byId('usage'),
    status: byId('usage-status'),
  });
  await dashboard.show(7);
}

main().catch(shown);
