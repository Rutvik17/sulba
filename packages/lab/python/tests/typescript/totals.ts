/** The sum of the amounts, in cents. */
export function total(amounts: readonly number[]): number {
  return amounts.reduce((sum, amount) => sum + amount, 0);
}

/** The amount in cents as dollars and cents, such as 12.50. */
export function dollars(cents: number): string {
  if (!Number.isInteger(cents)) {
    throw new RangeError(`${cents} isn't a whole number of cents.`);
  }
  return (cents / 100).toFixed(2);
}
