// The characters a formula draws, so a check can hold them to the math font. A browser draws an
// identifier of one letter, such as <mi>x</mi>, as its math italic form (MathML Core's
// `text-transform: math-auto`), so those count as the italic character, not the letter typed.

/** MathML Core's italic mappings (appendix C.1): the ranges, then the single characters. */
const italicRanges: readonly [from: number, to: number, start: number][] = [
  [0x41, 0x5a, 0x1d434], // A–Z
  [0x61, 0x7a, 0x1d44e], // a–z, with h below
  [0x391, 0x3a1, 0x1d6e2], // Α–Ρ
  [0x3a3, 0x3a9, 0x1d6f4], // Σ–Ω
  [0x3b1, 0x3c9, 0x1d6fc], // α–ω
];

const italicSingles = new Map<number, number>([
  [0x68, 0x210e], // h
  [0x131, 0x1d6a4], // ı
  [0x237, 0x1d6a5], // ȷ
  [0x3f4, 0x1d6f3], // ϴ
  [0x2207, 0x1d6fb], // ∇
  [0x2202, 0x1d715], // ∂
  [0x3f5, 0x1d716], // ϵ
  [0x3d1, 0x1d717], // ϑ
  [0x3f0, 0x1d718], // ϰ
  [0x3d5, 0x1d719], // ϕ
  [0x3f1, 0x1d71a], // ϱ
  [0x3d6, 0x1d71b], // ϖ
]);

export function italicOf(point: number): number {
  const single = italicSingles.get(point);
  if (single !== undefined) return single;
  for (const [from, to, start] of italicRanges) {
    if (point >= from && point <= to) return start + point - from;
  }
  return point;
}

// Invisible operators and spaces take no glyph.
const invisible = new Set([0x20, 0xa0, 0x200b, 0x2061, 0x2062, 0x2063, 0x2064]);

function decodeEntities(text: string): string {
  return text
    .replace(/&#x([0-9a-f]+);/gi, (_, hex: string) =>
      String.fromCodePoint(Number.parseInt(hex, 16)),
    )
    .replace(/&#(\d+);/g, (_, decimal: string) => String.fromCodePoint(Number(decimal)))
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&amp;/g, '&');
}

/** Every character a formula's MathML draws. */
export function drawnCharacters(mathml: string): Set<number> {
  const drawn = new Set<number>();
  for (const [, element, attributes = '', raw = ''] of mathml.matchAll(
    /<(mi|mo|mn|mtext|ms)\b([^>]*)>([^<]*)<\/\1>/g,
  )) {
    const points = [...decodeEntities(raw)].map((char) => char.codePointAt(0) as number);
    const italic =
      element === 'mi' && points.length === 1 && !/mathvariant="normal"/.test(attributes);
    for (const point of points) {
      if (!invisible.has(point)) drawn.add(italic ? italicOf(point) : point);
    }
  }
  return drawn;
}
