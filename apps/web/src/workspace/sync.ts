// While a learner is signed in, the workspace sends each attempt to their account and takes in the
// stages they passed on other devices (decision record 18). Signed out, nothing is kept or sent,
// and supabase-js never loads.
import { PUBLIC_SUPABASE_PUBLISHABLE_KEY, PUBLIC_SUPABASE_URL } from 'astro:env/client';
import { type Attempt, attemptOf, type Event, Outbox } from '@sulba/data/outbox';
import { hasSession, localStore } from '@sulba/data/session';
import type { Passed } from '@sulba/data/sync';

export interface Recorder {
  /** Keeps what happened in a stage, with the seconds spent there since its last attempt. */
  record(
    stage: { readonly id: string; readonly version: string },
    event: Event,
    seconds: number,
  ): void;
  /** Keeps attempts made on the learner's machine, with their own ids and times (decision record 28). */
  takeIn(attempts: readonly Attempt[]): void;
  stop(): void;
}

const quiet: Recorder = { record: () => undefined, takeIn: () => undefined, stop: () => undefined };

/** How long the outbox waits after an attempt, so a burst of attempts goes in one request. */
const pause = 2000;

/**
 * Starts syncing when this browser holds a session. Once a visit, `arrived` hears the stages passed
 * in the account; then the outbox goes after each attempt, and again when the connection returns.
 */
export function startSync(arrived: (passed: readonly Passed[]) => void): Recorder {
  const storage = localStore();
  if (!hasSession(storage)) return quiet;
  const outbox = new Outbox(storage);
  const live = Promise.all([import('@sulba/data/client'), import('@sulba/data/sync')]).then(
    ([{ connect }, sync]) => ({
      ...sync,
      client: connect(PUBLIC_SUPABASE_URL, PUBLIC_SUPABASE_PUBLISHABLE_KEY),
    }),
  );
  let stopped = false;
  let timer: ReturnType<typeof setTimeout> | undefined;

  const flush = async () => {
    // A session gone from storage was ended for good, here or by its expiry, so what waits for it
    // can't be sent; a session kept but unrefreshed is only offline, so its attempts wait.
    if (!hasSession(storage)) {
      outbox.clear();
      return;
    }
    const { client, send } = await live;
    const { data } = await client.auth.getSession();
    if (data.session) await send(client, outbox);
  };
  const soon = () => {
    clearTimeout(timer);
    timer = setTimeout(() => void flush().catch(() => undefined), pause);
  };
  addEventListener('online', soon);

  void (async () => {
    const { client, readPassed } = await live;
    const { data } = await client.auth.getSession();
    if (!data.session) return;
    const passed = await readPassed(client);
    if (!stopped) arrived(passed);
    soon();
  })().catch(() => undefined);

  return {
    record(stage, event, seconds) {
      if (stopped || !hasSession(storage)) return;
      outbox.add(attemptOf(stage, event, seconds, new Date()));
      soon();
    },
    takeIn(attempts) {
      if (stopped || !hasSession(storage) || attempts.length === 0) return;
      for (const attempt of attempts) outbox.add(attempt);
      soon();
    },
    stop() {
      stopped = true;
      clearTimeout(timer);
      removeEventListener('online', soon);
      void flush().catch(() => undefined);
    },
  };
}
