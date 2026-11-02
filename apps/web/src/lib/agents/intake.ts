/*
  Sulba Intake (decision record 63) reads a request and asks its writer what it needs to know
  before specs are drafted from it. It writes its questions to one file in its session's outputs,
  which the Worker checks and asks through ask_question as the person's agent (decision record
  64). The agent has no network and no shell: it reads the brief, writes the file and stops.
*/
import type Anthropic from '@anthropic-ai/sdk';
import { z } from 'zod';

/** What Intake hands in: at most 10 questions, each a sentence. */
export const handedIn = z.object({
  questions: z.array(z.string().trim().min(1).max(1000)).max(10),
});

export const outputFile = 'questions.json';

/** The agent, as Claude Managed Agents keeps it. */
export const definition: Anthropic.Beta.Agents.AgentCreateParams = {
  name: 'Sulba Intake',
  description:
    'Reads a request for software and asks its writer what it needs to know before specs are drafted.',
  model: { id: 'claude-opus-5-5', effort: 'low' },
  system: [
    'You are Sulba Intake. Someone at a company wrote a request for software in their own words. Before Sulba drafts specs from it, each with acceptance criteria a test can check, you find out what the request leaves open that would change what gets built, and ask its writer.',
    'Ask only what the writer can answer and what changes the specs: who uses it and for what, the data and documents it works with, the rules and numbers it must follow, what it connects to, and what is out of scope. Leave technology, frameworks and architecture to Sulba. Don’t ask what the request or the answers already say.',
    'Each question is one plain sentence ending in a question mark, answerable in a line or two. Ask at most 10, the one whose answer changes the most first, and none if the request is clear enough to specify.',
    `Write your questions to /mnt/session/outputs/${outputFile} as {"questions": ["...", "..."]}, and write nothing else there.`,
  ].join('\n\n'),
  tools: [
    {
      type: 'agent_toolset_20260401',
      default_config: { enabled: false, permission_policy: { type: 'always_allow' } },
      configs: [
        { name: 'read', enabled: true },
        { name: 'write', enabled: true },
      ],
    },
  ],
};

/** What the grader checks Intake's file against before it counts. */
export const rubric = [
  `- /mnt/session/outputs/${outputFile} exists and is JSON of the form {"questions": [strings]}.`,
  '- It holds at most 10 questions, and none repeats another or a question already answered in the brief.',
  '- Each question is one sentence ending in a question mark, under 300 characters.',
  '- Each asks about something the request leaves open that would change what is built: its users, data, rules, numbers, connections or scope.',
  '- No question asks the writer to choose a technology, framework or architecture.',
  '- No question asks what the request or its answers already say.',
  '- The question whose answer changes the most comes first.',
].join('\n');

export interface Brief {
  readonly number: number;
  readonly title: string;
  readonly body: string;
  readonly questions: readonly { text: string; answer: string | null }[];
}

/** The task Intake is given: the request, and the questions already asked about it. */
export function task(request: Brief): string {
  const answered = request.questions.filter((question) => question.answer !== null);
  const asked = request.questions.filter((question) => question.answer === null);
  return [
    'Read this request for software and write the questions its writer should answer before specs are drafted from it.',
    `REQ-${request.number}: ${request.title}`,
    request.body.trim() || 'The request says nothing beyond its title.',
    ...(answered.length
      ? [
          `Questions already answered:\n${answered.map((question) => `- ${question.text}\n  ${question.answer}`).join('\n')}`,
        ]
      : []),
    ...(asked.length
      ? [
          `Questions already asked and waiting for an answer, which you don’t ask again:\n${asked.map((question) => `- ${question.text}`).join('\n')}`,
        ]
      : []),
  ].join('\n\n');
}
