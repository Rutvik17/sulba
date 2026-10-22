/** A language the editor reads. */
export type Language = 'python' | 'typescript' | 'dockerfile';

/** The language of a stage's file, from its name. */
export function languageOf(file: string): Language {
  if (file === 'Dockerfile') return 'dockerfile';
  return file.endsWith('.ts') ? 'typescript' : 'python';
}
