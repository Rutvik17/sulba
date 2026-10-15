// Each answer to a review card. The browser keeps every review it records, signed in or not, and
// works out each card's schedule from them, so the log is what has to follow the learner from
// device to device (decision record 20). Each review carries an id made here, so one sent twice
// is kept once.

/** Again, Hard, Good or Easy, numbered as FSRS numbers them. */
export type Rating = 1 | 2 | 3 | 4;

/** A review as the reviews table takes it. The database fills in the learner and arrival. */
export interface Review {
  readonly id: string;
  readonly card_id: string;
  readonly rating: Rating;
  /** When the learner answered, by their clock. */
  readonly reviewed_at: string;
}

export function reviewOf(
  cardId: string,
  rating: Rating,
  at: Date,
  id: string = crypto.randomUUID(),
): Review {
  return { id, card_id: cardId, rating, reviewed_at: at.toISOString() };
}

export function isRating(value: unknown): value is Rating {
  return value === 1 || value === 2 || value === 3 || value === 4;
}

const logKey = 'sulba:reviews';

type Storage = Pick<globalThis.Storage, 'getItem' | 'setItem'>;

/**
 * Every review this browser has, in the order it took them in. It holds them for the page too, so
 * reviews still count while storage is blocked or full, and it reads storage again before each
 * write, so two tabs don't undo each other's reviews.
 */
export class ReviewLog {
  readonly #storage: Storage;
  #reviews: readonly Review[];

  constructor(storage: Storage) {
    this.#storage = storage;
    this.#reviews = this.#read();
  }

  all(): readonly Review[] {
    return this.#reviews;
  }

  add(review: Review): void {
    this.takeIn([review]);
  }

  /** Keeps the reviews it doesn't have yet, such as those made on another device. */
  takeIn(reviews: readonly Review[]): void {
    const merged = [...this.#read()];
    const ids = new Set(merged.map(idOf));
    for (const review of [...this.#reviews, ...reviews]) {
      if (isReview(review) && !ids.has(review.id)) {
        merged.push(review);
        ids.add(review.id);
      }
    }
    this.#reviews = merged;
    try {
      this.#storage.setItem(logKey, JSON.stringify(merged));
    } catch {
      // Storage is blocked or full: these reviews last only as long as the page.
    }
  }

  #read(): Review[] {
    try {
      const kept: unknown = JSON.parse(this.#storage.getItem(logKey) ?? '[]');
      return Array.isArray(kept) ? kept.filter(isReview) : [];
    } catch {
      return [];
    }
  }
}

function idOf(review: Review): string {
  return review.id;
}

function isReview(value: unknown): value is Review {
  if (typeof value !== 'object' || value === null) return false;
  const review = value as Record<keyof Review, unknown>;
  return (
    typeof review.id === 'string' &&
    typeof review.card_id === 'string' &&
    /^crd_[0-9a-z]{6}$/.test(review.card_id) &&
    isRating(review.rating) &&
    typeof review.reviewed_at === 'string' &&
    !Number.isNaN(Date.parse(review.reviewed_at))
  );
}
