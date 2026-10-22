/** A line for each amount, with its sign, then the balance. */
export function statement(amounts: readonly number[]): string[] {
  const balance = amounts.reduce((sum, amount) => sum + amount, 0);
  return [...amounts.map((amount) => (amount < 0 ? `${amount}` : `+${amount}`)), `= ${balance}`];
}
