# 53. Run every action from a command menu and from keys, built on React Aria

- Status: accepted
- Date: 2026-10-28

## Context

The product spec asks for every action three ways: a button, a key and Cmd K, with the menu showing each key so one way teaches the next, the way Linear's documentation lays out each feature as Keyboard, Mouse and Command menu. Keys are letters such as C, or sequences such as G then S, and never fire while someone is typing. Shortcuts of a single character help people who use the keyboard and get in the way of people who speak to their computer, so they need a way to be turned off. The app's components take their behaviour from React Aria Components (decision record 11).

## Decision

- **The menu:** Cmd K on a Mac and Ctrl K elsewhere opens it from any page of a workspace, and so does the sidebar's Search or run a command. It's React Aria's `Autocomplete` over a `Menu` in a `Modal`, in `packages/ui/src/command`: typing filters the commands, ignoring case and accents, the arrow keys move through them while the focus stays in the field, and Enter runs one. Each command shows its keys, which a screen reader reads as the command's description.
- **What's in it:** the workspace's commands (create a spec or a workspace; go to My work, Specs, Evidence, Members or Settings; switch workspace; sign out; the shortcuts) and, first, the page's own, such as a spec's status, owner and reviewers and the reviewer's answer. A command that needs a choice, such as Change status, opens a list of its choices, and Backspace in its empty search goes back. A search also finds each list's choices and the workspace's specs by ID or title.
- **The keys:** a command's shortcut is a key, a sequence of keys each pressed within a second of the last, or Cmd or Ctrl with a key. Workspace: C creates a spec, G then W, S, E, M or , goes to My work, Specs, Evidence, Members or Settings, O then W switches workspace and ? lists the shortcuts. A spec: S changes its status, A its owner and R adds a reviewer. A key without Cmd or Ctrl works only where it can't be text or part of an open control: not in a field, the editor, a dialog, a menu or a list. `apps/app/src/shortcuts.ts` holds the matching, with its unit tests.
- **Teaching:** the menu shows each command's keys, a button with a shortcut shows it in a tooltip, the sidebar shows each page's keys while the pointer is over it or the keyboard is on it, and ? lists them all.
- **Turning keys off:** the shortcuts list has a switch for keys without Cmd or Ctrl, which this browser keeps as `sulba:keys`. Cmd K or Ctrl K works either way.
- **Where commands come from:** a page adds its commands with `useCommands` while it's open, beside the code that does them, so the menu, the key and the button run the same code.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| React Aria's Autocomplete and Menu, keys matched in the app (chosen) | The library the app's components already use; virtual focus and the keys' description come with it; React Aria's own examples build a command palette this way | The sequence matching is code of our own, a short module with its unit tests |
| cmdk | Made for command menus, filters and sorts as it goes | A second accessibility library, on Radix's Dialog, beside React Aria's |
| tinykeys for the keys | Sequences, `$mod` for Cmd or Ctrl, a 1,000 ms window, and it skips fields | A dependency for a small part, which still leaves out editors and open controls that aren't fields |
| Keys with no way to turn them off | Nothing to build | Fails WCAG 2.1.4 for anyone who speaks to their computer |

## Evidence

- [React Aria, Autocomplete](https://react-spectrum.adobe.com/react-aria/Autocomplete.html): filters a Menu or ListBox from a TextField or SearchField, with virtual focus so the arrow keys move through the list while the field keeps the focus; its example Command Palette is a Modal and Dialog around an Autocomplete and a Menu, opened with a key held with Cmd on a Mac and Ctrl elsewhere.
- [Linear Docs, Joining your team on Linear](https://linear.app/docs/joining-your-team-on-linear): "?" brings up the help window and "c" creates an issue; Cmd K "pulls up the full set of available commands. If you want to do something, but aren't sure how, try searching the command menu."
- [Linear Docs, My Issues](https://linear.app/docs/my-issues): actions laid out as Keyboard, Mouse and Command menu, with "G then M to go to My Issues".
- [GitHub Docs, Keyboard shortcuts](https://docs.github.com/en/get-started/accessibility/keyboard-shortcuts): "?" lists the page's shortcuts, sequences such as G then I go to a tab, and character key shortcuts can be turned off while those with modifier keys stay on.
- [Atlassian Support, Use keyboard shortcuts in Jira](https://support.atlassian.com/jira-software-cloud/docs/use-keyboard-shortcuts/): keyboard shortcuts can be switched off from the shortcuts dialog.
- [W3C, Understanding Success Criterion 2.1.4: Character Key Shortcuts](https://www.w3.org/WAI/WCAG22/Understanding/character-key-shortcuts.html): a shortcut of letters, punctuation, numbers or symbols alone must be possible to turn off, remap to include a key such as Ctrl or Alt, or be active only while its control has focus.
- [cmdk, README](https://github.com/pacocoursey/cmdk): a command menu component that filters and sorts its items, whose Dialog "composes Radix UI's Dialog component".
- [tinykeys, README](https://github.com/jamiebuilds/tinykeys): sequences such as "g i", `$mod` as Meta on a Mac and Control elsewhere, each press "within 1000ms of the last", and it ignores `input`, `textarea`, `select` and `[contenteditable]`.

## Why

React Aria already gives the app its menus and dialogs, and its Autocomplete is a command menu's search and list with the focus handled, so a second library would add weight and a second set of accessibility behaviours for what one can do. Matching keys is small enough to own, and owning it lets the rule for where keys can fire include the editor and every open control, not only fields. The switch for single keys is what GitHub and Jira offer and what WCAG 2.1.4 asks.

## Consequences

- A new action joins the menu, and gets a key when it's common, in the same pull request.
- The menu lists a page's commands only while that page is open.
- A second key for an action, or remapping keys, needs a settings page of its own.

## Revisit when

People ask to remap keys, or the menu needs results from a search the browser can't run over what it already holds.
