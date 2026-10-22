// The dashboard: the desk's usage over the last days, a row for each UTC day, with what its
// tokens would cost at the model's prices.
import { ApiError, type Day, type Desk } from './api.ts';

/** What the desk's model costs, in dollars for a million tokens of each kind. */
export interface Prices {
  readonly prompt: number;
  readonly completion: number;
}

const dayName = new Intl.DateTimeFormat('en-US', {
  weekday: 'short',
  month: 'short',
  day: 'numeric',
  timeZone: 'UTC',
});
const count = new Intl.NumberFormat('en-US');
const share = new Intl.NumberFormat('en-US', { style: 'percent' });
const seconds = new Intl.NumberFormat('en-US', {
  style: 'unit',
  unit: 'second',
  maximumFractionDigits: 1,
});
const dollars = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 2,
  maximumFractionDigits: 4,
});
const none = '—';
const dayMs = 24 * 60 * 60 * 1000;

/** A day with no turns, which the desk leaves out of its answer. */
function quiet(day: string): Day {
  return {
    day,
    turns: 0,
    done: 0,
    prompt_tokens: 0,
    completion_tokens: 0,
    p50_seconds: 0,
    p90_seconds: 0,
  };
}

/** What the tokens cost, in dollars. */
function cost(prompt: number, completion: number, prices: Prices): number {
  return (prompt * prices.prompt + completion * prices.completion) / 1_000_000;
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
  const given = new Map(usage.map((day) => [day.day, day]));
  // Today in UTC, whatever the time zone of the machine the page runs on.
  const today = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
  const range = Array.from({ length: days }, (_, index) => {
    const day = new Date(today - (days - 1 - index) * dayMs).toISOString().slice(0, 10);
    return given.get(day) ?? quiet(day);
  });

  const table = document.createElement('table');
  table.createCaption().textContent = `The desk's usage, last ${days} days`;
  const row = (section: HTMLTableSectionElement, cells: string[], header: 'col' | 'row') => {
    const tr = section.insertRow();
    cells.forEach((text, index) => {
      // A row's first cell names the row, as each cell of the header names its column.
      const heading = header === 'col' || index === 0;
      const cell = document.createElement(heading ? 'th' : 'td');
      if (heading) cell.scope = header;
      cell.textContent = text;
      tr.append(cell);
    });
  };
  row(
    table.createTHead(),
    ['Day', 'Turns', 'Done', 'Prompt tokens', 'Reply tokens', 'Cost', 'Median', '90th percentile'],
    'col',
  );
  const body = table.createTBody();
  for (const day of range) {
    const any = day.turns > 0;
    row(
      body,
      [
        dayName.format(new Date(`${day.day}T00:00:00Z`)),
        count.format(day.turns),
        any ? share.format(day.done / day.turns) : none,
        count.format(day.prompt_tokens),
        count.format(day.completion_tokens),
        dollars.format(cost(day.prompt_tokens, day.completion_tokens, prices)),
        any ? seconds.format(day.p50_seconds) : none,
        any ? seconds.format(day.p90_seconds) : none,
      ],
      'row',
    );
  }
  const sum = (field: 'turns' | 'done' | 'prompt_tokens' | 'completion_tokens') =>
    range.reduce((total, day) => total + day[field], 0);
  const turns = sum('turns');
  // The days' medians don't give the median of all their turns, so the total has none.
  row(
    table.createTFoot(),
    [
      'Total',
      count.format(turns),
      turns > 0 ? share.format(sum('done') / turns) : none,
      count.format(sum('prompt_tokens')),
      count.format(sum('completion_tokens')),
      dollars.format(cost(sum('prompt_tokens'), sum('completion_tokens'), prices)),
      none,
      none,
    ],
    'row',
  );
  return table;
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
  readonly #desk: Desk;
  readonly #prices: Prices;
  readonly #elements: DashboardElements;

  constructor(desk: Desk, prices: Prices, elements: DashboardElements) {
    this.#desk = desk;
    this.#prices = prices;
    this.#elements = elements;
  }

  /** Shows the usage of the last days, or what went wrong, in place of what was there. */
  async show(days: number, now: Date = new Date()): Promise<void> {
    const { place, status } = this.#elements;
    status.textContent = '';
    try {
      const usage = await this.#desk.usage(days);
      place.replaceChildren(usageTable(place.ownerDocument, usage, days, now, this.#prices));
    } catch (error) {
      // Numbers from before stay off the page, so none are taken for today's.
      place.replaceChildren();
      status.textContent =
        error instanceof ApiError ? error.message : "The usage couldn't be loaded.";
    }
  }
}
