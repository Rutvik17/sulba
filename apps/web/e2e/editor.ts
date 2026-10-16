import { type Locator, test } from '@playwright/test';

/**
 * Replaces the code in an editor, as Select All and a paste would. Playwright's fill selects the
 * code through the browser, and on the Android phone the new code sometimes went in before the
 * editor had taken that selection in. The editor's own Select All takes effect at once.
 */
export async function write(editor: Locator, text: string) {
  // The editor's shortcuts take Command on an iPhone, as on a Mac, and Control elsewhere.
  const { defaultBrowserType, isMobile } = test.info().project.use;
  await editor.press(defaultBrowserType === 'webkit' && isMobile ? 'Meta+a' : 'ControlOrMeta+a');
  await editor.page().keyboard.insertText(text);
}
