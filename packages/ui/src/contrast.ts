/** Red, green and blue, each from 0 to 255. */
export type Rgb = readonly [red: number, green: number, blue: number];

const HEX = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i;
const RGB = /^rgb\(\s*(\d+)\s+(\d+)\s+(\d+)\s*(?:\/\s*([\d.]+)\s*)?\)$/;

/** Reads a colour written as `#rrggbb` or `rgb(r g b / alpha)`. */
export function parseColour(css: string): { rgb: Rgb; alpha: number } {
  const hex = HEX.exec(css.trim());
  if (hex) {
    const [, r = '', g = '', b = ''] = hex;
    return {
      rgb: [Number.parseInt(r, 16), Number.parseInt(g, 16), Number.parseInt(b, 16)],
      alpha: 1,
    };
  }
  const rgb = RGB.exec(css.trim());
  if (rgb) {
    const [, r = '', g = '', b = '', alpha = '1'] = rgb;
    return { rgb: [Number(r), Number(g), Number(b)], alpha: Number(alpha) };
  }
  throw new Error(`Not a #rrggbb or rgb() colour: ${css}`);
}

/** The colour seen where `colour`, which may be translucent, is drawn over an opaque `ground`. */
export function composite(colour: string, ground: string): Rgb {
  const top = parseColour(colour);
  const [r, g, b] = parseColour(ground).rgb;
  const mix = (channel: number, under: number) => channel * top.alpha + under * (1 - top.alpha);
  return [mix(top.rgb[0], r), mix(top.rgb[1], g), mix(top.rgb[2], b)];
}

function linear(channel: number): number {
  const c = channel / 255;
  return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

/** Relative luminance, as WCAG 2.2 defines it. */
export function luminance([r, g, b]: Rgb): number {
  return 0.2126 * linear(r) + 0.7152 * linear(g) + 0.0722 * linear(b);
}

/** The WCAG 2.2 contrast ratio between two colours, from 1 to 21. */
export function contrast(a: Rgb, b: Rgb): number {
  const [light, dark] = [luminance(a), luminance(b)].sort((x, y) => y - x) as [number, number];
  return (light + 0.05) / (dark + 0.05);
}
