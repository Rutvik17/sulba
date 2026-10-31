// The command menu, and the keys that run the same commands (decision record 53). The workspace
// gives the commands every page has; a page adds the ones that act on what it shows, which the
// menu lists first.
import { localStore } from '@sulba/data/session';
import { specKey, specsOf } from '@sulba/data/specs';
import { holds } from '@sulba/data/workspaces';
import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { type CommandGroup, CommandMenu } from '@sulba/ui/command';
import { Dialog } from '@sulba/ui/dialog';
import { Keys } from '@sulba/ui/keys';
import { Switch } from '@sulba/ui/switch';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from '@tanstack/react-router';
import { createContext, type ReactNode, use, useEffect, useId, useRef, useState } from 'react';
import { useAccount, useSignOut } from './account';
import styles from './commands.module.css';
import { NewRequest } from './NewRequest';
import { NewSpec } from './NewSpec';
import { keys, useWorkspaces } from './queries';
import { useWorkspace } from './Shell';
import {
  focusTaken,
  onMac,
  press,
  type Shortcut,
  sequenceTimeout,
  stepOf,
  stepsOf,
  typesText,
} from './shortcuts';

const css = classes(styles, 'groups', 'group', 'heading', 'list', 'row');

/** A command that does something at once. */
export interface Action {
  readonly id: string;
  readonly label: string;
  /** A word after the label, such as "Current". */
  readonly note?: string;
  readonly run: () => void;
}

export interface Command {
  readonly id: string;
  readonly label: string;
  /** The heading it's under, such as "Go to", or the ID of the spec it acts on. */
  readonly group: string;
  readonly keys?: Shortcut;
  /** What it does: an action, or a list of them it opens, as Change status opens the statuses. */
  readonly does: (() => void) | { readonly title: string; readonly actions: readonly Action[] };
}

interface Registry {
  /** Each page's commands, under the page's own key. */
  readonly pages: Map<symbol, readonly Command[]>;
  readonly createSpec: () => void;
  readonly createRequest: () => void;
  readonly openMenu: () => void;
}

const RegistryContext = createContext<Registry | null>(null);

function useRegistry(): Registry {
  const registry = use(RegistryContext);
  if (!registry) throw new Error('Commands are for pages inside a workspace');
  return registry;
}

/** Adds a page's commands to the menu and their keys while the page is open. */
export function useCommands(commands: readonly Command[]): void {
  const { pages } = useRegistry();
  const [page] = useState(() => Symbol());
  // Every render, so a command runs with what the page shows now.
  useEffect(() => {
    pages.set(page, commands);
  });
  useEffect(() => () => void pages.delete(page), [pages, page]);
}

/** Opens the dialog that writes a new spec, from the page's button or from C. */
export function useCreateSpec(): () => void {
  return useRegistry().createSpec;
}

/** Opens the dialog that writes a new request. */
export function useCreateRequest(): () => void {
  return useRegistry().createRequest;
}

/** Opens the command menu, from the sidebar's button. */
export function useOpenMenu(): () => void {
  return useRegistry().openMenu;
}

/** How a shortcut's keys are shown on this device. */
export function shortcutSteps(shortcut: Shortcut) {
  return stepsOf(shortcut, mac);
}

const mac = onMac(navigator.userAgent);
const menuKeys: Shortcut = ['mod+k'];
/** The menu's keys as aria-keyshortcuts names them. */
export const menuShortcut = mac ? 'Meta+K' : 'Control+K';
const modifiers = new Set(['Shift', 'Control', 'Alt', 'Meta', 'CapsLock']);

const inDialog = (target: EventTarget | null) =>
  target instanceof Element && target.closest('[role="dialog"], [role="alertdialog"]') !== null;

// The browser keeps the choice to turn off shortcuts of a single key, which WCAG 2.1.4 asks for.
const singleKeysKey = 'sulba:keys';

function singleKeysOn(): boolean {
  try {
    return localStore().getItem(singleKeysKey) !== 'off';
  } catch {
    return true;
  }
}

function keepSingleKeys(on: boolean): void {
  try {
    if (on) localStore().removeItem(singleKeysKey);
    else localStore().setItem(singleKeysKey, 'off');
  } catch {}
}

/** The groups the workspace gives, listed after a page's own. */
const workspaceGroups = ['Create', 'Go to', 'Workspace', 'Help'];

/** A page's commands first, in the order of their labels, then the workspace's, as it gives them. */
function ordered(commands: readonly Command[]): Command[] {
  const rank = (command: Command) => workspaceGroups.indexOf(command.group);
  return [...commands].sort(
    (a, b) => rank(a) - rank(b) || (rank(a) === -1 ? a.label.localeCompare(b.label, 'en') : 0),
  );
}

function grouped(entries: readonly { group: string; command: CommandGroup['commands'][number] }[]) {
  const groups = new Map<string, CommandGroup['commands'][number][]>();
  for (const { group, command } of entries)
    groups.set(group, [...(groups.get(group) ?? []), command]);
  return [...groups].map(([title, commands]) => ({ id: title, title, commands }));
}

/**
 * The command menu, the shortcuts dialog and the dialog for a new spec, with the keys that open
 * them and run every command that has a shortcut. Keys without Cmd or Ctrl work only where they
 * can't be typing, and can be turned off.
 */
export function Commands({ children }: { children: ReactNode }) {
  const workspace = useWorkspace();
  const { data: workspaces } = useWorkspaces();
  const navigate = useNavigate();
  const signOut = useSignOut();
  const [pages] = useState(() => new Map<symbol, readonly Command[]>());
  const [menu, setMenu] = useState<{ list: string | null; query: string } | null>(null);
  const [showingKeys, setShowingKeys] = useState(false);
  const [creating, setCreating] = useState(false);
  const [requesting, setRequesting] = useState(false);
  const [singleKeys, setSingleKeys] = useState(singleKeysOn);
  const [registry] = useState<Registry>(() => ({
    pages,
    createSpec: () => setCreating(true),
    createRequest: () => setRequesting(true),
    openMenu: () => setMenu({ list: null, query: '' }),
  }));
  const slug = workspace.slug;
  const canWrite = holds(workspace.role, 'member');

  const go =
    (
      to:
        | '/$slug'
        | '/$slug/requests'
        | '/$slug/tasks'
        | '/$slug/specs'
        | '/$slug/evidence'
        | '/$slug/members'
        | '/$slug/settings',
    ) =>
    () =>
      void navigate({ to, params: { slug } });
  const own: Command[] = [
    ...(canWrite
      ? [
          {
            id: 'new-spec',
            label: 'Create a spec',
            group: 'Create',
            keys: ['c'],
            does: () => setCreating(true),
          },
          {
            id: 'new-request',
            label: 'Create a request',
            group: 'Create',
            does: () => setRequesting(true),
          },
        ]
      : []),
    {
      id: 'new-workspace',
      label: 'Create a workspace',
      group: 'Create',
      does: () => void navigate({ to: '/new' }),
    },
    { id: 'go-work', label: 'Go to My work', group: 'Go to', keys: ['g', 'w'], does: go('/$slug') },
    {
      id: 'go-requests',
      label: 'Go to Requests',
      group: 'Go to',
      keys: ['g', 'r'],
      does: go('/$slug/requests'),
    },
    {
      id: 'go-specs',
      label: 'Go to Specs',
      group: 'Go to',
      keys: ['g', 's'],
      does: go('/$slug/specs'),
    },
    {
      id: 'go-tasks',
      label: 'Go to Tasks',
      group: 'Go to',
      keys: ['g', 't'],
      does: go('/$slug/tasks'),
    },
    {
      id: 'go-evidence',
      label: 'Go to Evidence',
      group: 'Go to',
      keys: ['g', 'e'],
      does: go('/$slug/evidence'),
    },
    {
      id: 'go-members',
      label: 'Go to Members',
      group: 'Go to',
      keys: ['g', 'm'],
      does: go('/$slug/members'),
    },
    {
      id: 'go-settings',
      label: 'Go to Settings',
      group: 'Go to',
      keys: ['g', ','],
      does: go('/$slug/settings'),
    },
    {
      id: 'switch',
      label: 'Switch workspace',
      group: 'Workspace',
      keys: ['o', 'w'],
      does: {
        title: 'Switch workspace',
        actions: workspaces.map((each) => ({
          id: each.slug,
          label: each.name,
          ...(each.slug === slug ? { note: 'Current' } : {}),
          run: () => void navigate({ to: '/$slug', params: { slug: each.slug } }),
        })),
      },
    },
    {
      id: 'sign-out',
      label: 'Sign out',
      group: 'Workspace',
      does: async () => {
        await signOut();
        await navigate({ to: '/' });
      },
    },
    {
      id: 'shortcuts',
      label: 'Keyboard shortcuts',
      group: 'Help',
      keys: ['?'],
      does: () => setShowingKeys(true),
    },
  ];
  const all = () => ordered([...[...pages.values()].flat(), ...own]);

  // The key handler reads the commands as they are when a key is pressed.
  const latest = useRef({ all, singleKeys, menuOpen: menu !== null });
  latest.current = { all, singleKeys, menuOpen: menu !== null };

  useEffect(() => {
    let pending: readonly string[] = [];
    let last = 0;
    const onKeyDown = (event: globalThis.KeyboardEvent) => {
      if (event.defaultPrevented || event.isComposing || event.repeat) return;
      const step = stepOf(event, mac);
      if (step === null) {
        // Shift, held for ?, leaves a sequence waiting; any other key ends it.
        if (!modifiers.has(event.key)) pending = [];
        return;
      }
      if (step === 'mod+k') {
        // Another dialog keeps the keyboard until it closes.
        if (!latest.current.menuOpen && inDialog(event.target)) return;
        event.preventDefault();
        pending = [];
        setMenu((open) => (open ? null : { list: null, query: '' }));
        return;
      }
      if (typesText(step) && (!latest.current.singleKeys || focusTaken(event.target))) return;
      if (event.timeStamp - last > sequenceTimeout) pending = [];
      last = event.timeStamp;
      const commands = latest.current.all().filter((command) => command.keys);
      const pressed = press(
        pending,
        step,
        commands.map((command) => command.keys ?? []),
      );
      pending = pressed.pending;
      const command = pressed.done && commands.find((each) => each.keys === pressed.done);
      if (!command) return;
      event.preventDefault();
      if (typeof command.does === 'function') command.does();
      else setMenu({ list: command.id, query: '' });
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  return (
    <RegistryContext value={registry}>
      {children}
      {menu ? (
        <Menu
          commands={all()}
          list={menu.list}
          query={menu.query}
          onChange={setMenu}
          onClose={() => setMenu(null)}
        />
      ) : null}
      <Shortcuts
        isOpen={showingKeys}
        onClose={() => setShowingKeys(false)}
        commands={all()}
        singleKeys={singleKeys}
        onSingleKeys={(on) => {
          setSingleKeys(on);
          keepSingleKeys(on);
        }}
      />
      <NewSpec isOpen={creating} onClose={() => setCreating(false)} />
      <NewRequest isOpen={requesting} onClose={() => setRequesting(false)} />
    </RegistryContext>
  );
}

const specLink = 'spec/';

/**
 * The menu, open: every command under its heading, or the actions of the list a command opened.
 * A search also finds the actions in each list, and the workspace's specs by ID or title.
 */
function Menu({
  commands,
  list,
  query,
  onChange,
  onClose,
}: {
  commands: readonly Command[];
  list: string | null;
  query: string;
  onChange: (menu: { list: string | null; query: string }) => void;
  onClose: () => void;
}) {
  const workspace = useWorkspace();
  const { client } = useAccount();
  const navigate = useNavigate();
  // The specs come with the menu; until they arrive, it lists the commands alone.
  const { data: specs } = useQuery({
    queryKey: keys.specs(workspace.id),
    queryFn: () => specsOf(client, workspace.id),
  });
  const opened = commands.find((command) => command.id === list);
  const listed = opened && typeof opened.does !== 'function' ? opened.does : null;

  const groups = listed
    ? [{ id: 'list', title: listed.title, commands: listed.actions }]
    : grouped([
        ...commands.map((command) => ({
          group: command.group,
          command: {
            id: command.id,
            label: typeof command.does === 'function' ? command.label : `${command.label}…`,
            ...(command.keys ? { keys: stepsOf(command.keys, mac) } : {}),
          },
        })),
        ...(query
          ? commands.flatMap(({ id, group, does }) =>
              typeof does === 'function'
                ? []
                : does.actions.map((action) => ({
                    group,
                    command: { id: `${id}/${action.id}`, label: `${does.title}: ${action.label}` },
                  })),
            )
          : []),
        ...(query
          ? (specs ?? []).map((spec) => ({
              group: 'Specs',
              command: {
                id: `${specLink}${spec.number}`,
                label: `${specKey(spec.number)} ${spec.title}`,
              },
            }))
          : []),
      ]);

  const act = (id: string) => {
    if (id.startsWith(specLink)) {
      onClose();
      void navigate({
        to: '/$slug/$spec',
        params: { slug: workspace.slug, spec: specKey(Number(id.slice(specLink.length))) },
      });
      return;
    }
    const [commandId, actionId] = listed && opened ? [opened.id, id] : id.split('/');
    const command = commands.find((each) => each.id === commandId);
    if (!command) return;
    if (typeof command.does === 'function') {
      onClose();
      command.does();
    } else if (actionId === undefined) {
      onChange({ list: command.id, query: '' });
    } else {
      onClose();
      command.does.actions.find((action) => action.id === actionId)?.run();
    }
  };

  // Backspace in an empty search goes back from a list to every command.
  const onKeyDown = (event: { key: string }) => {
    if (event.key === 'Backspace' && listed && query === '') onChange({ list: null, query: '' });
  };

  return (
    <CommandMenu
      isOpen
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
      label={listed ? listed.title : 'Commands'}
      placeholder={listed ? `${listed.title}…` : 'Type a command or search'}
      groups={groups}
      query={query}
      onQueryChange={(next) => onChange({ list, query: next })}
      onAction={act}
      onKeyDown={onKeyDown}
    />
  );
}

/** Every command with a shortcut, under its heading, and the switch for keys of a single press. */
function Shortcuts({
  isOpen,
  onClose,
  commands,
  singleKeys,
  onSingleKeys,
}: {
  isOpen: boolean;
  onClose: () => void;
  commands: readonly Command[];
  singleKeys: boolean;
  onSingleKeys: (on: boolean) => void;
}) {
  const base = useId();
  const menuCommand: Command = {
    id: 'menu',
    label: 'Open the command menu',
    group: 'Help',
    keys: menuKeys,
    does: () => {},
  };
  const keyed = commands.filter((command) => command.keys);
  const firstHelp = keyed.findIndex((command) => command.group === 'Help');
  keyed.splice(firstHelp === -1 ? keyed.length : firstHelp, 0, menuCommand);
  const groups = [...new Set(keyed.map((command) => command.group))];
  const menuSteps = stepsOf(menuKeys, mac)
    .map((step) => step.join(' '))
    .join('');

  return (
    <Dialog
      title="Keyboard shortcuts"
      isOpen={isOpen}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
      actions={
        <Button slot="close" variant="outline">
          Close
        </Button>
      }
    >
      <Switch
        isSelected={singleKeys}
        onChange={onSingleKeys}
        description={`Keys such as C and G then S. ${menuSteps} opens the command menu either way.`}
      >
        Single-key shortcuts
      </Switch>
      <div className={css.groups}>
        {groups.map((group, index) => (
          <section key={group} className={css.group} aria-labelledby={`${base}-${index}`}>
            <h3 id={`${base}-${index}`} className={css.heading}>
              {group}
            </h3>
            <ul className={css.list}>
              {keyed
                .filter((command) => command.group === group)
                .map((command) => (
                  <li key={command.id} className={css.row}>
                    <span>{command.label}</span>
                    <Keys steps={stepsOf(command.keys ?? [], mac)} />
                  </li>
                ))}
            </ul>
          </section>
        ))}
      </div>
    </Dialog>
  );
}
