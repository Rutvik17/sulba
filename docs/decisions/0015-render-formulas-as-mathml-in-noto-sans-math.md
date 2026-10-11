# 15. Render formulas as MathML at build time, in Noto Sans Math

- Status: accepted
- Date: 2026-10-11

## Context

The AI Engineering course explains its labs with formulas: sums, fractions, derivatives, norms, Greek letters. Every number a learner sees must come from code (CLAUDE.md), and a formula must look right, symbols included. Geist, the site's text font, has no Greek. The founder asked for a font from Free Faces if one there supports formulas, with no other preference.

## Decision

- **Writing formulas:** they are written in TeX in a stage's Markdoc prose, as a fenced `math` block or as inline code in dollars (`courses/README.md`).
- **Rendering:** Temml renders each one to MathML when the site is built, so a page needs no script to show it.
- **Font:** formulas are set in Noto Sans Math. Its v3.000 release, converted to WOFF2 without loss, lives in `packages/ui/src/fonts/noto-sans-math` with its licence.
- **Numbers:** a number in a stage's prose comes from that stage's `figures.py`, through `\fig{name}` in a formula and `{% $fig.name %}` in text.
- **Checks:** `pnpm check:content` and every build fail on any of these:
  - a formula that doesn't render;
  - a figure that is missing or never shown;
  - figures that differ between Pyodide and CPython;
  - a character the math font has no glyph for.

## Options

How formulas are drawn:

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Temml, TeX to MathML at build time (chosen) | No script or stylesheet on the page; screen readers read MathML; the browser lays it out from the font's MATH table | A displayed formula never breaks across lines, so long ones are written to fit a phone |
| KaTeX, at build time | Draws the same in every browser | Its HTML needs its stylesheet and a folder of its own fonts beside it, and carries MathML as well for screen readers |
| Formulas typed as Unicode text | Nothing to load | No fractions, roots or stretching brackets, and Geist has no Greek |

The font:

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Noto Sans Math (chosen) | Sans serif like Geist, at a weight that sits beside its text; full MATH table; Google keeps it up | 344 KB, loaded only on a page with a formula |
| Any typeface on Free Faces | Free Faces is the design reference | None of the 87 has a MATH table or the math italic letters MathML draws variables in |
| Fira Math, the math font of the Fira family (Fira Mono is on Free Faces) | Sans serif, full MATH table | One weight, much heavier than Geist's text; last released in 2020 as a pre-release |
| STIX Two Math | The most complete math font; textbook look | Serif, which sits less well beside Geist |

## Evidence

- Temml renders TeX into MathML `<math>` elements, works in Chrome, Edge, Firefox and Safari, and renders in Node with `renderToString`. Display math "gets no soft line breaks", and soft breaks in inline math don't work in WebKit ([Temml's documentation](https://temml.org/docs/en/administration)).
- MathML has been "available across browsers since January 2023" ([MDN](https://developer.mozilla.org/en-US/docs/Web/MathML)).
- KaTeX's default output is HTML for drawing with MathML for accessibility ([options](https://katex.org/docs/options)). Its `fonts/` folder "must stay alongside the CSS file" ([browser setup](https://katex.org/docs/browser)).
- A one-letter `<mi>` is drawn as its math italic character ([MathML Core, appendix C.1](https://w3c.github.io/mathml-core/#italic-mappings)), so the glyph check holds those characters, not the letters typed.
- **The fonts on [Free Faces](https://www.freefaces.gallery/), on 11 October 2026:**
  - Of the 87 typefaces listed, I measured the Google Fonts files of the text faces with fontTools.
  - Inter, JetBrains Mono, Fira Mono, Manrope and Open Sans have all 25 lowercase Greek letters and 13 or 14 of 16 math operators, but no MATH table and no math italic letters.
  - Instrument Serif and Instrument Sans have no Greek at all.
- **Noto Sans Math** is [v3.000 from notofonts/math](https://github.com/notofonts/math/releases/tag/NotoSansMath-v3.000), under the SIL Open Font License 1.1.
  - Release zip sha256: `ac351837b41f8a897f020b97fb0f075ad574c1e9669fb5839ada1f92fd748356`.
  - Its `googlefonts/ttf/NotoSansMath-Regular.ttf` sha256: `fe380412e05c2cca4b712644c58ed38ed7b1e3153bc483a8b38725fa487b8830`.
  - Converted with fontTools 4.60.1 and Brotli 1.2.0 to a 344,348-byte WOFF2 that keeps the MATH table and all 3,033 characters.
- [Fontsource's `@fontsource/noto-sans-math` 5.3.0](https://www.npmjs.com/package/@fontsource/noto-sans-math) ships only a Latin subset, without the math glyphs.
- [Fira Math's latest release](https://github.com/firamath/firamath/releases) is v0.3.4, from 15 October 2020, marked pre-release, with one weight.
- I rendered the same course formulas in Fira Math, Noto Sans Math and STIX Two Math in Chromium, Firefox and WebKit to compare them.

## Why

MathML drawn from a real math font is the web's own way to show formulas: no script, nothing for a screen reader to skip, and the font's own rules for every fraction, root and bracket. Noto Sans Math is the one font that has that and looks like the rest of the site. No typeface on Free Faces can set a formula; the nearest family, Fira, has a math font, but its weight doesn't match Geist.

The strongest case against: browsers lay out MathML a little differently from each other, so the same formula is not pixel-identical in Firefox and Chromium.

## Consequences

- Long formulas are split across aligned lines by hand, so they fit a phone, because MathML has no automatic line breaks.
- A page with a formula downloads 344 KB of font once. Pages without one never fetch it.
- The site builds each stage's figures in Pyodide, which adds a few seconds when any stage has a `figures.py`.

## Revisit when

MathML gains line breaking in all three engines, or a font family that suits the site gets a math font with a MATH table.
