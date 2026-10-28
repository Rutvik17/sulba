import { expect, test } from 'vitest';
import { serverAddress, setups } from './setups';

test('each agent is pointed at the server where the app is served', () => {
  expect(serverAddress('https://sulba.dev')).toBe('https://sulba.dev/mcp');
  const steps = setups('https://sulba.dev').flatMap((setup) => setup.steps);
  expect(steps.filter((step) => step.code?.includes('https://sulba.dev/mcp'))).toHaveLength(4);
});

test('Cursor’s configuration is the JSON its file takes', () => {
  const cursor = setups('http://127.0.0.1:4321').find((setup) => setup.id === 'cursor');
  expect(JSON.parse(cursor?.steps[0]?.code ?? '')).toEqual({
    mcpServers: { sulba: { url: 'http://127.0.0.1:4321/mcp' } },
  });
});
