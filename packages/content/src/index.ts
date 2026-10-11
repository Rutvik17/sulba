export { duplicateIds, prove, type Runner } from './check.ts';
export { drawnCharacters, italicOf } from './glyphs.ts';
export { idPattern, prefixes } from './ids.ts';
export {
  type Course,
  courseSlugs,
  type Dataset,
  type Lab,
  type Level,
  type Loaded,
  loadCourse,
  type Module,
  type Problem,
  type Stage,
} from './load.ts';
export { type RenderedProse, renderProse } from './prose.ts';
export { computeFigures, type FiguresRunner, figuresFiles, proseProblems } from './prose-check.ts';
export { addStarter, type StageRuns, stageRuns } from './runs.ts';
