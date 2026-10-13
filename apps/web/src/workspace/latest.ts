/**
 * Runs one request at a time. While one runs, a newer request takes the place of any that was
 * waiting, so only the latest runs next: dragging a slider never leaves a queue behind. `run` must
 * not reject.
 */
export function latestOnly<Request, Result>(
  run: (request: Request) => Promise<Result>,
  done: (request: Request, result: Result) => void,
): (request: Request) => void {
  let waiting: { readonly request: Request } | null = null;
  let running = false;
  return (request) => {
    waiting = { request };
    if (running) return;
    running = true;
    void (async () => {
      while (waiting) {
        const next = waiting.request;
        waiting = null;
        done(next, await run(next));
      }
      running = false;
    })();
  };
}
