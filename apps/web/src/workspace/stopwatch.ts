// The time a learner spends on a stage: it runs while the page is in view, and each attempt takes
// what has run since the one before.

export interface Stopwatch {
  /** The whole seconds since the last lap, or since the stopwatch started. */
  lap(): number;
  stop(): void;
}

/** Whether the page is in view, and a way to hear when that changes. */
export interface View {
  visible(): boolean;
  onChange(listener: () => void): () => void;
}

const page: View = {
  visible: () => document.visibilityState === 'visible',
  onChange: (listener) => {
    document.addEventListener('visibilitychange', listener);
    return () => document.removeEventListener('visibilitychange', listener);
  },
};

export function stopwatch(
  view: View = page,
  now: () => number = () => performance.now(),
): Stopwatch {
  let since: number | null = view.visible() ? now() : null;
  let banked = 0;
  const off = view.onChange(() => {
    if (view.visible()) since ??= now();
    else if (since !== null) {
      banked += now() - since;
      since = null;
    }
  });
  return {
    lap() {
      const elapsed = banked + (since === null ? 0 : now() - since);
      banked = 0;
      if (since !== null) since = now();
      return Math.round(elapsed / 1000);
    },
    stop: off,
  };
}
