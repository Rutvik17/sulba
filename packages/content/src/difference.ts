/**
 * Where two values parsed from JSON first differ, such as `readouts.0.value`, or null if they
 * agree: the same keys, arrays of the same length, and equal strings, booleans and nulls. Two
 * numbers agree when they are within `tolerance` of each other, or for numbers above 1 within
 * `tolerance` times the larger, since two runs of the same sum can differ in its last digits.
 */
export function difference(a: unknown, b: unknown, tolerance: number, at = ''): string | null {
  if (typeof a === 'number' && typeof b === 'number') {
    return Math.abs(a - b) <= tolerance * Math.max(1, Math.abs(a), Math.abs(b)) ? null : at;
  }
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) return at;
    for (const [index, item] of a.entries()) {
      const found = difference(item, b[index], tolerance, at ? `${at}.${index}` : String(index));
      if (found !== null) return found;
    }
    return null;
  }
  if (a && b && typeof a === 'object' && typeof b === 'object') {
    for (const key of new Set([...Object.keys(a), ...Object.keys(b)])) {
      const found = difference(
        (a as Record<string, unknown>)[key],
        (b as Record<string, unknown>)[key],
        tolerance,
        at ? `${at}.${key}` : key,
      );
      if (found !== null) return found;
    }
    return null;
  }
  return a === b ? null : at;
}

/** The part of a value parsed from JSON at a path such as `readouts.0.value`. */
export function partOf(value: unknown, path: string): unknown {
  return path
    .split('.')
    .filter(Boolean)
    .reduce<unknown>((part, key) => (part as Record<string, unknown> | undefined)?.[key], value);
}
