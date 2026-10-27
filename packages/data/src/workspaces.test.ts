import { describe, expect, it } from 'vitest';
import { holds, joinLink, nameProblem, slugOf, slugProblem } from './workspaces.ts';

describe('slugOf', () => {
  it('suggests an address from a name', () => {
    expect(slugOf('Acme Payments')).toBe('acme-payments');
    expect(slugOf('  Café  Zürich!  ')).toBe('cafe-zurich');
    expect(slugOf('R&D / Platform')).toBe('r-d-platform');
  });

  it('keeps to 32 characters, without a hyphen at the end', () => {
    const slug = slugOf('The quick brown fox jumps over the lazy dog');
    expect(slug).toBe('the-quick-brown-fox-jumps-over-t');
    expect(slugOf('abcdefghijklmnopqrstuvwxyz abcde f')).toBe('abcdefghijklmnopqrstuvwxyz-abcde');
  });

  it('suggests an address the checks accept', () => {
    for (const name of ['Acme', 'Data & ML', 'Ünïcödé Team']) {
      expect(slugProblem(slugOf(name))).toBeNull();
    }
  });
});

describe('slugProblem', () => {
  it('accepts lowercase letters, digits and single hyphens', () => {
    expect(slugProblem('acme')).toBeNull();
    expect(slugProblem('team-42')).toBeNull();
  });

  it('says what is wrong with an address', () => {
    expect(slugProblem('ab')).toBe('An address has at least 3 characters.');
    expect(slugProblem('a'.repeat(33))).toBe('An address has at most 32 characters.');
    expect(slugProblem('Acme')).toBe('Use lowercase letters, digits and hyphens.');
    expect(slugProblem('a_b')).toBe('Use lowercase letters, digits and hyphens.');
    expect(slugProblem('-acme')).toBe('A hyphen goes between two letters or digits.');
    expect(slugProblem('ac--me')).toBe('A hyphen goes between two letters or digits.');
    expect(slugProblem('join')).toBe('That address is taken.');
  });
});

describe('nameProblem', () => {
  it('asks for a name of 64 characters or fewer', () => {
    expect(nameProblem('Acme')).toBeNull();
    expect(nameProblem('   ')).toBe('Give the workspace a name.');
    expect(nameProblem('a'.repeat(65))).toBe('A name has at most 64 characters.');
  });
});

describe('holds', () => {
  it('lets each role do what the roles below it may', () => {
    expect(holds('owner', 'admin')).toBe(true);
    expect(holds('admin', 'admin')).toBe(true);
    expect(holds('member', 'admin')).toBe(false);
    expect(holds('viewer', 'member')).toBe(false);
  });
});

describe('joinLink', () => {
  it('points at the app’s join page', () => {
    expect(joinLink('https://sulba.dev', 'abc123')).toBe('https://sulba.dev/app/join/abc123');
  });
});
