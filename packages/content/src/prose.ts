// Turns a stage's Markdoc prose into HTML. Formulas are TeX: a fenced block marked `math` is shown
// on its own lines, and inline code wrapped in dollars, such as `$\sigma(z)$`, sits in the text.
// Temml renders each one to MathML when the site is built, so a page needs no script to show it
// and screen readers read it. Numbers come from the stage's figures.py: `\fig{name}` inside a
// formula, and `{% $fig.name %}` in the text. A line of text, such as a check's title, renders
// without a paragraph around it. Each table and each formula on its own lines sits in a box marked
// `data-scroll`, which the page lets scroll sideways when it is wider than the text.
import Markdoc, { type Config, type Node, type RenderableTreeNodes } from '@markdoc/markdoc';
import temml from 'temml';

export interface RenderedProse {
  readonly html: string;
  /** Each formula, as MathML. */
  readonly formulas: readonly string[];
  /** The figures the prose shows. */
  readonly used: ReadonlySet<string>;
  readonly errors: readonly string[];
}

const inline = /^\$(.+)\$$/s;
const figure = /\\fig\{([A-Za-z_]\w*)\}/g;
const placeholder = /<sulba-formula index="(\d+)"><\/sulba-formula>/g;
const { Tag } = Markdoc;
type Tag = InstanceType<typeof Tag>;

function scrolling(wide: Tag): Tag {
  return new Tag('div', { 'data-scroll': '' }, [wide]);
}

function variablesIn(ast: Node): string[] {
  const names: string[] = [];
  for (const node of ast.walk()) {
    const content = node.attributes.content as unknown;
    if (Markdoc.Ast.isVariable(content) && content.path[0] === 'fig') {
      names.push(String(content.path[1]));
    }
  }
  return names;
}

export function renderProse(
  text: string,
  figures: Readonly<Record<string, string>>,
  { oneLine = false }: { readonly oneLine?: boolean } = {},
): RenderedProse {
  const errors: string[] = [];
  const used = new Set<string>();
  const formulas: string[] = [];

  const formula = (tex: string, displayMode: boolean): Tag => {
    const filled = tex.replace(figure, (_, name: string) => {
      used.add(name);
      const value = figures[name];
      if (value === undefined) errors.push(`\\fig{${name}}: figures.py gives no ${name}.`);
      return value ?? '?';
    });
    try {
      formulas.push(
        temml.renderToString(filled, { displayMode, throwOnError: true, strict: true }),
      );
    } catch (error) {
      errors.push(`The formula ${tex.trim()} doesn't render: ${(error as Error).message}`);
      formulas.push('');
    }
    const placed = new Tag('sulba-formula', { index: formulas.length - 1 });
    return displayMode ? scrolling(placed) : placed;
  };

  const config: Config = {
    variables: { fig: figures },
    nodes: {
      table: {
        transform(node, config) {
          return scrolling(new Tag('table', {}, node.transformChildren(config)));
        },
      },
      fence: {
        attributes: { content: { type: String }, language: { type: String } },
        transform(node) {
          const { content, language } = node.attributes as { content: string; language?: string };
          if (language === 'math') return formula(content, true);
          const code = new Tag('code', language ? { 'data-language': language } : {}, [content]);
          return new Tag('pre', {}, [code]);
        },
      },
      code: {
        attributes: { content: { type: String } },
        transform(node) {
          const { content } = node.attributes as { content: string };
          const math = inline.exec(content);
          return math ? formula(math[1] ?? '', false) : new Tag('code', {}, [content]);
        },
      },
    },
  };

  const ast = Markdoc.parse(text);
  // Markdoc reports a variable figures.py doesn't give.
  for (const { error } of Markdoc.validate(ast, config)) errors.push(error.message);
  for (const name of variablesIn(ast)) used.add(name);
  let tree: RenderableTreeNodes = Markdoc.transform(ast, config);
  if (oneLine) {
    const [line, ...more] = ast.children;
    if (line?.type !== 'paragraph' || more.length) errors.push('This text is one line, alone.');
    else tree = ((tree as Tag).children[0] as Tag).children;
  }
  const html = Markdoc.renderers
    .html(tree)
    .replace(placeholder, (_, index: string) => formulas[Number(index)] ?? '');
  return { html, formulas: formulas.filter(Boolean), used, errors };
}
