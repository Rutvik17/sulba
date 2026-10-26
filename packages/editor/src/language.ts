/** A language the editor reads. */
export type Language = 'python' | 'typescript' | 'go' | 'dockerfile';

/** The language of a stage's file, from its name. */
export function languageOf(file: string): Language {
  if (file === 'Dockerfile') return 'dockerfile';
  if (file.endsWith('.go')) return 'go';
  return file.endsWith('.ts') ? 'typescript' : 'python';
}
