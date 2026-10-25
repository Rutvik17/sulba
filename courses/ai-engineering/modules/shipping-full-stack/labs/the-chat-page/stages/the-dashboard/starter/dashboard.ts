// The dashboard: the desk's usage over the last days, a row for each UTC day, with what its
// tokens would cost at the model's prices.
import { ApiError, type Day, type Desk } from './api.ts';

/** What the desk's model costs, in dollars for a million tokens of each kind. */
export interface Prices {
  readonly prompt: number;
  readonly completion: number;
}

/**
 * The usage table of the last `days` UTC days, today's included, earliest first: each day's
 * turns, the share of them done, their tokens and cost, and the median and 90th percentile of
 * their seconds, then the total.
 */
export function usageTable(
  document: Document,
  usage: readonly Day[],
  days: number,
  now: Date,
  prices: Prices,
): HTMLTableElement {
  throw new Error('usageTable() is not written yet.');
}

/** The parts of the page the dashboard works with. */
export interface DashboardElements {
  /** Where the table goes. */
  readonly place: HTMLElement;
  /** A status, for what went wrong. */
  readonly status: HTMLElement;
}

/** The dashboard of the person's usage of the desk. */
export class Dashboard {
  constructor(desk: Desk, prices: Prices, elements: DashboardElements) {
    throw new Error('Dashboard is not written yet.');
  }

  /** Shows the usage of the last days, or what went wrong, in place of what was there. */
  async show(days: number, now: Date = new Date()): Promise<void> {
    throw new Error('show() is not written yet.');
  }
}
