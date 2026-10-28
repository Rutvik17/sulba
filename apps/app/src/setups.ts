// How each coding agent connects to Sulba's MCP server, as each one's documentation gives it
// (decision record 51). Each signs in through the person's browser the first time it connects.

export interface Step {
  /** What to do. */
  readonly text: string;
  /** What to run or paste, when there is something. */
  readonly code?: string;
}

export interface Setup {
  readonly id: string;
  readonly name: string;
  readonly steps: readonly Step[];
}

/** The address of the MCP server served at `origin`. */
export function serverAddress(origin: string): string {
  return `${origin}/mcp`;
}

/** The steps for each agent, for the server at `origin`. */
export function setups(origin: string): readonly Setup[] {
  const address = serverAddress(origin);
  return [
    {
      id: 'claude-code',
      name: 'Claude Code',
      steps: [
        { text: 'Add Sulba:', code: `claude mcp add --transport http sulba ${address}` },
        { text: 'Then run /mcp in Claude Code, choose sulba and sign in.' },
      ],
    },
    {
      id: 'codex',
      name: 'Codex',
      steps: [
        { text: 'Add Sulba:', code: `codex mcp add sulba --url ${address}` },
        { text: 'Then sign in:', code: 'codex mcp login sulba' },
      ],
    },
    {
      id: 'cursor',
      name: 'Cursor',
      steps: [
        {
          text: 'Add Sulba to ~/.cursor/mcp.json, or to .cursor/mcp.json in one project:',
          code: JSON.stringify({ mcpServers: { sulba: { url: address } } }, null, 2),
        },
        { text: 'Cursor asks you to sign in when it connects.' },
      ],
    },
    {
      id: 'vscode',
      name: 'GitHub Copilot in VS Code',
      steps: [
        {
          text: 'Run MCP: Add Server from the Command Palette, choose HTTP and enter:',
          code: address,
        },
        { text: 'VS Code then asks you to trust the server and sign in.' },
      ],
    },
  ];
}
