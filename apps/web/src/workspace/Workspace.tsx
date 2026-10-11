import { Editor, type EditorHandle } from '@sulba/editor/editor';
import { Lab } from '@sulba/lab/client';
import { pyodidePath } from '@sulba/lab/protocol';
import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { Tab, TabList, TabPanel, Tabs } from '@sulba/ui/tabs';
import { useEffect, useRef, useState } from 'react';
import type { LabView, StageView } from '../lib/labs';
import { Printed, type Run, TestResults } from './Results';
import { codeOf, isOpen, runOf } from './stages';
import { kept } from './storage';
import styles from './workspace.module.css';

const css = classes(
  styles,
  'stages',
  'stage',
  'number',
  'kind',
  'state',
  'workspace',
  'left',
  'panel',
  'prose',
  'hints',
  'right',
  'head',
  'file',
  'tools',
  'code',
  'dock',
  'done',
);

const kinds: Record<StageView['kind'], string> = { build: 'Build' };

/** The stage to open: the one the address names if it's open, else the first not yet passed. */
function firstStage(lab: LabView): number {
  const named = new URLSearchParams(location.search).get('stage');
  const index = lab.stages.findIndex((stage) => stage.slug === named);
  if (index >= 0 && isOpen(lab, index, kept)) return index;
  const next = lab.stages.findIndex((stage) => !kept.passed(stage.id));
  return next >= 0 ? next : lab.stages.length - 1;
}

/** A lab's stages, and the workspace for the one open. Python stays loaded across stages. */
export default function Workspace({ lab }: { lab: LabView }) {
  const [index, setIndex] = useState(() => firstStage(lab));
  const [passed, setPassed] = useState(() => lab.stages.filter((stage) => kept.passed(stage.id)));
  const [python, setPython] = useState<Lab | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const runner = new Lab({ indexURL: pyodidePath });
    setPython(runner);
    const packages = [...new Set(lab.stages.flatMap((stage) => stage.packages))];
    runner.prepare(packages).then(
      () => setLoading(false),
      // A run tries again and says so if Python still won't load.
      () => setLoading(false),
    );
    return () => runner.dispose();
  }, [lab]);

  const open = (to: number) => {
    setIndex(to);
    const address = new URL(location.href);
    address.searchParams.set('stage', lab.stages[to]?.slug ?? '');
    history.replaceState(null, '', address);
  };

  const stage = lab.stages[index];
  if (!stage) return null;
  const isPassed = (each: StageView) => passed.some((done) => done.id === each.id);

  return (
    <>
      <nav aria-label="Stages">
        <ol className={css.stages}>
          {lab.stages.map((each, at) => (
            <li key={each.id}>
              <button
                type="button"
                className={css.stage}
                aria-current={at === index ? 'step' : undefined}
                disabled={!isOpen(lab, at, kept)}
                onClick={() => open(at)}
              >
                <span className={css.number}>{at + 1}</span>
                <span className={css.kind}>{kinds[each.kind]}</span>
                {each.title}
                <span className={css.state}>
                  {isPassed(each)
                    ? 'Done'
                    : isOpen(lab, at, kept)
                      ? ''
                      : `Opens when stage ${at} is done`}
                </span>
              </button>
            </li>
          ))}
        </ol>
      </nav>
      <StageWorkspace
        key={stage.id}
        lab={lab}
        index={index}
        python={python}
        loading={loading}
        passed={isPassed(stage)}
        onPass={() => {
          kept.pass(stage.id);
          setPassed(lab.stages.filter((each) => kept.passed(each.id)));
        }}
        onNext={index + 1 < lab.stages.length ? () => open(index + 1) : null}
      />
    </>
  );
}

interface StageProps {
  readonly lab: LabView;
  readonly index: number;
  readonly python: Lab | null;
  readonly loading: boolean;
  readonly passed: boolean;
  readonly onPass: () => void;
  readonly onNext: (() => void) | null;
}

function StageWorkspace({ lab, index, python, loading, passed, onPass, onNext }: StageProps) {
  const stage = lab.stages[index] as StageView;
  const editor = useRef<EditorHandle>(null);
  const [opening] = useState(() => codeOf(lab, index, kept));
  const [run, setRun] = useState<Run>({ state: 'idle' });
  const [tried, setTried] = useState(passed);
  const [hints, setHints] = useState(0);
  const [results, setResults] = useState<'tests' | 'printed'>('tests');

  const runTests = async () => {
    if (!python || run.state === 'running') return;
    const code = editor.current?.code() ?? opening;
    setRun({ state: 'running' });
    setResults('tests');
    setTried(true);
    try {
      const result = await python.run(runOf(lab, index, code, kept));
      setRun({ state: 'done', result });
      if (result.status === 'pass') onPass();
    } catch {
      setRun({ state: 'failed' });
    }
  };

  const reset = () => {
    const fresh = codeOf(lab, index, {
      ...kept,
      code: (id) => (id === stage.id ? null : kept.code(id)),
    });
    editor.current?.replace(fresh);
    kept.saveCode(stage.id, null);
  };

  const done = run.state === 'done' && run.result.status === 'pass';

  return (
    <section className={css.workspace} aria-label={`Stage ${index + 1}: ${stage.title}`}>
      <div className={css.left}>
        <Tabs defaultSelectedKey="brief">
          <TabList aria-label="Stage">
            <Tab id="brief">Brief</Tab>
            <Tab id="hints">Hints</Tab>
            <Tab id="explanation">Explanation</Tab>
            <Tab id="solution" isDisabled={!tried}>
              Solution
            </Tab>
          </TabList>
          <TabPanel id="brief">
            <div className={css.panel}>
              <h2>{stage.title}</h2>
              <Prose html={stage.brief} />
            </div>
          </TabPanel>
          <TabPanel id="hints">
            <div className={css.panel}>
              {hints > 0 && (
                <ol className={css.hints}>
                  {stage.hints.slice(0, hints).map((hint) => (
                    <li key={hint}>
                      <Prose html={hint} />
                    </li>
                  ))}
                </ol>
              )}
              {hints < stage.hints.length ? (
                <Button variant="outline" size="small" onPress={() => setHints(hints + 1)}>
                  {hints === 0 ? 'Show a hint' : 'Show the next hint'}
                </Button>
              ) : (
                <p>That’s every hint for this stage.</p>
              )}
            </div>
          </TabPanel>
          <TabPanel id="explanation">
            <div className={css.panel}>
              <Prose html={stage.explanation} />
            </div>
          </TabPanel>
          <TabPanel id="solution">
            <div className={css.panel}>
              <Editor defaultValue={stage.solution} label={`Solution: ${stage.file}`} readOnly />
            </div>
          </TabPanel>
        </Tabs>
      </div>

      <div className={css.right}>
        <div className={css.head}>
          <span className={css.file}>{stage.file}</span>
          <div className={css.tools}>
            <Button variant="ghost" size="small" onPress={reset}>
              Reset
            </Button>
            <Button size="small" onPress={runTests} isDisabled={!python || run.state === 'running'}>
              Run tests
            </Button>
          </div>
        </div>
        <div className={css.code}>
          <Editor
            ref={editor}
            defaultValue={opening}
            label={stage.file}
            onChange={(code) => kept.saveCode(stage.id, code)}
            onRun={runTests}
          />
        </div>
        <div className={css.dock}>
          {done && (
            <div className={css.done}>
              <p>Stage {index + 1} done.</p>
              {onNext && (
                <Button size="small" onPress={onNext}>
                  Next stage
                </Button>
              )}
            </div>
          )}
          <Tabs
            selectedKey={results}
            onSelectionChange={(key) => setResults(key as typeof results)}
          >
            <TabList aria-label="Results">
              <Tab id="tests">Tests</Tab>
              <Tab id="printed">Printed</Tab>
            </TabList>
            <TabPanel id="tests">
              <div className={css.panel}>
                <TestResults
                  run={run}
                  loading={loading}
                  file={stage.file}
                  onGoTo={(line) => editor.current?.goTo(line)}
                />
              </div>
            </TabPanel>
            <TabPanel id="printed">
              <div className={css.panel}>
                <Printed run={run} />
              </div>
            </TabPanel>
          </Tabs>
        </div>
      </div>
    </section>
  );
}

/** Prose made from a course's Markdoc files when the site was built. */
function Prose({ html }: { html: string }) {
  // biome-ignore lint/security/noDangerouslySetInnerHtml: Markdoc made this HTML at build time from course files, which can't contain HTML of their own.
  return <div className={css.prose} dangerouslySetInnerHTML={{ __html: html }} />;
}
